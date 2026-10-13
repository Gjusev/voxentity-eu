"""Build the 180-scenario synthetic corpus (12 cells × 15 cases).

Difficulty mix per cell: 5 direct, 4 tricky (orthographic/phonetic),
3 segmented/spelled, 3 correction. Split: 5 dev + 10 test per cell, with
disjoint values and disjoint frame halves per family.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ..contracts import SCHEMA_VERSION, Scenario
from ..provenance import sha256_text, write_text_atomic
from . import pools, templates
from .verbalize import (
    verbalize_calendar,
    verbalize_email,
    verbalize_phone,
    verbalize_postal_address,
    verbalize_reference_code,
)

LOCALES = ("de-DE", "fr-FR")
ENTITIES = ("person_name", "phone", "email", "calendar_value", "postal_address", "reference_code")

# cell layout: difficulty -> (dev_count, test_count)
CELL_PLAN = {
    "direct": (2, 3),
    "tricky": (1, 3),
    "segmented": (1, 2),
    "correction": (1, 2),
}

ENTITY_SHORT = {
    "person_name": "name",
    "phone": "phone",
    "email": "mail",
    "calendar_value": "date",
    "postal_address": "addr",
    "reference_code": "ref",
}


def _cell_pools(locale: str, entity: str) -> dict[str, list]:
    """One generation pass per pool family; extra slices never overlap primary."""

    if entity == "person_name":
        combined = pools.person_pool(locale, 26)
        return {"primary": combined[:20], "tricky": pools.person_pool(locale, 10, tricky_only=True), "extra": combined[20:26]}
    if entity == "phone":
        combined = pools.phone_pool(locale, 26)
        return {"primary": combined[:20], "tricky": pools.tricky_phone_pool(locale, 10), "extra": combined[20:26]}
    if entity == "email":
        combined = pools.email_pool(locale, 26)
        return {"primary": combined[:20], "tricky": pools.tricky_email_pool(locale, 10), "extra": combined[20:26]}
    if entity == "calendar_value":
        combined = pools.calendar_pool(locale, 26)
        return {"primary": combined[:20], "tricky": pools.tricky_calendar_pool(locale, 10), "extra": combined[20:26]}
    if entity == "postal_address":
        combined = pools.address_pool(locale, 26)
        return {"primary": combined[:20], "tricky": pools.address_pool(locale, 10, variant="-tricky"), "extra": combined[20:26]}
    if entity == "reference_code":
        combined = pools.reference_pool(locale, 26)
        return {"primary": combined[:20], "tricky": pools.tricky_reference_pool(locale, 10), "extra": combined[20:26]}
    raise ValueError(entity)


def _spoken(value: Any, entity: str, locale: str, difficulty: str) -> str:
    """Verbalize one entity value for synthesis, per difficulty style."""

    segmented = difficulty == "segmented"
    if entity == "person_name":
        from .verbalize import letters_spelled

        if segmented:
            first, last = value.split(" ", 1)
            return f"{first} {letters_spelled(last, locale)}"
        return value
    if entity == "phone":
        style = "by_digit" if segmented else "grouped"
        return verbalize_phone(value, locale, style=style)
    if entity == "email":
        return verbalize_email(value, locale, spell_local=segmented)
    if entity == "calendar_value":
        day, month, year = value
        return verbalize_calendar(day, month, year, locale, segmented=segmented)
    if entity == "postal_address":
        street, house, postal, locality = value["street"], value["house_number"], value["postal_code"], value["locality"]
        if segmented:
            from .verbalize import DIGITS_DE, DIGITS_FR, SPELL_DE, SPELL_FR, digits_spoken

            digit_table = DIGITS_DE if locale == "de-DE" else DIGITS_FR
            spell_table = SPELL_DE if locale == "de-DE" else SPELL_FR
            # house spoken digit-by-digit; letter suffix via the spelling
            # alphabet, word suffixes (bis/ter) spoken as words
            import re as _re

            m = _re.match(r"(\d+)([A-Za-z]*)", house)
            digits_part, suffix_part = m.groups()
            number_word = " ".join(digit_table[int(c)] for c in digits_part)
            if suffix_part:
                if suffix_part.lower() in ("bis", "ter"):
                    number_word += f" {suffix_part.lower()}"
                else:
                    number_word += f" {spell_table.get(suffix_part.lower(), suffix_part)}"
            if locale == "de-DE":
                return (
                    f"Die Straße ist {street}, die Hausnummer ist {number_word}, "
                    f"die Postleitzahl ist {digits_spoken(postal, locale)}, der Ort ist {locality}"
                )
            return (
                f"La rue est {street}, le numéro est {number_word}, "
                f"le code postal est {digits_spoken(postal, locale)}, la ville est {locality}"
            )
        return verbalize_postal_address(street, house, postal, locality, locale)
    if entity == "reference_code":
        return verbalize_reference_code(value, locale, spell=segmented or difficulty == "tricky")
    raise ValueError(entity)


def _written(value: Any, entity: str) -> str:
    if entity == "calendar_value":
        day, month, year = value
        base = f"{day:02d}.{month:02d}"
        return f"{base}.{year}" if year else base
    if entity == "postal_address":
        return f"{value['street']} {value['house_number']}, {value['postal_code']} {value['locality']}"
    return str(value)


def _mutate(value: Any, entity: str, locale: str) -> Any:
    """Deterministic previous-mention generator for correction cases.

    Falls back to None when the mutation would be a no-op; the caller then
    substitutes a spare pool value (always distinct from finals)."""

    if entity == "person_name":
        return None  # name corrections use a wholly different surname from extra
    if entity == "phone":
        head, tail = value[:-2], value[-2:]
        mutated = head + tail[::-1]
        return None if mutated == value else mutated
    if entity == "email":
        local, dom = value.split("@")
        return f"{local}x@{dom}"
    if entity == "calendar_value":
        day, month, year = value
        return None if day == 1 else (day - 1, month, year)
    if entity == "postal_address":
        prev = dict(value)
        prev["house_number"] = _bump_house(value["house_number"])
        return prev
    if entity == "reference_code":
        letters, _, digits = value.partition("-")
        mutated = f"{letters}-{digits[:-2]}{digits[-2:][::-1]}"
        return None if mutated == value else mutated
    raise ValueError(entity)


def _previous_value(value: Any, entity: str, locale: str, extra: list, i: int) -> Any:
    mutated = _mutate(value, entity, locale)
    if mutated is not None and mutated != value:
        return mutated
    return extra[i % len(extra)]


def _bump_house(house: str) -> str:
    import re

    m = re.match(r"(\d+)([A-Za-z]*)", house)
    num, suffix = m.groups()
    return f"{int(num) + 2}{suffix}"


def _as_gold_value(value: Any, entity: str) -> Any:
    """Convert internal pool representation into the contract value shape."""

    if entity == "calendar_value":
        day, month, year = value
        return {"day": day, "month": month, "year": year}
    return value


def _entity_dict(entity: str, value: Any, mention: str, variants: list[str]) -> dict:
    out = {
        "entity_id": "target-1",
        "type": entity,
        "canonical_value": _as_gold_value(value, entity),
        "accepted_variants": variants,
        "mention_text": mention,
        "target": True,
    }
    if entity == "reference_code":
        out["case_sensitive"] = True
    return out


def build_corpus() -> list[Scenario]:
    scenarios: list[Scenario] = []
    for locale in LOCALES:
        for entity in ENTITIES:
            cell_pools = _cell_pools(locale, entity)
            # value budget: direct 5 (0:5), tricky 4, segmented 3 (5:8), correction 3 (8:11)
            primary = cell_pools["primary"]
            tricky = cell_pools["tricky"]
            extra = cell_pools["extra"]

            cases: list[dict[str, Any]] = []
            # direct: primary[0:5]
            for i, value in enumerate(primary[0:5]):
                cases.append({"difficulty": "direct", "value": value, "split": "dev" if i < 2 else "test"})
            # tricky: tricky[0:4]
            for i, value in enumerate(tricky[0:4]):
                cases.append({"difficulty": "tricky", "value": value, "split": "dev" if i < 1 else "test"})
            # segmented: primary[5:8]
            for i, value in enumerate(primary[5:8]):
                cases.append({"difficulty": "segmented", "value": value, "split": "dev" if i < 1 else "test"})
            # correction: primary[8:11], previous derived from the final value
            for i, value in enumerate(primary[8:11]):
                cases.append({"difficulty": "correction", "value": value, "split": "dev" if i < 1 else "test", "corr_idx": i})

            assert len(cases) == 15, f"{locale}/{entity}: {len(cases)} cases"
            plan_check = {}
            for c in cases:
                plan_check[c["difficulty"]] = plan_check.get(c["difficulty"], 0) + 1
            expected = {k: dev + test for k, (dev, test) in CELL_PLAN.items()}
            assert plan_check == expected, f"{locale}/{entity}: {plan_check} != {expected}"

            for idx, case in enumerate(cases):
                split = case["split"]
                difficulty = case["difficulty"]
                value = case["value"]
                fam = templates.template_family(locale, entity, difficulty, split)
                tag = _difficulty_tag(entity, difficulty)
                sid = f"{split}-{locale.split('-')[0]}-{ENTITY_SHORT[entity]}-{idx:03d}"

                spoken = _spoken(value, entity, locale, difficulty)
                written = _written(value, entity)
                frame = templates.frames_for(locale, entity, difficulty, split, idx)

                previous = None
                if difficulty == "correction":
                    previous = _previous_value(value, entity, locale, extra, idx)
                    prev_spoken = _spoken(previous, entity, locale, "direct")
                    prev_written = _written(previous, entity)
                    synthesis_text = frame.format(e=spoken, prev=prev_spoken)
                    written_text = frame.format(e=written, prev=prev_written)
                else:
                    synthesis_text = frame.format(e=spoken)
                    written_text = frame.format(e=written)

                variants = _accepted_variants(entity, value)
                scenarios.append(
                    Scenario.model_validate(
                        {
                            "schema_version": SCHEMA_VERSION,
                            "scenario_id": sid,
                            "split": split,
                            "locale": locale,
                            "entity_type": entity,
                            "template_family": fam,
                            "difficulty_tags": [tag],
                            "written_text": written_text,
                            "synthesis_text": synthesis_text,
                            "entities": [_entity_dict(entity, value, written, variants)],
                            "previous_mentions": (
                                [{"type": entity, "value": _as_gold_value(previous, entity)}]
                                if previous is not None
                                else []
                            ),
                            "seed": int(sha256_text(sid)[:8], 16) % (2**31),
                        }
                    )
                )
    return scenarios


def _difficulty_tag(entity: str, difficulty: str) -> str:
    if difficulty == "direct":
        return "direct"
    if difficulty == "tricky":
        return "phonetic" if entity in ("phone", "calendar_value", "reference_code") else "orthographic"
    if difficulty == "segmented":
        return "spelling" if entity in ("person_name", "email", "reference_code") else "segmented"
    return "correction"


def _accepted_variants(entity: str, value: Any) -> list[str]:
    if entity == "person_name" and isinstance(value, str) and "-" in value:
        return [value.replace("-", " ")]  # hyphenated surnames may be spoken with a pause
    return []


def cli_build(config: str, out: str) -> dict[str, Any]:
    out_dir = Path(out)
    out_dir.mkdir(parents=True, exist_ok=True)
    gold_dir = out_dir / "gold"
    gold_dir.mkdir(exist_ok=True)

    scenarios = build_corpus()
    lines = [s.model_dump_json() for s in sorted(scenarios, key=lambda s: s.scenario_id)]
    write_text_atomic(gold_dir / "scenarios.jsonl", "\n".join(lines) + "\n")

    summary = corpus_summary(scenarios)
    write_text_atomic(out_dir / "corpus_manifest.json", json.dumps(summary, ensure_ascii=False, indent=1))
    return summary


def corpus_summary(scenarios: list[Scenario]) -> dict[str, Any]:
    from collections import Counter

    per_cell: Counter = Counter()
    split_counts: Counter = Counter()
    difficulty_counts: Counter = Counter()
    for s in scenarios:
        per_cell[(s.locale, s.entity_type)] += 1
        split_counts[s.split] += 1
        difficulty_counts[tuple(s.difficulty_tags)] += 1
    return {
        "total_scenarios": len(scenarios),
        "splits": dict(split_counts),
        "per_cell": {f"{loc}|{ent}": n for (loc, ent), n in sorted(per_cell.items())},
        "difficulty_mix": {"+".join(k): v for k, v in sorted(difficulty_counts.items())},
        "corpus_hash": sha256_text("\n".join(sorted(s.scenario_id for s in scenarios))),
    }

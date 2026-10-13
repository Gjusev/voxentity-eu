"""Corpus validation gates (docs/09 P2, docs/10 test matrix).

Checks counts, splits, family/value separation across splits, correction
semantics and that no pair leaks between dev and test.
"""

from __future__ import annotations

from collections import Counter
from typing import Any

from ..contracts import AudioRecord, Scenario
from ..scoring.normalize import canonical_form


def validate_corpus(scenarios: list[Scenario]) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []

    # --- counts
    # suite layout: main = 180 (de+fr), es = 90; every locale contributes
    # 6 cells x 15 cases
    locales_present = sorted({s.locale for s in scenarios})
    expected_total = 15 * 6 * len(locales_present)
    if len(scenarios) != expected_total:
        errors.append(f"expected {expected_total} scenarios for locales {locales_present}, found {len(scenarios)}")
    per_cell: Counter = Counter((s.locale, s.entity_type) for s in scenarios)
    for locale in locales_present:
        for entity in (
            "person_name", "phone", "email", "calendar_value", "postal_address", "reference_code"
        ):
            n = per_cell.get((locale, entity), 0)
            if n != 15:
                errors.append(f"cell {locale}/{entity}: {n} scenarios, expected 15")
    per_locale_dev = 5 * 6
    split_counts = Counter(s.split for s in scenarios)
    if split_counts.get("dev", 0) != per_locale_dev * len(locales_present) or (
        split_counts.get("test", 0) != 10 * 6 * len(locales_present)
    ):
        errors.append(
            f"split sizes {dict(split_counts)}, expected "
            f"{per_locale_dev * len(locales_present)} dev / {10 * 6 * len(locales_present)} test"
        )

    # --- difficulty mix per cell
    for locale in locales_present:
        for entity in (
            "person_name", "phone", "email", "calendar_value", "postal_address", "reference_code"
        ):
            cell = [s for s in scenarios if s.locale == locale and s.entity_type == entity]
            buckets = Counter()
            for s in cell:
                tags = set(s.difficulty_tags)
                if tags == {"direct"}:
                    buckets["direct"] += 1
                elif "correction" in tags:
                    buckets["correction"] += 1
                elif tags & {"segmented", "spelling"}:
                    buckets["segmented"] += 1
                elif tags & {"orthographic", "phonetic"}:
                    buckets["tricky"] += 1
                else:
                    errors.append(f"{s.scenario_id}: unrecognized difficulty tags {tags}")
            expected = {"direct": 5, "tricky": 4, "segmented": 3, "correction": 3}
            if dict(buckets) != expected:
                errors.append(f"{locale}/{entity}: difficulty mix {dict(buckets)} != {expected}")

    # --- unique scenario ids
    ids = [s.scenario_id for s in scenarios]
    if len(set(ids)) != len(ids):
        dupes = [i for i, c in Counter(ids).items() if c > 1]
        errors.append(f"duplicate scenario ids: {dupes[:5]}")

    # --- families bound to exactly one split
    fam_splits: dict[str, set[str]] = {}
    for s in scenarios:
        fam_splits.setdefault(s.template_family, set()).add(s.split)
    for fam, splits in fam_splits.items():
        if len(splits) > 1:
            errors.append(f"template family {fam} appears in splits {sorted(splits)}")

    # --- value separation across splits (canonical forms per locale × entity)
    for locale in locales_present:
        for entity in (
            "person_name", "phone", "email", "calendar_value", "postal_address", "reference_code"
        ):
            cell = [s for s in scenarios if s.locale == locale and s.entity_type == entity]
            seen: dict[str, tuple[str, str]] = {}  # canonical -> (scenario_id, split)
            for s in cell:
                for e in s.entities:
                    key = repr(canonical_form(e.canonical_value, s.entity_type, s.locale))
                    if key in seen and seen[key][1] != s.split:
                        errors.append(
                            f"equivalent value in both splits: {s.scenario_id} and {seen[key][0]} ({entity})"
                        )
                    seen.setdefault(key, (s.scenario_id, s.split))
                for m in s.previous_mentions:
                    key = repr(canonical_form(m.value, m.type, s.locale))
                    if key in seen and seen[key][1] != s.split:
                        errors.append(
                            f"previous-mention value leaks across splits: {s.scenario_id} vs {seen[key][0]}"
                        )
                    seen.setdefault(key, (s.scenario_id, s.split))

    # --- correction semantics
    for s in scenarios:
        if "correction" in s.difficulty_tags:
            if not s.previous_mentions:
                errors.append(f"{s.scenario_id}: correction without previous mention")
                continue
            final = canonical_form(s.entities[0].canonical_value, s.entity_type, s.locale)
            prev = canonical_form(s.previous_mentions[-1].value, s.entity_type, s.locale)
            if repr(final) == repr(prev):
                errors.append(f"{s.scenario_id}: correction previous value equals final")
            if s.entities[0].mention_text not in s.written_text:
                errors.append(f"{s.scenario_id}: mention_text not part of written_text")
        else:
            if s.previous_mentions:
                errors.append(f"{s.scenario_id}: previous_mentions only allowed for corrections")
            if s.entities[0].mention_text not in s.written_text:
                errors.append(f"{s.scenario_id}: mention_text not part of written_text")

    # --- synthesis text must be fully verbalized: phones say 'Plus', never '+'
    for s in scenarios:
        if "+" in s.synthesis_text:
            errors.append(f"{s.scenario_id}: synthesis_text contains raw '+'")

    return {"errors": errors, "warnings": warnings, "total": len(scenarios)}


def cli_validate(manifest_path: str, gold_path: str) -> dict[str, Any]:
    from ..commands import InvalidInput, QualityGateFailed
    from ..contracts import read_jsonl

    scenarios = list(read_jsonl(gold_path, Scenario))
    report = validate_corpus(scenarios)

    try:
        audio = list(read_jsonl(manifest_path, AudioRecord))
    except FileNotFoundError as exc:
        report["warnings"].append(f"audio manifest not found yet ({exc.filename}); corpus-only checks ran")
        audio = []
    if audio:
        from ..contracts import check_references, check_unique_ids

        try:
            check_unique_ids(audio, "audio_id")
            scenario_ids = {s.scenario_id for s in scenarios}
            check_references(audio, scenario_ids)
        except ValueError as exc:
            report["errors"].append(f"audio integrity: {exc}")
        # pair leakage: telephone rows must pair with a clean row of the same
        # scenario; a scenario can never span splits (covered above for values)
        split_by_scenario = {s.scenario_id: s.split for s in scenarios}
        clean_scenarios = {a.scenario_id for a in audio if a.condition == "clean"}
        by_id = {a.audio_id: a for a in audio}
        for a in audio:
            if a.corpus != "synthetic":
                continue
            if a.condition == "telephone" and a.scenario_id not in clean_scenarios:
                report["errors"].append(f"telephone audio without clean pair: {a.audio_id}")
            parent = by_id.get(a.parent_audio_id) if a.parent_audio_id else None
            if parent is not None:
                if split_by_scenario.get(parent.scenario_id) != split_by_scenario.get(a.scenario_id):
                    report["errors"].append(f"pair spans splits: {a.audio_id}")

    if report["errors"]:
        raise QualityGateFailed(f"{len(report['errors'])} corpus validation errors: {report['errors'][:5]}")
    if not scenarios:
        raise InvalidInput("no scenarios found")
    return {"validated": report["total"], "errors": 0, "result": "ok"}

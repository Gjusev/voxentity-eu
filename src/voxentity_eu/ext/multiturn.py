"""Cross-turn correction suite: does the agent's FINAL stored state follow the caller?

Each case has two caller turns spoken by the same voice:
- correction:   t1 gives A, t2 corrects to B (a near-miss of A)  -> gold B
- confirmation: t1 gives A, t2 confirms without restating it      -> gold A
- repeat:       t1 gives A, t2 repeats A                          -> gold A

Per cell (locale x entity): dev = 1 correction + 1 confirmation; test = 2
corrections + 1 confirmation + 1 repeat. Turns are synthesized as ordinary
single-audio Scenario "vehicles" (ids mt-<split>-<lang>-<entity>-t<turn>-<i>) so
synthesis, channel, export and ASR reuse the core pipeline; the multi-turn gold
lives in gold/multiturn_cases.jsonl and is only read by score_suite().
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Literal

import numpy as np

from ..contracts import SCHEMA_VERSION, Entity, Scenario, StrictModel
from ..corpus import generate as core
from ..corpus import pools
from ..provenance import sha256_text, write_text_atomic

SUITE = "multiturn"
LOCALES = ("de-DE", "fr-FR")
ENTITIES = ("phone", "email", "calendar_value", "reference_code")
SHORT = {"phone": "phone", "email": "mail", "calendar_value": "date", "reference_code": "ref"}
PLAN = {"dev": ["correction", "confirmation"], "test": ["correction", "correction", "confirmation", "repeat"]}
NOUN = {
    ("de-DE", "phone"): "Nummer", ("de-DE", "email"): "Mailadresse",
    ("de-DE", "calendar_value"): "Termin", ("de-DE", "reference_code"): "Referenz",
    ("fr-FR", "phone"): "numéro", ("fr-FR", "email"): "adresse mail",
    ("fr-FR", "calendar_value"): "rendez-vous", ("fr-FR", "reference_code"): "référence",
}
TURN1 = {"de-DE": {"dev": "Meine {n} ist {v}.", "test": "Notieren Sie bitte: {n} {v}."},
         "fr-FR": {"dev": "Ma {n} est {v}.", "test": "Notez bien, {n} : {v}."}}
TURN2 = {
    "de-DE": {"correction": {"dev": "Moment, das war falsch. Richtig ist {v}.",
                             "test": "Entschuldigung, ich korrigiere mich: {v}."},
              "confirmation": {"dev": "Ja, genau, das stimmt.", "test": "Ja, so ist es richtig."},
              "repeat": {"test": "Ich wiederhole: {v}."}},
    "fr-FR": {"correction": {"dev": "Attendez, c'était faux. La bonne valeur est {v}.",
                             "test": "Pardon, je me suis trompé : {v}."},
              "confirmation": {"dev": "Oui, c'est exact.", "test": "Oui, c'est bien ça."},
              "repeat": {"test": "Je répète : {v}."}},
}


class Turn(StrictModel):
    scenario_id: str
    written_text: str
    synthesis_text: str


class MultiTurnCase(StrictModel):
    case_id: str
    split: Literal["dev", "test"]
    locale: str
    entity_type: str
    kind: Literal["correction", "confirmation", "repeat"]
    turns: list[Turn]
    first: Entity
    final: Entity


def _values(locale: str, entity: str, n: int) -> list[Any]:
    pool = {"phone": pools.phone_pool, "email": pools.email_pool,
            "calendar_value": pools.calendar_pool, "reference_code": pools.reference_pool}[entity]
    return pool(locale, 40 + n)[40:]


def _entity(entity: str, value: Any) -> Entity:
    return Entity.model_validate(core._entity_dict(entity, value, core._written(value, entity), []))


def build_cases() -> list[MultiTurnCase]:
    cases: list[MultiTurnCase] = []
    for locale in LOCALES:
        for entity in ENTITIES:
            kinds = [("dev", k) for k in PLAN["dev"]] + [("test", k) for k in PLAN["test"]]
            values = _values(locale, entity, len(kinds) + 4)
            noun = NOUN[(locale, entity)]
            for i, (split, kind) in enumerate(kinds):
                a = values[i]
                b = core._previous_value(a, entity, locale, values[len(kinds):], i)  # near-miss
                t2 = TURN2[locale][kind][split if kind != "repeat" else "test"]
                second = b if kind == "correction" else a
                base = f"mt-{split}-{locale[:2]}-{SHORT[entity]}"
                turns = [
                    Turn(scenario_id=f"{base}-t1-{i:03d}",
                         written_text=TURN1[locale][split].format(n=noun, v=core._written(a, entity)),
                         synthesis_text=TURN1[locale][split].format(n=noun, v=core._spoken(a, entity, locale, "direct"))),
                    Turn(scenario_id=f"{base}-t2-{i:03d}",
                         written_text=t2.format(v=core._written(second, entity)),
                         synthesis_text=t2.format(v=core._spoken(second, entity, locale, "direct"))),
                ]
                cases.append(MultiTurnCase(
                    case_id=f"{base}-{i:03d}", split=split, locale=locale, entity_type=entity, kind=kind,
                    turns=turns, first=_entity(entity, a), final=_entity(entity, b if kind == "correction" else a)))
    return cases


def vehicle_scenarios(cases: list[MultiTurnCase]) -> list[Scenario]:
    """One single-audio Scenario per turn, only to drive synthesis and ASR."""

    out = []
    for c in cases:
        for t, label in zip(c.turns, (c.first, c.final), strict=True):  # value each turn carries
            out.append(Scenario.model_validate({
                "schema_version": SCHEMA_VERSION, "scenario_id": t.scenario_id, "split": c.split,
                "locale": c.locale, "entity_type": c.entity_type,
                "template_family": f"mt_{c.locale[:2]}_{c.kind}_{c.split}",
                "difficulty_tags": ["direct"], "written_text": t.written_text,
                "synthesis_text": t.synthesis_text,
                "entities": [label.model_dump()], "previous_mentions": [],
                "seed": int(sha256_text(t.scenario_id)[:8], 16),
            }))
    return out


def build_suite(out_dir: Path) -> dict:
    cases = build_cases()
    case_lines = "\n".join(c.model_dump_json() for c in cases) + "\n"
    write_text_atomic(out_dir / "gold" / "multiturn_cases.jsonl", case_lines)
    write_text_atomic(out_dir / "gold" / "scenarios.jsonl",
                      "\n".join(s.model_dump_json() for s in vehicle_scenarios(cases)) + "\n")
    manifest = {"suite": SUITE, "cases": len(cases), "turn_audios_clean": 2 * len(cases),
                "splits": {sp: sum(c.split == sp for c in cases) for sp in ("dev", "test")},
                "kinds": {k: sum(c.kind == k for c in cases) for k in ("correction", "confirmation", "repeat")},
                "corpus_hash": sha256_text(case_lines)}
    write_text_atomic(out_dir / "corpus_manifest.json", json.dumps(manifest, indent=1))
    return manifest


# --- evaluation ---------------------------------------------------------------------


def _canon(entity: Entity | None, raw: str | None, etype: str, locale: str):
    from ..scoring.normalize import canonical_form, parse_slot_value

    if entity is not None:
        return canonical_form(entity.canonical_value, etype, locale, case_sensitive=True)
    if raw is None:
        return None
    try:
        return canonical_form(parse_slot_value(raw, etype, locale), etype, locale, case_sensitive=True)
    except (ValueError, TypeError):
        return ("unparseable", raw)


def run_agent(cases: list[MultiTurnCase], transcripts: dict[str, str | None], store_root: Path, condition: str) -> list[dict]:
    """Reference agent over both turns of each case; reads the persisted final state.

    transcripts: turn audio_id (scenario_id, '-tel' suffix for telephone) -> text.
    """

    from ..adapters.agent import AgentStore
    from ..adapters.slots import extract

    store = AgentStore(store_root)
    rows = []
    suffix = "-tel" if condition == "telephone" else ""
    for c in cases:
        sid = f"{c.case_id}-{condition}"
        store.create_session(sid, c.entity_type)
        turn_values: list[str | None] = []
        for t in c.turns:
            text = transcripts.get(t.scenario_id + suffix)
            r = extract(text or "", c.entity_type, c.locale)
            value = r.slots[0]["value"] if r.status == "ok" and r.slots else None
            turn_values.append(value)
            if value is not None:
                store.store_slot(sid, c.entity_type, value)  # replacement semantics
        store.finalize(sid)
        state = store.read_state(sid)
        final = next((s["value"] for s in state["final_slots"] if s["type"] == c.entity_type), None)
        rows.append({"case_id": c.case_id, "condition": condition, "turn_values": turn_values,
                     "final_value": final, "transcripts": [transcripts.get(t.scenario_id + suffix) for t in c.turns]})
    return rows


def score_rows(cases: list[MultiTurnCase], rows: list[dict]) -> list[dict]:
    by_id = {c.case_id: c for c in cases}
    out = []
    for r in rows:
        c = by_id[r["case_id"]]
        gold_final = _canon(c.final, None, c.entity_type, c.locale)
        gold_first = _canon(c.first, None, c.entity_type, c.locale)
        got = _canon(None, r["final_value"], c.entity_type, c.locale)
        t1 = _canon(None, r["turn_values"][0], c.entity_type, c.locale)
        t2 = _canon(None, r["turn_values"][1], c.entity_type, c.locale)
        expected_t2 = gold_final if c.kind != "confirmation" else None
        if got == gold_final:
            outcome = "correct"
        elif got is None:
            outcome = "omission"
        elif c.kind == "correction" and got == gold_first:
            outcome = "stale"
        elif c.kind != "correction" and t1 == gold_first:
            outcome = "spurious_change"  # turn 1 stored the right value; turn 2 moved the state off it
        else:  # includes a misheard turn 1 that turn 2 never touched (not a persistence failure)
            outcome = "wrong_value"
        out.append({**r, "split": c.split, "locale": c.locale, "entity_type": c.entity_type, "kind": c.kind,
                    "outcome": outcome, "correct": outcome == "correct",
                    "turns_extracted_ok": t1 == gold_first and t2 == expected_t2})
    return out


def _ci(flags: list[bool], seed: int = 20260101, reps: int = 2000) -> list[float] | None:
    if not flags:
        return None
    rng = np.random.default_rng(seed)
    arr = np.array(flags, dtype=float)
    stats = arr[rng.integers(0, len(arr), size=(reps, len(arr)))].mean(axis=1)
    return [float(x) for x in np.percentile(stats, [2.5, 97.5])]


def summarize(scored: list[dict], split: str = "test") -> dict:
    rows = [r for r in scored if r["split"] == split]

    def block(rs: list[dict]) -> dict:
        flags = [r["correct"] for r in rs]
        cond = [r["correct"] for r in rs if r["turns_extracted_ok"]]
        return {"n": len(rs), "final_state_accuracy": sum(flags) / len(rs) if rs else None, "ci95": _ci(flags),
                "outcomes": {o: sum(r["outcome"] == o for r in rs)
                             for o in ("correct", "stale", "spurious_change", "omission", "wrong_value")},
                "n_turns_extracted_ok": len(cond),
                "final_state_accuracy_given_turns_ok": sum(cond) / len(cond) if cond else None}

    return {"split": split, "overall": block(rows),
            "by_condition": {k: block([r for r in rows if r["condition"] == k]) for k in ("clean", "telephone")},
            "by_kind": {k: block([r for r in rows if r["kind"] == k]) for k in ("correction", "confirmation", "repeat")},
            "by_entity": {e: block([r for r in rows if r["entity_type"] == e]) for e in ENTITIES}}

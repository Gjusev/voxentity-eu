"""Deterministic offline scoring: gold + predictions -> per-example verdicts.

The scorer never calls the network, never sees filenames that encode answers
(rejected upstream by export-inputs) and reads the agent's *observed final
state* rather than trusting spoken words.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..contracts import (
    AudioRecord,
    Prediction,
    Scenario,
    validate_predictions_against_audio,
)
from .normalize import (
    NORMALIZER_VERSION,
    canonical_form,
    literal_form,
    parse_slot_value,
)

OUTCOME_LABELS = ("correct", "omission", "substitution", "failure")


@dataclass
class ExampleResult:
    audio_id: str
    scenario_id: str
    run_id: str
    locale: str
    entity_type: str
    condition: str
    split: str
    difficulty_tags: list[str]
    status: str  # prediction row status
    outcome: str  # correct | omission | substitution | failure
    literal_correct: bool
    canonical_correct: bool
    extra_output: bool
    stale_value: bool
    is_correction_case: bool
    predicted_value: str | None
    gold_literal: str
    predicted_slot_types: list[str]
    error_type: str | None

    @property
    def correct(self) -> bool:
        return self.outcome == "correct"


class RunIntegrityError(Exception):
    pass


class IncompleteRun(Exception):
    def __init__(self, missing: list[str]) -> None:
        self.missing = missing
        super().__init__(f"{len(missing)} eligible audio rows have no prediction: {missing[:5]}...")


def _load_agent_state(path: str, state_root: Path | None) -> list[dict[str, Any]]:
    """Read the observed final agent state; the only evidence for agent_slots."""

    p = Path(path)
    if not p.is_absolute() and state_root is not None:
        p = state_root / p
    try:
        raw = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise RunIntegrityError(f"unreadable observed final state {path}: {exc}") from exc
    slots = raw.get("final_slots")
    if slots is None:
        raise RunIntegrityError(f"observed final state {path} lacks final_slots")
    return list(slots)


def score_example(
    scenario: Scenario,
    prediction: Prediction,
    audio: AudioRecord,
    *,
    state_root: Path | None = None,
) -> ExampleResult:
    entity = scenario.entities[0]
    target_type = scenario.entity_type
    is_correction = bool(scenario.previous_mentions)

    gold_canonical = canonical_form(
        entity.canonical_value, target_type, scenario.locale,
        case_sensitive=entity.case_sensitive or True,
    )
    gold_literal = literal_form(entity.canonical_value)
    variant_canonicals = [
        canonical_form(v, target_type, scenario.locale, case_sensitive=entity.case_sensitive or True)
        for v in entity.accepted_variants
    ]

    # Where do candidate slots come from?
    if prediction.track == "agent_slots" and prediction.status == "ok":
        state_slots = _load_agent_state(prediction.observed_final_state_path or "", state_root)
        candidate_slots = [s for s in state_slots if s.get("type") == target_type]
        all_slots = state_slots
    else:
        candidate_slots = [s for s in prediction.predicted_slots if s.type == target_type]
        all_slots = [{"type": s.type} for s in prediction.predicted_slots]

    predicted_value: str | None = None
    literal_correct = False
    canonical_correct = False
    extra_output = False
    stale_value = False

    if prediction.status in ("error", "timeout", "unsupported"):
        outcome = "failure"
    elif not candidate_slots:
        outcome = "omission"
    else:
        predicted_value = str(candidate_slots[0].get("value", "") if isinstance(candidate_slots[0], dict) else candidate_slots[0].value)
        structured = parse_slot_value(predicted_value, target_type, scenario.locale)
        pred_literal = literal_form(structured)
        pred_canonical = canonical_form(
            structured, target_type, scenario.locale,
            case_sensitive=entity.case_sensitive or True,
        )
        literal_correct = pred_literal == gold_literal
        canonical_correct = pred_canonical == gold_canonical or pred_canonical in variant_canonicals
        outcome = "correct" if canonical_correct else "substitution"

        if is_correction and scenario.previous_mentions:
            prev = scenario.previous_mentions[-1].value
            prev_canonical = canonical_form(prev, target_type, scenario.locale)
            if pred_canonical == prev_canonical:
                stale_value = True

    # extra output: unsolicited slot types or duplicates of the target type
    type_counts: dict[str, int] = {}
    for s in all_slots:
        t = s.get("type") if isinstance(s, dict) else s.type
        type_counts[t] = type_counts.get(t, 0) + 1
    extra_output = any(t != target_type for t in type_counts) or type_counts.get(target_type, 0) > 1

    return ExampleResult(
        audio_id=prediction.audio_id,
        scenario_id=scenario.scenario_id,
        run_id=prediction.run_id,
        locale=scenario.locale,
        entity_type=target_type,
        condition=audio.condition,
        split=scenario.split,
        difficulty_tags=list(scenario.difficulty_tags),
        status=prediction.status,
        outcome=outcome,
        literal_correct=literal_correct,
        canonical_correct=canonical_correct,
        extra_output=extra_output,
        stale_value=stale_value,
        is_correction_case=is_correction,
        predicted_value=predicted_value,
        gold_literal=gold_literal,
        predicted_slot_types=sorted(type_counts),
        error_type=prediction.error_type,
    )


def score_run(
    scenarios: list[Scenario],
    audio: list[AudioRecord],
    predictions: list[Prediction],
    *,
    state_root: Path | None = None,
    splits: tuple[str, ...] = ("test",),
    require_complete: bool = True,
) -> dict[str, Any]:
    """Score one run; raises on integrity errors, flags incompleteness."""

    scenario_by_id = {s.scenario_id: s for s in scenarios}
    audio_by_id = {a.audio_id: a for a in audio}
    eligible = {
        a.audio_id: a
        for a in audio
        if a.corpus == "synthetic"
        and a.qa_status == "accepted"
        and scenario_by_id.get(a.scenario_id) is not None
        and scenario_by_id[a.scenario_id].split in splits
    }

    validate_predictions_against_audio(list(predictions), set(audio_by_id))

    by_run: dict[str, list[Prediction]] = {}
    for p in predictions:
        by_run.setdefault(p.run_id, []).append(p)
    if len(by_run) > 1:
        raise RunIntegrityError(f"mixed run_ids in one predictions file: {sorted(by_run)}")
    run_id = next(iter(by_run)) if by_run else ""

    covered = {p.audio_id for p in predictions}
    missing = sorted(set(eligible) - covered)
    if missing and require_complete:
        raise IncompleteRun(missing)

    results: list[ExampleResult] = []
    for p in predictions:
        a = audio_by_id.get(p.audio_id)
        if a is None or a.audio_id not in eligible:
            continue
        sc = scenario_by_id[a.scenario_id]
        results.append(score_example(sc, p, a, state_root=state_root))

    return {
        "run_id": run_id,
        "normalizer_version": NORMALIZER_VERSION,
        "splits": list(splits),
        "expected_count": len(eligible),
        "scored_count": len(results),
        "missing_audio_ids": missing,
        "incomplete": bool(missing),
        "results": results,
    }


# --- CLI entry -----------------------------------------------------------------


def cli_score(gold_path: str, predictions_path: str, manifest_path: str, out_path: str) -> dict:
    from ..contracts import read_jsonl
    from .aggregate import summarize

    scenarios = list(read_jsonl(gold_path, Scenario))
    audio = list(read_jsonl(manifest_path, AudioRecord))
    predictions = list(read_jsonl(predictions_path, Prediction))

    # Inference worked on opaque input ids; scoring translates them back via the
    # gold-side mapping written by export-inputs (separate access paths, docs/04).
    gold_dir = Path(gold_path).resolve().parent
    mapping: dict[str, str] = {}
    for map_file in sorted(gold_dir.glob("input_mapping_*.json")):
        mapping.update(json.loads(map_file.read_text(encoding="utf-8")))
    if mapping:
        translated = []
        for p in predictions:
            data = p.model_dump()
            if data["audio_id"] in mapping:
                data["audio_id"] = mapping[data["audio_id"]]
            translated.append(Prediction.model_validate(data))
        predictions = translated

    state_root = Path(predictions_path).resolve().parent
    try:
        payload = score_run(scenarios, audio, predictions, state_root=state_root)
    except IncompleteRun as exc:
        payload = {
            "run_id": "",
            "incomplete": True,
            "missing_audio_ids": exc.missing,
            "results": [],
            "error": "incomplete run: not eligible for ranking",
        }
        _write_scored(out_path, payload)
        raise
    payload["summary"] = summarize(payload["results"])
    _write_scored(out_path, payload)
    return {
        "run_id": payload["run_id"],
        "scored": payload["scored_count"],
        "out": out_path,
        "slot_accuracy": payload["summary"]["overall"]["slot_accuracy"],
    }


def _write_scored(out_path: str, payload: dict[str, Any]) -> None:
    from ..provenance import write_text_atomic

    def _ser(obj: Any) -> Any:
        if isinstance(obj, ExampleResult):
            return obj.__dict__
        raise TypeError(f"unserializable {type(obj)}")

    write_text_atomic(out_path, json.dumps(payload, ensure_ascii=False, default=_ser, indent=1))

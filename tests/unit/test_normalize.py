"""Hand-computed scorer fixtures and negative controls (docs/10-validation.md)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from voxentity_eu.contracts import AudioRecord, Prediction, Scenario
from voxentity_eu.scoring.bootstrap import bootstrap_ci, bootstrap_paired_difference
from voxentity_eu.scoring.match import IncompleteRun, RunIntegrityError, score_example, score_run
from voxentity_eu.scoring.normalize import (
    canonical_email,
    canonical_person_name,
    canonical_phone,
    canonical_reference_code,
    literal_form,
)


def scenario(**over) -> Scenario:
    base = {
        "schema_version": "0.2",
        "scenario_id": "sc",
        "split": "test",
        "locale": "de-DE",
        "entity_type": "phone",
        "template_family": "f",
        "difficulty_tags": ["direct"],
        "written_text": "x",
        "synthesis_text": "x",
        "entities": [
            {
                "entity_id": "target-1",
                "type": "phone",
                "canonical_value": "+491701234567",
                "mention_text": "+49 170 1234567",
                "target": True,
            }
        ],
        "previous_mentions": [],
        "seed": 1,
    }
    base.update(over)
    return Scenario.model_validate(base)


def audio(audio_id: str = "au", condition: str = "clean", scenario_id: str = "sc") -> AudioRecord:
    return AudioRecord.model_validate(
        {
            "audio_id": audio_id,
            "scenario_id": scenario_id,
            "corpus": "synthetic",
            "condition": condition,
            "path": f"audio/{audio_id}.wav",
            "sha256": "a" * 64,
            "sample_rate_hz": 16000,
            "num_samples": 16000,
            "duration_seconds": 1.0,
            "qa_status": "accepted",
        }
    )


def prediction(value: str | None, status: str = "ok", slot_type: str = "phone", **over) -> Prediction:
    row = {
        "run_id": "r1",
        "audio_id": "au",
        "track": "asr_slots",
        "status": status,
        "transcript": None,
        "error_type": None,
    }
    if status == "ok":
        row["predicted_slots"] = [{"type": slot_type, "value": value}] if value is not None else []
    else:
        row["predicted_slots"] = []
        row["error_type"] = status
    row.update(over)
    return Prediction.model_validate(row)


# --- normalization: the adversarial matrix --------------------------------------


def test_phone_loses_leading_zero_is_incorrect():
    # caller said +49 170 1234567; system dropped the + and the digit kept is wrong shape
    assert canonical_phone("+49 170 1234 567", "de-DE") == "+491701234567"
    assert canonical_phone("0170 1234567", "de-DE") == "+491701234567"  # declared trunk rule
    assert canonical_phone("1701234567", "de-DE") == "1701234567"  # lost trunk zero -> mismatch
    assert canonical_phone("0049 170 1234567", "de-DE") == "+491701234567"  # 00-prefix rule
    # leading zeros after the prefix are preserved
    assert canonical_phone("+49 0170", "de-DE") == "+490170"


def test_sharp_s_and_accents_stay_distinct():
    assert canonical_person_name("Weiß") == "weiß"
    assert canonical_person_name("weiss") == "weiss"
    assert canonical_person_name("Weiß") != canonical_person_name("weiss")
    assert canonical_person_name("Élodie") == "élodie"
    assert canonical_person_name("Elodie") == "elodie"
    assert canonical_person_name("Élodie") != canonical_person_name("Elodie")


def test_reference_code_o_vs_zero_is_incorrect():
    assert canonical_reference_code("AB-O75") != canonical_reference_code("AB-075")
    assert canonical_reference_code("AB-I7") != canonical_reference_code("AB-17")
    # case policy is public per contract: default sensitive
    assert canonical_reference_code("ab-075") != canonical_reference_code("AB-075")
    assert canonical_reference_code("ab-075", case_sensitive=False) == canonical_reference_code(
        "AB-075", case_sensitive=False
    )
    assert canonical_reference_code("AB 075") == canonical_reference_code("AB075")
    assert canonical_reference_code("AB075") != canonical_reference_code("AB-075")  # hyphen lost


def test_email_domain_and_char_changes_are_incorrect():
    assert canonical_email("Anna.Weber@example.com") == "Anna.Weber@example.com"
    assert canonical_email("anna.weber@EXAMPLE.com") == "anna.weber@example.COM".lower()
    assert canonical_email("Anna.Weber@example.org") != canonical_email("Anna.Weber@example.com")
    assert canonical_email("Anna.Weber1@example.com") != canonical_email("Anna.Weber@example.com")
    # local part case is preserved by default
    assert canonical_email("Anna.Weber@example.com") != canonical_email("anna.weber@example.com")


# --- single digit / accent error detection ---------------------------------------


def test_single_digit_swap_detected():
    sc = scenario()
    pred = prediction("+49 170 1234 576")
    res = score_example(sc, pred, audio())
    assert res.outcome == "substitution"
    assert not res.canonical_correct


def test_single_accent_loss_detected():
    sc = scenario(
        locale="fr-FR",
        entity_type="person_name",
        entities=[
            {
                "entity_id": "target-1",
                "type": "person_name",
                "canonical_value": "Élodie Mercier",
                "mention_text": "Élodie Mercier",
                "target": True,
            }
        ],
    )
    res = score_example(sc, prediction("Elodie Mercier", slot_type="person_name"), audio())
    assert res.outcome == "substitution"
    ok = score_example(sc, prediction("élodie  mercier", slot_type="person_name"), audio())  # case + doubled space forgiven
    assert ok.outcome == "correct"


def test_correction_returning_first_mention_is_stale_and_incorrect():
    sc = scenario(
        difficulty_tags=["correction"],
        previous_mentions=[{"type": "phone", "value": "+491701234000"}],
    )
    res = score_example(sc, prediction("+49 170 1234 000"), audio())
    assert res.outcome == "substitution"
    assert res.stale_value is True
    fixed = score_example(sc, prediction("+49 170 1234 567"), audio())
    assert fixed.outcome == "correct" and fixed.stale_value is False


def test_calendar_missing_requested_component_is_incorrect_without_gold_inference():
    sc = scenario(
        entity_type="calendar_value",
        entities=[
            {
                "entity_id": "target-1",
                "type": "calendar_value",
                "canonical_value": {"day": 14, "month": 3, "year": 2027},
                "mention_text": "vierzehnten März zweitausendsiebenundzwanzig",
                "target": True,
            }
        ],
    )
    # extractor recovered day and month but no year -> must NOT borrow 2027 from gold
    res = score_example(sc, prediction("14. März", slot_type="calendar_value"), audio())
    assert res.outcome == "substitution"
    assert score_example(sc, prediction("14. März 2027", slot_type="calendar_value"), audio()).outcome == "correct"


def test_address_street_right_number_wrong_is_incorrect():
    sc = scenario(
        entity_type="postal_address",
        entities=[
            {
                "entity_id": "target-1",
                "type": "postal_address",
                "canonical_value": {
                    "street": "Eichenweg",
                    "house_number": "4a",
                    "postal_code": "10115",
                    "locality": "Berlin",
                },
                "mention_text": "Eichenweg 4a, 10115 Berlin",
                "target": True,
            }
        ],
    )
    wrong_number = score_example(sc, prediction("Eichenweg 4, 10115 Berlin", slot_type="postal_address"), audio())
    assert wrong_number.outcome == "substitution"
    # street case and postal formatting forgiven, suffix exact
    ok = score_example(sc, prediction("Eichenweg 4a, 10115 Berlin", slot_type="postal_address"), audio())
    assert ok.outcome == "correct"


def test_postal_house_number_suffix_case_matters():
    sc = scenario(
        entity_type="postal_address",
        entities=[
            {
                "entity_id": "target-1",
                "type": "postal_address",
                "canonical_value": {
                    "street": "Eichenweg",
                    "house_number": "4a",
                    "postal_code": "10115",
                    "locality": "Berlin",
                },
                "mention_text": "Eichenweg 4a, 10115 Berlin",
                "target": True,
            }
        ],
    )
    res = score_example(sc, prediction("Eichenweg 4A, 10115 Berlin", slot_type="postal_address"), audio())
    # exact suffix comparison: 4A != 4a
    assert res.outcome == "substitution"


# --- run-level integrity ----------------------------------------------------------


def test_duplicate_row_is_run_error():
    sc = scenario()
    au = audio()
    preds = [prediction("+49 170 1234 567"), prediction("+49 170 1234 567")]
    with pytest.raises(Exception, match="duplicate"):
        score_run([sc], [au], preds)


def test_foreign_id_is_run_error():
    with pytest.raises(Exception, match="unknown audio_id"):
        score_run([scenario()], [audio()], [prediction("x") and prediction("+49 170 1234 567", audio_id="au-foreign")])


def test_timeout_with_valid_id_participates_as_failure():
    sc = scenario()
    res = score_example(sc, prediction(None, status="timeout"), audio())
    assert res.outcome == "failure"
    payload = score_run([sc], [audio()], [prediction(None, status="timeout")])
    assert payload["scored_count"] == 1
    assert payload["summary"] if "summary" in payload else True


def test_missing_prediction_marks_run_incomplete():
    sc2 = scenario(scenario_id="sc2")
    aus = [audio("au1", scenario_id="sc"), audio("au2", scenario_id="sc2")]
    with pytest.raises(IncompleteRun):
        score_run([scenario(), sc2], aus, [prediction("+49 170 1234 567", audio_id="au1")])


def test_empty_transcript_is_valid_output_not_missing_row():
    sc = scenario()
    res = score_example(sc, prediction(None), audio())  # ok, no slots
    assert res.outcome == "omission"
    assert res.status == "ok"


def test_extra_unsolicited_slot_flags_extra_output():
    sc = scenario()
    pred = prediction(
        "+49 170 1234 567",
        predicted_slots=[
            {"type": "phone", "value": "+49 170 1234 567"},
            {"type": "email", "value": "x@example.com"},
        ],
    )
    res = score_example(sc, pred, audio())
    assert res.outcome == "correct"
    assert res.extra_output is True


def test_duplicate_target_slots_flag_extra_output():
    pred = prediction(
        "+49 170 1234 567",
        predicted_slots=[
            {"type": "phone", "value": "+49 170 1234 567"},
            {"type": "phone", "value": "+49 170 1234 000"},
        ],
    )
    res = score_example(scenario(), pred, audio())
    assert res.extra_output is True


def test_agent_state_file_is_the_evidence():
    sc = scenario()
    au = audio()
    state = {"schema_version": "0.2", "session_id": "s1", "requested_type": "phone",
             "final_slots": [{"type": "phone", "value": "0170 1234567"}]}
    p = Path(__file__).parent / "_agent_state.json"
    p.write_text(json.dumps(state), encoding="utf-8")
    pred = Prediction.model_validate(
        {
            "run_id": "r1",
            "audio_id": "au",
            "track": "agent_slots",
            "status": "ok",
            "predicted_slots": [],  # spoken words claim nothing
            "observed_final_state_path": str(p),
        }
    )
    res = score_example(sc, pred, au)
    assert res.outcome == "correct"  # state read succeeded with the right value

    # agent said the right thing but never stored it -> failure of persistence
    state_empty = dict(state, final_slots=[])
    p2 = Path(__file__).parent / "_agent_state_empty.json"
    p2.write_text(json.dumps(state_empty), encoding="utf-8")
    pred2 = Prediction.model_validate(
        {
            "run_id": "r1",
            "audio_id": "au",
            "track": "agent_slots",
            "status": "ok",
            "predicted_slots": [{"type": "phone", "value": "+491701234567"}],
            "observed_final_state_path": str(p2),
        }
    )
    res2 = score_example(sc, pred2, au)
    assert res2.outcome == "omission"  # nothing persisted
    p.unlink()
    p2.unlink()


def test_missing_state_file_is_integrity_error():
    sc = scenario()
    pred = Prediction.model_validate(
        {
            "run_id": "r1",
            "audio_id": "au",
            "track": "agent_slots",
            "status": "ok",
            "predicted_slots": [],
            "observed_final_state_path": "does/not/exist.json",
        }
    )
    with pytest.raises(RunIntegrityError):
        score_example(sc, pred, audio())


# --- literal vs canonical separation -----------------------------------------------


def test_literal_and_canonical_reported_separately():
    sc = scenario()
    # presentation-formatted but correct value: literal differs, canonical equal
    res = score_example(sc, prediction("0170 1234 567"), audio())
    assert res.literal_correct is False
    assert res.canonical_correct is True
    assert literal_form("+491701234567") == "+491701234567"


# --- statistics --------------------------------------------------------------------


def _synth_results(n_per_cell: int = 5) -> list:
    import types

    out = []
    i = 0
    for locale in ("de-DE", "fr-FR"):
        for entity in ("person_name", "phone", "email", "calendar_value", "postal_address", "reference_code"):
            for k in range(n_per_cell):
                for cond in ("clean", "telephone"):
                    correct = k % 2 == 0 or cond == "clean"
                    r = types.SimpleNamespace(
                        audio_id=f"a{i}", scenario_id=f"s{locale}-{entity}-{k}", run_id="r",
                        locale=locale, entity_type=entity, condition=cond, split="test",
                        difficulty_tags=["direct"], status="ok",
                        outcome="correct" if correct else "substitution",
                        literal_correct=True,
                        canonical_correct=correct, correct=correct,
                        extra_output=False, stale_value=False, is_correction_case=False,
                        predicted_value=None, gold_literal="", predicted_slot_types=[],
                        error_type=None,
                    )
                    out.append(r)
                    i += 1
    return out


def test_bootstrap_same_seed_same_result():
    results = _synth_results()
    a = bootstrap_ci(results, seed=7)
    b = bootstrap_ci(results, seed=7)
    assert a["ci95"] == b["ci95"]
    bootstrap_ci(results, seed=8)
    assert a["ci95"] is not None


def test_bootstrap_paired_uses_same_clusters():
    results_a = _synth_results()
    results_b = [r for r in results_a]
    d = bootstrap_paired_difference(results_a, results_b, seed=7)
    assert d["point_difference"] == 0.0
    assert d["ci95"] == [0.0, 0.0]


def test_duplicate_variants_do_not_increase_independent_n():
    import types

    def make(dup: int):
        rows = []
        for k in range(3):
            for d in range(dup):
                rows.append(
                    types.SimpleNamespace(
                        audio_id=f"a{k}-{d}", scenario_id=f"s{k}", run_id="r", locale="de-DE",
                        entity_type="phone", condition="clean", split="test",
                        difficulty_tags=["direct"], status="ok",
                        outcome="correct" if k > 0 else "substitution", correct=k > 0,
                        literal_correct=k > 0, canonical_correct=k > 0, extra_output=False,
                        stale_value=False, is_correction_case=False, predicted_value=None,
                        gold_literal="", predicted_slot_types=[], error_type=None,
                    )
                )
        return rows

    ci1 = bootstrap_ci(make(1), seed=3)
    ci4 = bootstrap_ci(make(4), seed=3)
    # same 3 scenarios resampled: identical clusters regardless of acoustic dups
    assert ci1["ci95"] == ci4["ci95"]
    assert ci1["point"] == ci4["point"]

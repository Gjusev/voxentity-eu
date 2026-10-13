"""Adversarial contract tests: IDs, paths, types, duplicates, gold isolation."""

from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from voxentity_eu.contracts import (
    AudioRecord,
    CalendarValue,
    PostalAddressValue,
    Prediction,
    PreviousMention,
    RightsEntry,
    RunManifest,
    Scenario,
    check_references,
    check_unique_ids,
    dumps_strict,
    read_json,
    read_jsonl,
    validate_measured_evidence,
    validate_predictions_against_audio,
)

EXAMPLES = Path(__file__).resolve().parents[2] / "examples"


def make_scenario(**over) -> dict:
    base = {
        "schema_version": "0.2",
        "scenario_id": "sc-1",
        "split": "dev",
        "locale": "de-DE",
        "entity_type": "phone",
        "template_family": "de_phone_direct_dev",
        "difficulty_tags": ["direct"],
        "written_text": "Meine Nummer ist +49 170 1234567.",
        "synthesis_text": "Meine Nummer ist plus neunundvierzig, eins sieben null, eins zwei drei vier fünf sechs sieben.",
        "entities": [
            {
                "entity_id": "target-1",
                "type": "phone",
                "canonical_value": "+491701234567",
                "accepted_variants": [],
                "mention_text": "+49 170 1234567",
                "target": True,
            }
        ],
        "previous_mentions": [],
        "seed": 1,
    }
    base.update(over)
    return base


def make_audio(**over) -> dict:
    base = {
        "audio_id": "au-1",
        "scenario_id": "sc-1",
        "corpus": "synthetic",
        "condition": "clean",
        "path": "audio/synthetic/clean/au-1.wav",
        "sha256": "a" * 64,
        "sample_rate_hz": 16000,
        "channels": 1,
        "num_samples": 16000,
        "duration_seconds": 1.0,
        "qa_status": "pending_review",
    }
    base.update(over)
    return base


# --- Scenario ---------------------------------------------------------------


def test_design_example_scenario_parses():
    sc = read_json(EXAMPLES / "scenario.json", Scenario)
    assert sc.entities[0].canonical_value == "AB-75"
    assert sc.entities[0].case_sensitive is True  # reference_code default


def test_design_example_predictions_parse_and_release_rejects():
    preds = read_jsonl(EXAMPLES / "predictions.jsonl", Prediction)
    assert len(preds) == 2
    with pytest.raises(ValueError, match="observed_final_state_path"):
        validate_measured_evidence(list(preds))


def test_rejects_bad_id_chars():
    with pytest.raises(ValidationError):
        Scenario.model_validate(make_scenario(scenario_id="SC/1"))


def test_rejects_multiple_targets():
    with pytest.raises(ValidationError, match="exactly one target"):
        Scenario.model_validate(
            make_scenario(
                entities=[
                    {
                        "entity_id": "target-1",
                        "type": "phone",
                        "canonical_value": "+491701234567",
                        "mention_text": "+49 170 1234567",
                        "target": True,
                    },
                    {
                        "entity_id": "target-2",
                        "type": "phone",
                        "canonical_value": "+491709998887",
                        "mention_text": "+49 170 9998887",
                        "target": True,
                    },
                ]
            )
        )


def test_correlation_requires_previous_mention():
    with pytest.raises(ValidationError, match="previous_mentions"):
        Scenario.model_validate(make_scenario(difficulty_tags=["correction"]))


def test_calendar_must_use_object():
    with pytest.raises(ValidationError, match="calendar_value requires"):
        Scenario.model_validate(
            make_scenario(
                entity_type="calendar_value",
                difficulty_tags=["direct"],
                entities=[
                    {
                        "entity_id": "target-1",
                        "type": "calendar_value",
                        "canonical_value": "3. Mai",
                        "mention_text": "dritten Mai",
                        "target": True,
                    }
                ],
            )
        )


def test_calendar_object_valid_and_year_optional():
    Scenario.model_validate(
        make_scenario(
            entity_type="calendar_value",
            difficulty_tags=["direct"],
            entities=[
                {
                    "entity_id": "target-1",
                    "type": "calendar_value",
                    "canonical_value": {"day": 3, "month": 5},
                    "mention_text": "dritten Mai",
                    "target": True,
                }
            ],
        )
    )
    with pytest.raises(ValidationError):
        CalendarValue(day=3, month=5, year=1)  # year out of allowed range


def test_postal_address_object_required():
    with pytest.raises(ValidationError, match="postal_address requires"):
        Scenario.model_validate(
            make_scenario(
                entity_type="postal_address",
                entities=[
                    {
                        "entity_id": "target-1",
                        "type": "postal_address",
                        "canonical_value": "Eichenweg 4",
                        "mention_text": "Eichenweg 4",
                        "target": True,
                    }
                ],
            )
        )
    PostalAddressValue(street="Eichenweg", house_number="4", postal_code="10115", locality="Berlin")


def test_case_sensitive_only_for_reference_code():
    with pytest.raises(ValidationError, match="case_sensitive"):
        Scenario.model_validate(
            make_scenario(
                entities=[
                    {
                        "entity_id": "target-1",
                        "type": "phone",
                        "canonical_value": "+491701234567",
                        "mention_text": "+49 170 1234567",
                        "target": True,
                        "case_sensitive": True,
                    }
                ]
            )
        )


def test_schema_version_mismatch_rejected():
    with pytest.raises(ValidationError, match="schema_version"):
        Scenario.model_validate(make_scenario(schema_version="0.1"))


# --- Audio ------------------------------------------------------------------


def test_rejects_path_escape():
    for bad in ("../escape.wav", "audio/../../x.wav", "C:\\abs\\path.wav", "/abs.wav"):
        with pytest.raises(ValidationError, match="path"):
            AudioRecord.model_validate(make_audio(path=bad))


def test_telephone_requires_parent_and_transform():
    with pytest.raises(ValidationError, match="parent_audio_id"):
        AudioRecord.model_validate(make_audio(condition="telephone"))
    a = AudioRecord.model_validate(
        make_audio(condition="telephone", parent_audio_id="au-0", transform_id="tr-1", sample_rate_hz=8000)
    )
    assert a.parent_audio_id == "au-0"


def test_clean_must_not_have_parent():
    with pytest.raises(ValidationError, match="clean"):
        AudioRecord.model_validate(make_audio(parent_audio_id="au-0"))


def test_human_control_requires_external_refs():
    with pytest.raises(ValidationError, match="human_control"):
        AudioRecord.model_validate(
            make_audio(
                corpus="human_control",
                scenario_id=None,
                source_id="S04",
            )
        )
    ok = AudioRecord.model_validate(
        make_audio(
            corpus="human_control",
            scenario_id=None,
            source_id="S04",
            external_row_id="row-1",
            external_split="test",
            transcript="ein Beispielsatz",
        )
    )
    assert ok.transcript == "ein Beispielsatz"


def test_rejects_stereo():
    with pytest.raises(ValidationError, match="mono"):
        AudioRecord.model_validate(make_audio(channels=2))


def test_rejects_nan_duration():
    raw = make_audio(duration_seconds=1.0)
    raw["duration_seconds"] = float("nan")
    with pytest.raises(ValidationError):
        AudioRecord.model_validate(raw)


# --- cross-record integrity ---------------------------------------------------


def test_duplicate_audio_ids_rejected():
    rows = [AudioRecord.model_validate(make_audio()), AudioRecord.model_validate(make_audio(audio_id="au-2"))]
    check_unique_ids(rows, "audio_id")  # fine
    rows2 = [AudioRecord.model_validate(make_audio()), AudioRecord.model_validate(make_audio())]
    with pytest.raises(ValueError, match="duplicate"):
        check_unique_ids(rows2, "audio_id")


def test_broken_reference_rejected():
    rows = [AudioRecord.model_validate(make_audio(audio_id="au-1", scenario_id="sc-missing"))]
    with pytest.raises(ValueError, match="unknown scenario_id"):
        check_references(rows, scenario_ids={"sc-1"})
    # telephone audio pointing at a missing parent
    rows2 = [
        AudioRecord.model_validate(make_audio(audio_id="au-1")),
        AudioRecord.model_validate(
            make_audio(audio_id="au-2", condition="telephone", parent_audio_id="au-9", transform_id="tr-1", sample_rate_hz=8000)
        ),
    ]
    with pytest.raises(ValueError, match="unknown parent"):
        check_references(rows2, scenario_ids={"sc-1"})


def test_unknown_or_duplicate_prediction_rows_rejected():
    preds = [
        Prediction.model_validate(
            {
                "run_id": "r1",
                "audio_id": "au-1",
                "track": "asr",
                "status": "ok",
                "transcript": "hallo",
            }
        )
    ]
    validate_predictions_against_audio(list(preds), {"au-1"})
    dup = list(preds) + list(preds)
    with pytest.raises(ValueError, match="duplicate"):
        validate_predictions_against_audio(dup, {"au-1"})
    with pytest.raises(ValueError, match="unknown audio_id"):
        validate_predictions_against_audio(list(preds), {"au-other"})


def test_timeout_is_valid_failed_row():
    p = Prediction.model_validate(
        {
            "run_id": "r1",
            "audio_id": "au-1",
            "track": "asr",
            "status": "timeout",
            "transcript": None,
            "error_type": "timeout",
        }
    )
    assert p.status == "timeout"


def test_error_requires_error_type():
    with pytest.raises(ValidationError, match="error_type"):
        Prediction.model_validate(
            {"run_id": "r1", "audio_id": "au-1", "track": "asr", "status": "error", "transcript": None}
        )


# --- run manifest -------------------------------------------------------------


def make_manifest(**over) -> dict:
    base = {
        "run_id": "r1",
        "schema_version": "0.2",
        "suite_version": "0.1.0",
        "dataset_hash": "b" * 64,
        "eligible_audio_ids_hash": "c" * 64,
        "code_commit": "deadbeef",
        "dependency_lock_hash": "d" * 64,
        "model_id": "openai/whisper-large-v3-turbo",
        "model_revision": "41f01f3fe87f28c78e2fbf8b568835947dd65ed9",
        "backend": "transformers",
        "device": "cuda:0",
        "precision": "fp16",
        "decoding_config": {"language": "de"},
        "prompt_hash": None,
        "normalizer_version": "n1",
        "seed": 0,
        "input_audio_policy": "gold-free inputs directory",
        "track": "asr",
        "expected_count": 10,
        "completed_count": 10,
        "failed_count": 0,
        "access_mode": "local",
        "charge_limit": 0.0,
    }
    base.update(over)
    return base


def test_manifest_incomplete_flag_consistency():
    RunManifest.model_validate(make_manifest())
    with pytest.raises(ValidationError, match="incomplete"):
        RunManifest.model_validate(make_manifest(completed_count=8))
    RunManifest.model_validate(make_manifest(completed_count=8, incomplete=True))


def test_manifest_counts_cannot_exceed_expected():
    with pytest.raises(ValidationError, match="exceed"):
        RunManifest.model_validate(make_manifest(completed_count=6, failed_count=6))


# --- strict json --------------------------------------------------------------


def test_dumps_strict_rejects_nan():
    with pytest.raises(ValueError):
        dumps_strict({"x": float("nan")})


def test_previous_mention_shape():
    PreviousMention(type="phone", value="+491701234567")
    with pytest.raises(ValidationError):
        PreviousMention(type="postal_address", value="kein Objekt")


def test_rights_entry_enum():
    RightsEntry(
        source_id="S04",
        url="https://huggingface.co/datasets/google/fleurs",
        revision="70bb2e84b976b7e960aa89f1c648e09c59f894dd",
        declared_license="cc-by-4.0",
        license_url="https://creativecommons.org/licenses/by/4.0/",
        rights_holder="Google",
        redistribution="allowed",
        review_status="verified",
    )
    with pytest.raises(ValidationError):
        RightsEntry(
            source_id="S04",
            url="x",
            revision="r",
            declared_license="?",
            license_url="x",
            rights_holder="?",
            redistribution="maybe",
            review_status="verified",
        )

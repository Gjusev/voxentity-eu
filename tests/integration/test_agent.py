"""P6 integration: reference agent persistence semantics (docs/10 matrix)."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from voxentity_eu.adapters.agent import AgentStore, ReferenceAgent
from voxentity_eu.adapters.base import AsrResult
from voxentity_eu.scoring.match import score_example


@dataclass
class FakeAsr:
    transcripts: dict[str, str] = field(default_factory=dict)

    name = "fake"

    def load(self) -> None: ...

    def transcribe(self, audio_path: str, locale: str, **config):
        return AsrResult(status="ok", transcript=self.transcripts.get(audio_path, ""))


def make_scenario_dict(**over):
    base = {
        "schema_version": "0.2",
        "scenario_id": "sc-ag",
        "split": "test",
        "locale": "de-DE",
        "entity_type": "reference_code",
        "template_family": "f",
        "difficulty_tags": ["correction"],
        "written_text": "Die Referenz ist XW-9690, pardon, XW-9609.",
        "synthesis_text": "Die Referenz ist iks weh Bindestrich sechsundneunzig neunzig, pardon, iks weh Bindestrich sechsundneunzig null neun.",
        "entities": [
            {
                "entity_id": "target-1",
                "type": "reference_code",
                "canonical_value": "XW-9609",
                "mention_text": "XW-9609",
                "target": True,
            }
        ],
        "previous_mentions": [{"type": "reference_code", "value": "XW-9690"}],
        "seed": 1,
    }
    base.update(over)
    return base


def test_agent_persists_final_corrected_value(tmp_path: Path):
    from voxentity_eu.contracts import AudioRecord, Prediction, Scenario

    sc = Scenario.model_validate(make_scenario_dict())
    store = AgentStore(tmp_path / "store")
    agent = ReferenceAgent(
        FakeAsr({"a.wav": "Die Referenz ist iks weh Bindestrich sechsundneunzig null neun."}), store
    )
    result = agent.evaluate("a.wav", "reference_code", "de-DE", "s1")
    audio = AudioRecord.model_validate(
        {
            "audio_id": "au", "scenario_id": sc.scenario_id, "corpus": "synthetic",
            "condition": "clean", "path": "x.wav", "sha256": "a" * 64,
            "sample_rate_hz": 16000, "num_samples": 1600, "duration_seconds": 0.1,
            "qa_status": "accepted",
        }
    )
    pred = Prediction.model_validate(
        {
            "run_id": "r", "audio_id": "au", "track": "agent_slots", "status": "ok",
            "transcript": result["transcript"], "predicted_slots": [],
            "observed_final_state_path": result["observed_final_state_path"],
        }
    )
    r = score_example(sc, pred, audio)
    assert r.outcome == "correct", (r.predicted_value, r.gold_literal)
    assert r.stale_value is False


def test_agent_stale_value_negative_control(tmp_path: Path):
    """ASR returns only the superseded mention: the store keeps a stale value."""

    from voxentity_eu.contracts import AudioRecord, Prediction, Scenario

    sc = Scenario.model_validate(make_scenario_dict())
    store = AgentStore(tmp_path / "store")
    agent = ReferenceAgent(
        FakeAsr({"a.wav": "Die Referenz ist iks weh Bindestrich sechsundneunzig neunzig."}), store
    )
    result = agent.evaluate("a.wav", "reference_code", "de-DE", "s1")
    audio = AudioRecord.model_validate(
        {
            "audio_id": "au", "scenario_id": sc.scenario_id, "corpus": "synthetic",
            "condition": "clean", "path": "x.wav", "sha256": "a" * 64,
            "sample_rate_hz": 16000, "num_samples": 1600, "duration_seconds": 0.1,
            "qa_status": "accepted",
        }
    )
    pred = Prediction.model_validate(
        {
            "run_id": "r", "audio_id": "au", "track": "agent_slots", "status": "ok",
            "transcript": "I said XW-9609",  # words claim the right thing...
            "predicted_slots": [{"type": "reference_code", "value": "XW-9609"}],
            "observed_final_state_path": result["observed_final_state_path"],  # ...store says otherwise
        }
    )
    r = score_example(sc, pred, audio)
    assert r.outcome == "substitution"
    assert r.stale_value is True  # ...but the store kept the stale value


def test_agent_says_value_but_stores_nothing(tmp_path: Path):
    from voxentity_eu.contracts import AudioRecord, Prediction, Scenario

    sc = Scenario.model_validate(make_scenario_dict(difficulty_tags=["direct"], previous_mentions=[]))
    store = AgentStore(tmp_path / "store")

    # simulate: extraction returned nothing; nothing was stored
    store.create_session("s1", "reference_code")
    state_path = store.finalize("s1")
    audio = AudioRecord.model_validate(
        {
            "audio_id": "au", "scenario_id": sc.scenario_id, "corpus": "synthetic",
            "condition": "clean", "path": "x.wav", "sha256": "a" * 64,
            "sample_rate_hz": 16000, "num_samples": 1600, "duration_seconds": 0.1,
            "qa_status": "accepted",
        }
    )
    pred = Prediction.model_validate(
        {
            "run_id": "r", "audio_id": "au", "track": "agent_slots", "status": "ok",
            "transcript": "Die Referenz ist XW-9609.",
            "predicted_slots": [],
            "observed_final_state_path": str(state_path),
        }
    )
    r = score_example(sc, pred, audio)
    assert r.outcome == "omission"  # speaking is not persisting


def test_store_slot_replaces_previous_value(tmp_path: Path):
    store = AgentStore(tmp_path / "store")
    store.create_session("s", "phone")
    e1 = store.store_slot("s", "phone", "+491701111111")
    assert e1["replaces"] is None
    e2 = store.store_slot("s", "phone", "+491702222222")
    assert e2["replaces"] == "+491701111111"
    path = store.finalize("s")
    state = json.loads(path.read_text(encoding="utf-8"))
    assert state["final_slots"] == [{"type": "phone", "value": "+491702222222"}]
    # strict reset: the session cannot be reused
    try:
        store.store_slot("s", "phone", "+491703333333")
        raise AssertionError("session reuse must fail")
    except ValueError:
        pass


def test_missing_state_file_is_integrity_error():
    from voxentity_eu.contracts import AudioRecord, Prediction, Scenario
    from voxentity_eu.scoring.match import RunIntegrityError

    sc = Scenario.model_validate(make_scenario_dict())
    audio = AudioRecord.model_validate(
        {
            "audio_id": "au", "scenario_id": sc.scenario_id, "corpus": "synthetic",
            "condition": "clean", "path": "x.wav", "sha256": "a" * 64,
            "sample_rate_hz": 16000, "num_samples": 1600, "duration_seconds": 0.1,
            "qa_status": "accepted",
        }
    )
    pred = Prediction.model_validate(
        {
            "run_id": "r", "audio_id": "au", "track": "agent_slots", "status": "ok",
            "transcript": "x", "predicted_slots": [],
            "observed_final_state_path": "nowhere.json",
        }
    )
    import pytest

    with pytest.raises(RunIntegrityError):
        score_example(sc, pred, audio)

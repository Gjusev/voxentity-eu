"""`voxentity compare` must work on the scored JSON files that `score` writes."""

import json

from voxentity_eu.scoring.aggregate import cli_compare


def _row(sid, cond, outcome):
    return {
        "audio_id": sid, "scenario_id": sid, "run_id": "r", "locale": "de-DE", "entity_type": "phone",
        "condition": cond, "split": "test", "difficulty_tags": [], "status": "ok", "outcome": outcome,
        "literal_correct": False, "canonical_correct": outcome == "correct", "extra_output": False,
        "stale_value": False, "is_correction_case": False, "predicted_value": None, "gold_literal": "x",
        "predicted_slot_types": [], "error_type": None,
    }


def test_compare_from_json_files(tmp_path):
    a = {"run_id": "a", "results": [_row("s1", "clean", "correct"), _row("s1", "telephone", "omission")]}
    b = {"run_id": "b", "results": [_row("s1", "clean", "omission"), _row("s1", "telephone", "omission")]}
    pa, pb = tmp_path / "a.json", tmp_path / "b.json"
    pa.write_text(json.dumps(a)), pb.write_text(json.dumps(b))
    out = cli_compare(str(pa), str(pb), str(tmp_path / "c.json"))
    assert out["comparison"]["n_shared"] == 2  # keyed by (scenario, condition), not collapsed
    assert out["comparison"]["a_better"] == 1
    assert out["paired_difference"]["point_difference"] == 0.5

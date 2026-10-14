"""Multi-turn outcome rules: persistence failures are separated from perception errors."""

import pytest

from voxentity_eu.ext import multiturn as mt


@pytest.fixture(scope="module")
def cases():
    return {c.kind: c for c in mt.build_cases() if c.entity_type == "phone" and c.locale == "de-DE"}


def _row(case, t1, t2, final):
    return {"case_id": case.case_id, "condition": "clean", "turn_values": [t1, t2], "final_value": final, "transcripts": []}


def _outcome(case, t1, t2, final):
    return mt.score_rows([case], [_row(case, t1, t2, final)])[0]["outcome"]


def test_outcomes(cases):
    corr, conf, rep = cases["correction"], cases["confirmation"], cases["repeat"]
    first, final = corr.first.canonical_value, corr.final.canonical_value
    assert _outcome(corr, first, final, final) == "correct"
    assert _outcome(corr, first, None, first) == "stale"  # correction never reached the state
    a = conf.first.canonical_value
    assert _outcome(conf, a, None, a) == "correct"
    assert _outcome(conf, "+491111", None, "+491111") == "wrong_value"  # misheard turn 1, untouched: not spurious
    r = rep.first.canonical_value
    assert _outcome(rep, r, "+492222", "+492222") == "spurious_change"  # right value overwritten
    assert _outcome(rep, None, None, None) == "omission"


def test_gold_text_ceiling_is_perfect():
    cases = mt.build_cases()
    import tempfile
    from pathlib import Path

    tx = {t.scenario_id: t.written_text for c in cases for t in c.turns}
    rows = mt.score_rows(cases, mt.run_agent(cases, tx, Path(tempfile.mkdtemp()), "clean"))
    assert all(r["correct"] for r in rows)

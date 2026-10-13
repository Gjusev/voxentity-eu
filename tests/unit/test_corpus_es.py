"""ES extension suite: structure, split separation, and the frozen main corpus.

The ES suite is separate (docs/09 §Extensiones): 6 cells x 15 cases, its own
manifest under data/ext/es, and the DE/FR corpus must stay byte-identical.
"""

import json
from collections import Counter
from pathlib import Path

import pytest

from voxentity_eu.corpus import templates
from voxentity_eu.corpus.generate import build_corpus, build_corpus_es, corpus_summary
from voxentity_eu.corpus.validate import validate_corpus
from voxentity_eu.scoring.normalize import canonical_form

MAIN_CORPUS_HASH = "b7513367297700f3cd89df1e781af5a636f44beec320defbbd64234e2e1dde4b"


@pytest.fixture(scope="module")
def es() -> list:
    return build_corpus_es()


def test_es_suite_structure(es):
    report = validate_corpus(es)
    assert report["errors"] == [], report["errors"]
    assert len(es) == 90
    summary = corpus_summary(es)
    assert summary["splits"] == {"dev": 30, "test": 60}
    assert set(summary["per_cell"].values()) == {15}
    assert set(summary["per_cell"]) == {f"es-ES|{e}" for e in (
        "person_name", "phone", "email", "calendar_value", "postal_address", "reference_code"
    )}


def test_es_es_only(es):
    assert {s.locale for s in es} == {"es-ES"}
    assert all(s.scenario_id.split("-")[1] == "es" for s in es)


def test_es_difficulty_mix_per_cell(es):
    for entity in ("person_name", "phone", "email", "calendar_value", "postal_address", "reference_code"):
        cell = [s for s in es if s.entity_type == entity]
        buckets = Counter()
        for s in cell:
            tags = set(s.difficulty_tags)
            if tags == {"direct"}:
                buckets["direct"] += 1
            elif "correction" in tags:
                buckets["correction"] += 1
            elif tags & {"segmented", "spelling"}:
                buckets["segmented"] += 1
            else:
                buckets["tricky"] += 1
        assert dict(buckets) == {"direct": 5, "tricky": 4, "segmented": 3, "correction": 3}


def test_es_no_frame_duplicated_across_pools(es):
    """A frame string may not appear in two (difficulty, split) pools —
    regression for the audit finding that hit the FR pools."""

    pools: dict[tuple[str, str, str], set[str]] = {}
    for (locale, entity), per_difficulty in templates.FRAMES.items():
        for _difficulty, frames in per_difficulty.items():
            for i, frame in enumerate(frames):
                split = "dev" if i % 2 == 0 else "test"
                pools.setdefault((locale, entity, split), set()).add(frame)
    for (locale, entity, split), frames in pools.items():
        other = "test" if split == "dev" else "dev"
        overlap = frames & pools.get((locale, entity, other), set())
        assert not overlap, (locale, entity, split, overlap)


def test_es_values_disjoint_across_splits(es):
    seen: dict[tuple, tuple[str, str]] = {}
    for s in es:
        for e in s.entities:
            key = (s.locale, s.entity_type, repr(canonical_form(e.canonical_value, s.entity_type, s.locale)))
            if key in seen and seen[key][1] != s.split:
                raise AssertionError(f"leak: {s.scenario_id} vs {seen[key][0]}")
            seen.setdefault(key, (s.scenario_id, s.split))


def test_es_correction_semantics(es):
    for s in es:
        if "correction" in s.difficulty_tags:
            assert s.previous_mentions, s.scenario_id
            assert s.entities[0].canonical_value != s.previous_mentions[-1].value
        else:
            assert not s.previous_mentions


def test_main_corpus_hash_is_frozen():
    summary = corpus_summary(build_corpus())
    assert summary["corpus_hash"] == MAIN_CORPUS_HASH


def test_main_gold_bytes_unchanged():
    """The committed de/fr scenarios.jsonl must equal a fresh build."""

    repo_root = Path(__file__).resolve().parents[2]
    committed = repo_root / "data/generated/gold/scenarios.jsonl"
    if not committed.exists():  # fresh clone without generated data
        pytest.skip("committed main gold not present")
    from voxentity_eu.contracts import Scenario

    fresh = sorted(build_corpus(), key=lambda s: s.scenario_id)
    committed_rows = [
        Scenario.model_validate(json.loads(line))
        for line in committed.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert [s.scenario_id for s in fresh] == [s.scenario_id for s in committed_rows]
    for a, b in zip(fresh, committed_rows, strict=False):
        assert a == b, a.scenario_id


def test_es_build_is_deterministic():
    a = [s.model_dump_json() for s in sorted(build_corpus_es(), key=lambda s: s.scenario_id)]
    b = [s.model_dump_json() for s in sorted(build_corpus_es(), key=lambda s: s.scenario_id)]
    assert a == b

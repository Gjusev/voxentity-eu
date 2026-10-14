"""P2 corpus gates: counts, split separation, correction semantics, export isolation."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from voxentity_eu.contracts import AudioRecord, Scenario
from voxentity_eu.corpus import pools, verbalize
from voxentity_eu.corpus.export_inputs import export_inputs
from voxentity_eu.corpus.generate import build_corpus, corpus_summary
from voxentity_eu.corpus.validate import validate_corpus


@pytest.fixture(scope="module")
def corpus() -> list[Scenario]:
    return build_corpus()


def test_counts_exact(corpus):
    report = validate_corpus(corpus)
    assert report["errors"] == [], report["errors"]
    assert len(corpus) == 180


def test_rebuild_is_byte_identical():
    a = [s.model_dump_json() for s in sorted(build_corpus(), key=lambda s: s.scenario_id)]
    b = [s.model_dump_json() for s in sorted(build_corpus(), key=lambda s: s.scenario_id)]
    assert a == b


def test_no_family_in_both_splits(corpus):
    fam_splits: dict[str, set[str]] = {}
    for s in corpus:
        fam_splits.setdefault(s.template_family, set()).add(s.split)
    assert all(len(v) == 1 for v in fam_splits.values())


def test_no_equivalent_values_across_splits(corpus):
    from voxentity_eu.scoring.normalize import canonical_form

    seen: dict[tuple, tuple[str, str]] = {}
    for s in corpus:
        for e in s.entities:
            key = (s.locale, s.entity_type, repr(canonical_form(e.canonical_value, s.entity_type, s.locale)))
            if key in seen and seen[key][0].split != s.split:
                raise AssertionError(f"leak: {s.scenario_id} vs {seen[key][0].scenario_id}")
            seen.setdefault(key, (s.scenario_id, s.split))


def test_correction_semantics(corpus):
    for s in corpus:
        if "correction" in s.difficulty_tags:
            assert s.previous_mentions, s.scenario_id
            final = s.entities[0].canonical_value
            prev = s.previous_mentions[-1].value
            assert final != prev
            # the corrected (final) value is what written_text shows as the answer
            assert s.entities[0].mention_text in s.written_text
        else:
            assert not s.previous_mentions


def test_voice_assignment_alternates_within_cell_regardless_of_difficulty():
    from voxentity_eu.audio.synthesize import CELL_ORDER, voice_for

    for locale, entity in CELL_ORDER:
        voices = [voice_for("ignored", locale, entity, i) for i in range(15)]
        # alternation, never keyed on difficulty (idx blocks map to difficulties)
        assert voices.count(voices[0]) in (7, 8)
        assert all(v in ("serena", "dylan") for v in voices)


def test_verbalization_roundtrips_for_reference_blocks():
    # the reference extractor must be able to invert these (checked in adapters tests)
    spoken = verbalize.verbalize_reference_code("AB-075", "de-DE", spell=False)
    assert "siebenundsiebzig" not in spoken  # leading zero keeps digits separate
    spoken_fr = verbalize.verbalize_phone("+33612345678", "fr-FR")
    assert "plus trois trois" in spoken_fr


def test_year_words_are_natural():
    assert verbalize.year_word_de(2026) == "zweitausendsechsundzwanzig"
    assert verbalize.year_word_fr(2028) == "deux mille vingt-huit"
    assert verbalize.year_word_fr(1990) == "mille neuf cent quatre-vingt-dix"


def test_phone_pool_lengths():
    de = pools.phone_pool("de-DE", 5)
    assert all(p.startswith("+49") and len(p) == 13 for p in de)
    fr = pools.phone_pool("fr-FR", 5)
    assert all(p.startswith("+33") and len(p) == 12 for p in fr)
    assert len(set(de)) == 5


def test_export_inputs_is_gold_free(tmp_path: Path, corpus):
    audio = []
    audio_src = tmp_path / "audio"
    audio_src.mkdir()
    import numpy as np
    import soundfile as sf

    for s in corpus[:6]:
        aid = f"{s.scenario_id}-clean"
        rel = f"synthetic/clean/{aid}.wav"
        path = audio_src / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        sf.write(path, np.zeros(1600, dtype="int16"), 16000, subtype="PCM_16")
        audio.append(
            AudioRecord.model_validate(
                {
                    "audio_id": aid,
                    "scenario_id": s.scenario_id,
                    "corpus": "synthetic",
                    "condition": "clean",
                    "path": rel,
                    "sha256": "a" * 64,
                    "sample_rate_hz": 16000,
                    "num_samples": 1600,
                    "duration_seconds": 0.1,
                    "qa_status": "accepted",
                }
            )
        )
    out = tmp_path / "inputs"
    result = export_inputs(corpus, audio, audio_src, out)
    assert result["exported"] == 6
    assert result["problems"] == []
    # no gold in the exported rows
    rows = [json.loads(line) for line in (out / "inputs.jsonl").read_text(encoding="utf-8").splitlines()]
    banned = {"written_text", "synthesis_text", "canonical_value", "difficulty_tags", "entities"}
    for r in rows:
        assert banned.isdisjoint(r)
        assert set(r) == {"input_id", "audio_relpath", "sha256", "locale", "corpus", "condition", "requested_slot_type"}
    # filenames are opaque hashes, not scenario/value derivations
    import re as _re

    assert all(_re.fullmatch(r"[0-9a-f]{16}", f.stem) for f in (out / "audio").glob("*.wav"))


def test_export_rejects_answer_encoding_filenames(tmp_path: Path, corpus):
    import numpy as np
    import soundfile as sf

    s = next(x for x in corpus if x.entity_type == "reference_code")
    audio_src = tmp_path / "audio"
    answer = str(s.entities[0].canonical_value).replace("-", " ")  # e.g. "AB 0755"
    rel = f"synthetic/clean/{answer}.wav"
    path = audio_src / rel
    path.parent.mkdir(parents=True)
    sf.write(path, np.zeros(1600, dtype="int16"), 16000, subtype="PCM_16")
    audio = [
        AudioRecord.model_validate(
            {
                "audio_id": "bad-1",
                "scenario_id": s.scenario_id,
                "corpus": "synthetic",
                "condition": "clean",
                "path": rel,
                "sha256": "a" * 64,
                "sample_rate_hz": 16000,
                "num_samples": 1600,
                "duration_seconds": 0.1,
                "qa_status": "accepted",
            }
        )
    ]
    result = export_inputs(corpus, audio, audio_src, tmp_path / "out2")
    assert result["exported"] == 0
    assert any("encode the answer" in p for p in result["problems"])


def test_scenario_ids_are_opaque_to_difficulty_of_answers(corpus):
    # ids may describe type/difficulty (public) but must never contain the value
    from voxentity_eu.scoring.normalize import literal_form

    for s in corpus:
        val = literal_form(s.entities[0].canonical_value)
        assert val.split(" ")[0][:6].lower() not in s.scenario_id


def test_export_order_does_not_leak_audio_id_structure(tmp_path: Path, corpus):
    """Rows/files are ordered by opaque input_id, never by audio_id (which
    encodes split+difficulty). Regression test for the audit finding."""
    import numpy as np
    import soundfile as sf

    audio_src = tmp_path / "audio"
    audio = []
    for s in corpus[:8]:
        rel = f"synthetic/clean/{s.scenario_id}.wav"
        p = audio_src / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        sf.write(p, np.zeros(1600, dtype="int16"), 16000, subtype="PCM_16")
        audio.append(
            AudioRecord.model_validate(
                {
                    "audio_id": s.scenario_id, "scenario_id": s.scenario_id,
                    "corpus": "synthetic", "condition": "clean", "path": rel,
                    "sha256": "a" * 64, "sample_rate_hz": 16000, "num_samples": 1600,
                    "duration_seconds": 0.1, "qa_status": "accepted",
                }
            )
        )
    out = tmp_path / "inputs"
    result = export_inputs(corpus, audio, audio_src, out)
    assert result["exported"] == 8
    rows = [json.loads(line) for line in (out / "inputs.jsonl").read_text(encoding="utf-8").splitlines()]
    ids = [r["input_id"] for r in rows]
    assert ids == sorted(ids), "rows must be ordered by opaque input_id"
    # the sorted order must NOT coincide with audio_id order for this set
    mapping = result["mapping"]
    decrypted = [mapping[i] for i in ids]
    assert decrypted != sorted(decrypted), "opaque order must not reproduce audio_id order"


def test_summary_counts(corpus):
    summary = corpus_summary(corpus)
    assert summary["total_scenarios"] == 180
    assert summary["splits"] == {"dev": 60, "test": 120}
    assert set(summary["per_cell"].values()) == {15}


def test_extension_suite_validation_uses_declared_size():
    from voxentity_eu.corpus.validate import validate_corpus
    from voxentity_eu.ext.codeswitch import build_scenarios

    cs = build_scenarios()
    assert validate_corpus(cs, expected_total=len(cs))["errors"] == []
    assert any("declares" in e for e in validate_corpus(cs[:-1], expected_total=len(cs))["errors"])
    assert validate_corpus(cs)["errors"]  # the strict core layout still rejects a non-core suite

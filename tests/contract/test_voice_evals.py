"""Contract test against the pinned voice-evals checkout (S16).

The integration is optional: when the sibling repository is absent or at a
different commit, the test skips (core works without voice-evals). When
present, exported fixtures must load through the real FixtureCallerVoice.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

VOICE_EVALS_DIR = Path("C:/Code Main/voice-evals")
PINNED_COMMIT = "3f6f9dd6412cbbaf8842405d6444fb2d74b8790e"


def _repo_commit() -> str | None:
    head = VOICE_EVALS_DIR / ".git" / "HEAD"
    if not head.exists():
        return None
    text = head.read_text(encoding="utf-8").strip()
    if text.startswith("ref:"):
        ref = head.parent / text[4:].strip()
        if ref.exists():
            return ref.read_text(encoding="utf-8").strip()
    return text


@pytest.fixture(scope="module")
def fixture_caller_cls():
    commit = _repo_commit()
    if commit != PINNED_COMMIT:
        pytest.skip(f"voice-evals checkout not at pinned commit {PINNED_COMMIT[:8]} (found {commit})")
    sys.path.insert(0, str(VOICE_EVALS_DIR / "src"))
    from voice_evals.probe.voices.fixture import FixtureCallerVoice

    return FixtureCallerVoice


def test_export_fixture_loads_with_real_caller(tmp_path: Path, fixture_caller_cls):
    import asyncio

    from voxentity_eu.adapters.voice_evals_export import export_voice_evals_fixture
    from voxentity_eu.contracts import AudioRecord, Scenario, read_jsonl

    scenarios_path = Path("data/generated/gold/scenarios.jsonl")
    synthesis_path = Path("data/generated/synthesis.jsonl")
    if not scenarios_path.exists() or not synthesis_path.exists():
        pytest.skip("corpus/synthesis not built yet")
    scenarios = list(read_jsonl(scenarios_path, Scenario))
    synthesis = [
        json.loads(line)
        for line in synthesis_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    audio = [
        a
        for a in read_jsonl(Path("data/generated/audio_manifest.jsonl"), AudioRecord)
        if a.condition == "clean" and a.qa_status in ("accepted", "pending_review")
    ][:6]
    audio_root = Path("data/audio")
    if not all((audio_root / a.path).exists() for a in audio):
        pytest.skip("synthesis not complete yet")

    out = tmp_path / "fixture" / "manifest.json"
    result = export_voice_evals_fixture(
        scenarios, audio, audio_root, synthesis, "serena", "clean", out
    )
    assert result["clips"] > 0
    manifest = json.loads(out.read_text(encoding="utf-8"))
    assert manifest["format"]["sample_rate"] == 16000

    caller = fixture_caller_cls(out)
    clip = manifest["clips"][0]

    async def fetch():
        from voice_evals.probe.audio import AudioFormat

        return await caller.synthesize(clip["text"], audio_format=AudioFormat(sample_rate=16000, channels=1, sample_width=2, encoding="pcm_s16le"))

    served = asyncio.run(fetch())
    assert served.samples > 0
    assert served.provenance["engine"] == "fixture"


def test_duplicate_texts_rejected(tmp_path: Path):
    import numpy as np
    import soundfile as sf

    from voxentity_eu.adapters.voice_evals_export import export_voice_evals_fixture
    from voxentity_eu.commands import QualityGateFailed
    from voxentity_eu.contracts import AudioRecord, Scenario

    scenario_dict = {
        "schema_version": "0.2",
        "scenario_id": "dup-1",
        "split": "test",
        "locale": "de-DE",
        "entity_type": "person_name",
        "template_family": "f",
        "difficulty_tags": ["direct"],
        "written_text": "x",
        "synthesis_text": "Identischer diktierter Text.",
        "entities": [
            {"entity_id": "target-1", "type": "person_name", "canonical_value": "Anna",
             "mention_text": "Anna", "target": True}
        ],
        "previous_mentions": [],
        "seed": 1,
    }
    scenarios = [Scenario.model_validate(scenario_dict)]
    audio = []
    audio_root = tmp_path / "audio"
    for i in range(2):
        rel = f"synthetic/clean/dup{i}.wav"
        p = audio_root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        sf.write(p, np.zeros(1600, dtype="int16"), 16000, subtype="PCM_16")
        audio.append(
            AudioRecord.model_validate(
                {
                    "audio_id": f"dup{i}", "scenario_id": "dup-1", "corpus": "synthetic",
                    "condition": "clean", "path": rel, "sha256": "a" * 64,
                    "sample_rate_hz": 16000, "num_samples": 1600,
                    "duration_seconds": 0.1, "qa_status": "accepted",
                    "synthesis_id": "sy-dup-1",
                }
            )
        )
    synthesis = [
        {"synthesis_id": "sy-dup-1", "model_id": "m", "model_revision": "0" * 40,
         "speaker_id": "serena"}
    ]
    with pytest.raises(QualityGateFailed, match="duplicate clip text"):
        export_voice_evals_fixture(
            scenarios, audio, audio_root, synthesis, "serena", "clean",
            tmp_path / "m.json",
        )

"""Voice-coverage suite: the 120 core TEST scenarios re-synthesized with two more voices.

Motivation (coverage analysis on the core corpus): dylan-voiced items scored
about 10 pp higher than serena-voiced ones for BOTH ASR systems, but voices
were assigned per scenario, so voice and scenario are confounded. Here every
test scenario is spoken by vivian AND ryan (Qwen3-TTS CustomVoice speakers
that passed the DE/FR smoke test, data/smoke_tts/report4.json), giving a
voice comparison paired by scenario. Text and gold are the core ones; the core
corpus itself is unchanged.
"""

from __future__ import annotations

import json
from pathlib import Path

from ..contracts import Scenario
from ..corpus.generate import build_corpus
from ..provenance import sha256_text, write_text_atomic

SUITE = "voices"
VOICES = ("vivian", "ryan")


def build_scenarios() -> list[Scenario]:
    out = []
    for s in build_corpus():
        if s.split != "test":
            continue
        for v in VOICES:
            out.append(s.model_copy(update={"scenario_id": f"vx-{v}-{s.scenario_id}"}))
    return out


def core_id(vx_id: str) -> tuple[str, str]:
    """vx-<voice>-<core id> -> (voice, core scenario id)."""

    _, voice, rest = vx_id.split("-", 2)
    return voice, rest


def build_suite(out_dir: Path) -> dict:
    scenarios = build_scenarios()
    lines = "\n".join(s.model_dump_json() for s in scenarios) + "\n"
    write_text_atomic(out_dir / "gold" / "scenarios.jsonl", lines)
    manifest = {"suite": SUITE, "voices": list(VOICES), "scenarios": len(scenarios),
                "core_test_scenarios": len(scenarios) // len(VOICES), "corpus_hash": sha256_text(lines)}
    write_text_atomic(out_dir / "corpus_manifest.json", json.dumps(manifest, indent=1))
    return manifest

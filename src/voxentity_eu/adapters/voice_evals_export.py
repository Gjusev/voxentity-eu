"""voice-evals fixture manifest export (docs/06 §Integración voice-evals).

One manifest per voice × condition; duplicate texts within a manifest are
rejected (FixtureCallerVoice indexes clips by exact text). Telephone audio
ships as an explicit 16 kHz transport copy alongside the 8 kHz original;
upsampling never claims wideband recovery.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ..commands import InvalidInput, QualityGateFailed
from ..contracts import AudioRecord, Scenario, read_jsonl
from ..provenance import sha256_file, write_text_atomic

EXPORT_RATE = 16000


def export_voice_evals_fixture(
    scenarios: list[Scenario],
    audio: list[AudioRecord],
    audio_root: Path,
    synthesis_records: list[dict[str, Any]],
    voice_id: str,
    condition: str,
    out_path: Path,
) -> dict[str, Any]:
    import numpy as np
    import soundfile as sf
    from scipy.signal import resample_poly

    scenario_by_id = {s.scenario_id: s for s in scenarios}
    voice_by_sid = {r["synthesis_id"].removeprefix("sy-"): r["speaker_id"] for r in synthesis_records}

    clips: list[dict[str, Any]] = []
    seen_texts: dict[str, str] = {}
    out_dir = out_path.parent
    wav_dir = out_dir / "clips"
    wav_dir.mkdir(parents=True, exist_ok=True)

    for a in audio:
        if a.corpus != "synthetic" or a.condition != condition:
            continue
        if voice_by_sid.get(a.scenario_id) != voice_id:
            continue
        sc = scenario_by_id.get(a.scenario_id)
        if sc is None:
            continue
        text = sc.synthesis_text
        if text in seen_texts:
            raise QualityGateFailed(
                f"duplicate clip text within manifest: {a.audio_id} and {seen_texts[text]}"
            )
        seen_texts[text] = a.audio_id
        src = audio_root / a.path
        data, rate = sf.read(src, dtype="float64", always_2d=False)
        if rate != EXPORT_RATE:
            from math import gcd

            g = gcd(EXPORT_RATE, rate)
            data = resample_poly(data, EXPORT_RATE // g, rate // g)
        name = f"{a.audio_id}.wav"
        target = wav_dir / name
        sf.write(target, (data * 32768.0).clip(-32768, 32767).astype(np.int16), EXPORT_RATE, subtype="PCM_16")
        clips.append(
            {
                "text": text,
                "file": f"clips/{name}",
                "sha256": sha256_file(target),
                "provenance": {
                    "corpus": "voxentity-eu synthetic",
                    "model": next(
                        (r["model_id"] for r in synthesis_records if r["synthesis_id"] == a.synthesis_id),
                        "unknown",
                    ),
                    "model_revision": next(
                        (r["model_revision"] for r in synthesis_records if r["synthesis_id"] == a.synthesis_id),
                        "unknown",
                    ),
                    "voice": voice_id,
                    "condition": condition,
                    "native_sample_rate": a.sample_rate_hz,
                    "resampled_for_transport": a.sample_rate_hz != EXPORT_RATE,
                },
            }
        )

    manifest = {
        "format": {"sample_rate": EXPORT_RATE, "channels": 1, "sample_width": 2, "encoding": "pcm_s16le"},
        "clips": clips,
        "note": (
            f"voxentity-eu synthetic corpus, voice={voice_id}, condition={condition}; "
            "telephone audio upsampled 8->16 kHz for transport only"
            if condition == "telephone"
            else f"voxentity-eu synthetic corpus, voice={voice_id}, condition={condition}"
        ),
    }
    write_text_atomic(out_path, json.dumps(manifest, ensure_ascii=False, indent=1))
    return {"clips": len(clips), "out": str(out_path)}


def cli_export_voice_evals(manifest_path: str, voice_id: str, condition: str, out_path: str) -> dict[str, Any]:
    if condition not in ("clean", "telephone"):
        raise InvalidInput(f"unknown condition {condition}")
    manifest_file = Path(manifest_path)
    scenarios = list(read_jsonl(manifest_file.parent / "gold" / "scenarios.jsonl", Scenario))
    audio = list(read_jsonl(manifest_file, AudioRecord))
    synthesis = []
    synth_path = manifest_file.parent / "synthesis.jsonl"
    if synth_path.exists():
        synthesis = [
            json.loads(line)
            for line in synth_path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
    audio_root = manifest_file.parent.parent / "audio"
    return export_voice_evals_fixture(
        scenarios, audio, audio_root, synthesis, voice_id, condition, Path(out_path)
    )

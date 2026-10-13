"""Second TTS family suite: the 120 core test scenarios synthesized with Piper (VITS).

Gate: research/second-tts-gate.md. Voices pinned at rhasspy/piper-voices
revision below; one voice per locale (thorsten DE, CC0 data; siwis FR,
CC-BY 4.0 data, attribution required). The Piper runtime (piper-tts >= 1.3,
GPL-3.0-or-later) is an external tool used from an isolated venv
(.venv-piper); it is never a dependency of this package. Generated-audio
rights stay "conditional" (DATA_LICENSE.md).

    PYTHONPATH=src .venv-piper/Scripts/python -m voxentity_eu.ext.piper_tts

writes data/ext/piper/generated/{gold/scenarios.jsonl, synthesis.jsonl,
audio_manifest.jsonl} and clean 16 kHz audio; the telephone channel, QA,
export and ASR then use the core CLI on that manifest.
"""

from __future__ import annotations

import json
import wave
from pathlib import Path

from ..contracts import AudioRecord, SynthesisRecord
from ..corpus.generate import build_corpus
from ..provenance import environment_hash, sha256_file, sha256_text, write_text_atomic

SUITE = "piper"
MODEL_ID = "rhasspy/piper-voices"
MODEL_REVISION = "c10ece1aade47bb51c153c893d14e5bf8e5b7117"
VOICES = {"de-DE": "de_DE-thorsten-medium", "fr-FR": "fr_FR-siwis-medium"}
VOICE_SHA256 = {  # .onnx files as downloaded at MODEL_REVISION
    "de_DE-thorsten-medium": "7e64762d8e5118bb578f2eea6207e1a35a8e0c30595010b666f983fc87bb7819",
    "fr_FR-siwis-medium": "641d1ab097da2b81128c076810edb052b385decc8be3381814802a64a73baf99",
}
ROOT = Path(__file__).resolve().parents[3]


def build_scenarios():
    return [s.model_copy(update={"scenario_id": f"px-{s.scenario_id}"}) for s in build_corpus() if s.split == "test"]


def main(out_dir: Path = ROOT / "data/ext/piper/generated", models: Path = ROOT / "models/piper") -> int:
    import numpy as np
    import soundfile as sf
    from piper import PiperVoice

    from ..audio.channel import MASTER_RATE, clean_from_master

    for name, digest in VOICE_SHA256.items():
        if sha256_file(models / f"{name}.onnx") != digest:
            raise SystemExit(f"{name}.onnx does not match the pinned hash")
    scenarios = build_scenarios()
    lines = "\n".join(s.model_dump_json() for s in scenarios) + "\n"
    write_text_atomic(out_dir / "gold" / "scenarios.jsonl", lines)
    audio_root = out_dir.parent / "audio"
    (audio_root / "masters").mkdir(parents=True, exist_ok=True)
    (audio_root / "synthetic/clean").mkdir(parents=True, exist_ok=True)
    voices = {loc: PiperVoice.load(str(models / f"{name}.onnx")) for loc, name in VOICES.items()}
    env = environment_hash(include=("python", "numpy", "soundfile", "onnxruntime", "piper-tts"))
    synth, audio, failed = [], [], []
    for s in scenarios:
        master = audio_root / "masters" / f"{s.scenario_id}.wav"
        try:
            with wave.open(str(master), "wb") as w:
                voices[s.locale].synthesize_wav(s.synthesis_text, w)
        except Exception as exc:  # noqa: BLE001 - recorded, never hidden
            failed.append({"scenario_id": s.scenario_id, "error": f"{type(exc).__name__}: {exc}"})
            continue
        data, rate = sf.read(master, dtype="float64", always_2d=False)
        clean = clean_from_master(data, rate)
        clean_path = audio_root / "synthetic/clean" / f"{s.scenario_id}.wav"
        sf.write(clean_path, clean.astype(np.int16), MASTER_RATE, subtype="PCM_16")
        synth.append(SynthesisRecord(
            synthesis_id=f"sy-{s.scenario_id}", model_id=MODEL_ID, model_revision=MODEL_REVISION,
            speaker_id=VOICES[s.locale], language_arg=s.locale, generation_config={"runtime": "piper-tts", "defaults": True},
            seed=s.seed, environment_hash=env, text_sha256=sha256_text(s.synthesis_text),
            master_sha256=sha256_file(master), attempt=1, quality_decision="accepted"))
        audio.append(AudioRecord.model_validate({
            "audio_id": s.scenario_id, "scenario_id": s.scenario_id, "corpus": "synthetic", "condition": "clean",
            "path": f"synthetic/clean/{s.scenario_id}.wav", "sha256": sha256_file(clean_path),
            "sample_rate_hz": MASTER_RATE, "num_samples": int(len(clean)), "duration_seconds": len(clean) / MASTER_RATE,
            "synthesis_id": f"sy-{s.scenario_id}", "qa_status": "pending_review"}))
    write_text_atomic(out_dir / "synthesis.jsonl", "\n".join(r.model_dump_json() for r in synth) + "\n")
    write_text_atomic(out_dir / "audio_manifest.jsonl", "\n".join(a.model_dump_json() for a in audio) + "\n")
    if failed:
        write_text_atomic(out_dir / "synthesis_attempts.jsonl", "\n".join(json.dumps(f) for f in failed) + "\n")
    write_text_atomic(out_dir / "corpus_manifest.json", json.dumps({
        "suite": SUITE, "scenarios": len(scenarios), "synthesized": len(audio), "failed": len(failed),
        "model_id": MODEL_ID, "model_revision": MODEL_REVISION, "voices": VOICES, "voice_sha256": VOICE_SHA256,
        "runtime": "piper-tts (GPL-3.0-or-later, isolated venv)", "corpus_hash": sha256_text(lines)}, indent=1))
    print({"synthesized": len(audio), "failed": len(failed)})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

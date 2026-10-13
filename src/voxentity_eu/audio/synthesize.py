"""Qwen3-TTS CustomVoice synthesis over the corpus (P3).

Voice policy (docs/03 §B): predefined speakers only, no cloning. Voices were
chosen by generating one DE and one FR sample per candidate on the local GPU
(data/smoke_tts/report4.json): serena and dylan generated cleanly in both
languages. Assignment alternates by case index within each cell (8/7 split),
never by difficulty.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

MODEL_ID = "Qwen/Qwen3-TTS-12Hz-0.6B-CustomVoice"
MODEL_REVISION = "85e237c12c027371202489a0ec509ded67b5e4b5"
VOICES = ("serena", "dylan")
LANGUAGE_ARG = {"de-DE": "german", "fr-FR": "french"}
MASTER_RATE = 24000

CELL_ORDER = [
    (locale, entity)
    for locale in ("de-DE", "fr-FR")
    for entity in (
        "person_name", "phone", "email", "calendar_value", "postal_address", "reference_code"
    )
]


def voice_for(scenario_id: str, locale: str, entity: str, case_index: int) -> str:
    cell_index = CELL_ORDER.index((locale, entity))
    return VOICES[(cell_index + case_index) % 2]


def case_index_of(scenario_id: str) -> int:
    return int(scenario_id.rsplit("-", 1)[1])


def cli_synthesize(manifest_path: str, profile: str = "qwen", resume: bool = True) -> dict[str, Any]:
    import numpy as np
    import soundfile as sf
    import torch

    from ..commands import InvalidInput, MissingDependency
    from ..contracts import AudioRecord, Scenario, SynthesisRecord, read_jsonl
    from ..provenance import environment_hash, sha256_file, sha256_text, write_text_atomic

    if profile != "qwen":
        raise InvalidInput(f"unknown synthesis profile {profile}")
    try:
        from qwen_tts import Qwen3TTSModel
    except ImportError as exc:
        raise MissingDependency(f"qwen-tts unavailable: {exc}") from exc
    if not torch.cuda.is_available():
        raise MissingDependency("cuda unavailable for qwen synthesis profile")

    manifest_file = Path(manifest_path)
    scenarios = list(read_jsonl(manifest_file.parent / "gold" / "scenarios.jsonl", Scenario))
    out_root = manifest_file.parent.parent  # data/
    audio_root = out_root / "audio"
    master_dir = audio_root / "masters"
    master_dir.mkdir(parents=True, exist_ok=True)

    synth_path = manifest_file.parent / "synthesis.jsonl"
    done: dict[str, SynthesisRecord] = {}
    if resume and synth_path.exists():
        for rec in read_jsonl(synth_path, SynthesisRecord):
            done[rec.synthesis_id] = rec

    model = Qwen3TTSModel.from_pretrained(
        MODEL_ID,
        revision=MODEL_REVISION,
        device_map="cuda:0",
        dtype=torch.float32,  # Pascal GTX 1080: no bf16/fp16 codec path
        attn_implementation="sdpa",
    )
    env_hash = environment_hash(include=("python", "torch", "transformers", "numpy", "soundfile"))

    records: list[SynthesisRecord] = list(done.values())
    # merge into the existing manifest: telephone rows and QA verdicts must
    # survive a resume; this run only rewrites clean rows it actually produced
    existing: dict[str, AudioRecord] = {}
    if manifest_file.exists():
        for row in read_jsonl(manifest_file, AudioRecord):
            existing[row.audio_id] = row
    audio_records: list[AudioRecord] = []
    attempts_logged: list[dict[str, Any]] = []
    failed: list[str] = []

    for i, sc in enumerate(sorted(scenarios, key=lambda s: s.scenario_id)):
        sid = f"sy-{sc.scenario_id}"
        text_hash = sha256_text(sc.synthesis_text)
        voice = voice_for(sc.scenario_id, sc.locale, sc.entity_type, case_index_of(sc.scenario_id))
        master_path = master_dir / f"{sc.scenario_id}.wav"
        if sid in done and master_path.exists() and done[sid].text_sha256 == text_hash:
            attempt, master_sha = done[sid].attempt, done[sid].master_sha256
        else:
            attempt = 1 + sum(1 for r in records if r.synthesis_id.startswith(sid))
            try:
                wavs, sr = model.generate_custom_voice(
                    text=sc.synthesis_text,
                    speaker=voice,
                    language=LANGUAGE_ARG[sc.locale],
                )
            except Exception as exc:  # noqa: BLE001 - logged, never hidden
                attempts_logged.append(
                    {"synthesis_id": sid, "attempt": attempt, "error": f"{type(exc).__name__}: {exc}"}
                )
                failed.append(sc.scenario_id)
                continue
            master = (np.asarray(wavs[0], dtype=np.float64) * 32768.0).clip(-32768, 32767).astype(np.int16)
            sf.write(master_path, master, sr, subtype="PCM_16")
            master_sha = sha256_file(master_path)
        rec = SynthesisRecord(
            synthesis_id=sid,
            model_id=MODEL_ID,
            model_revision=MODEL_REVISION,
            speaker_id=voice,
            language_arg=LANGUAGE_ARG[sc.locale],
            generation_config={"dtype": "float32", "attn": "sdpa", "non_streaming": True},
            seed=sc.seed,
            environment_hash=env_hash,
            text_sha256=text_hash,
            master_sha256=master_sha,
            attempt=attempt,
            quality_decision="accepted",
        )
        records = [r for r in records if r.synthesis_id != sid] + [rec]

        # derived clean condition: PCM16 mono 16 kHz from the master
        master_audio, rate = sf.read(master_path, dtype="float64", always_2d=False)
        from .channel import MASTER_RATE, clean_from_master

        clean = clean_from_master(master_audio, rate)
        clean_dir = audio_root / "synthetic" / "clean"
        clean_dir.mkdir(parents=True, exist_ok=True)
        clean_path = clean_dir / f"{sc.scenario_id}.wav"
        sf.write(clean_path, clean.astype(np.int16), MASTER_RATE, subtype="PCM_16")

        new_clean = AudioRecord.model_validate(
            {
                "audio_id": sc.scenario_id,
                "scenario_id": sc.scenario_id,
                "corpus": "synthetic",
                "condition": "clean",
                "path": f"synthetic/clean/{sc.scenario_id}.wav",
                "sha256": sha256_file(clean_path),
                "sample_rate_hz": MASTER_RATE,
                "num_samples": int(len(clean)),
                "duration_seconds": len(clean) / MASTER_RATE,
                "synthesis_id": sid,
                "qa_status": "pending_review",
            }
        )
        existing[new_clean.audio_id] = new_clean
        audio_records.append(new_clean)
        if (i + 1) % 20 == 0:
            print(f"[synthesize] {i + 1}/{len(scenarios)} done", flush=True)
            # incremental checkpoint: crash-safe resume via synthesis.jsonl
            write_text_atomic(
                synth_path,
                "\n".join(r.model_dump_json() for r in sorted(records, key=lambda r: r.synthesis_id)) + "\n",
            )
            write_text_atomic(
                manifest_file,
                "\n".join(a.model_dump_json() for a in sorted(existing.values(), key=lambda a: a.audio_id)) + "\n",
            )

    write_text_atomic(synth_path, "\n".join(r.model_dump_json() for r in sorted(records, key=lambda r: r.synthesis_id)) + "\n")
    write_text_atomic(
        manifest_file,
        "\n".join(a.model_dump_json() for a in sorted(existing.values(), key=lambda a: a.audio_id)) + "\n",
    )
    if attempts_logged:
        write_text_atomic(
            manifest_file.parent / "synthesis_attempts.jsonl",
            "\n".join(json.dumps(a, ensure_ascii=False) for a in attempts_logged) + "\n",
        )
    return {
        "masters": len(audio_records),
        "failed": failed,
        "attempts": len(attempts_logged),
        "voices": VOICES,
    }

"""Inference runner over gold-free inputs, with per-clip cache and resume.

Cache key = sha256(audio bytes) + system identity + decoding config + prompt
hash. The runner never imports the scorer and never sees gold: it reads the
exported inputs directory only (docs/06 §Reanudación y caché).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .commands import InvalidInput
from .provenance import sha256_file, sha256_json, write_text_atomic

SYSTEMS: dict[str, dict[str, str]] = {
    "whisper-turbo": {
        "kind": "asr",
        "class": "voxentity_eu.adapters.whisper.WhisperTurbo",
        "model_id": "openai/whisper-large-v3-turbo",
        "revision": "41f01f3fe87f28c78e2fbf8b568835947dd65ed9",
    },
    "voxtral-mini": {
        "kind": "asr",
        "class": "voxentity_eu.adapters.voxtral.VoxtralMini",
        "model_id": "mistralai/Voxtral-Mini-3B-2507",
        "revision": "3060fe34b35ba5d44202ce9ff3c097642914f8f3",
    },
}


def load_system(system_name: str, device: str, dtype: str):
    if system_name not in SYSTEMS:
        raise InvalidInput(f"unknown system {system_name}; known: {sorted(SYSTEMS)}")
    spec = SYSTEMS[system_name]
    module_path, class_name = spec["class"].rsplit(".", 1)
    module = __import__(module_path.replace("voxentity_eu.", "voxentity_eu."), fromlist=[class_name])
    import importlib

    module = importlib.import_module(module_path)
    cls = getattr(module, class_name)
    return cls(device=device, dtype=dtype), spec


def _cache_key(audio_sha: str, spec: dict[str, str], config: dict[str, Any]) -> str:
    return sha256_json(
        {"audio_sha256": audio_sha, "system": spec, "decoding": config}
    )


def run_asr(
    inputs_dir: Path,
    system_name: str,
    out_dir: Path,
    *,
    device: str = "cuda:0",
    dtype: str = "float16",
    resume: bool = True,
    splits_filter: set[str] | None = None,
    corpus_filter: str | None = None,
) -> dict[str, Any]:
    """Track A (asr) run. Produces predictions.jsonl + run_manifest.json."""

    import time

    rows = [json.loads(line) for line in (inputs_dir / "inputs.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    if corpus_filter:
        rows = [r for r in rows if r["corpus"] == corpus_filter]
    out_dir.mkdir(parents=True, exist_ok=True)
    cache_path = out_dir / "cache.jsonl"
    cache: dict[str, dict[str, Any]] = {}
    if resume and cache_path.exists():
        for line in cache_path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                entry = json.loads(line)
                cache[entry["key"]] = entry

    system, spec = load_system(system_name, device, dtype)
    system.load()
    decoding_config = {"language_explicit": True, "task": "transcribe", "greedy": True, "dtype": dtype}

    results: list[dict[str, Any]] = []
    t_start = time.time()
    for i, row in enumerate(rows):
        audio_path = inputs_dir / row["audio_relpath"]
        audio_sha = sha256_file(audio_path)
        key = _cache_key(audio_sha, spec, decoding_config)
        if key in cache and resume:
            entry = cache[key]
        else:
            try:
                r = system.transcribe(str(audio_path), row["locale"], **decoding_config)
                entry = {
                    "key": key,
                    "input_id": row["input_id"],
                    "status": r.status,
                    "transcript": r.transcript,
                    "error_type": r.error_type,
                }
            except Exception as exc:  # noqa: BLE001 - surfaced as error rows, never hidden
                entry = {
                    "key": key,
                    "input_id": row["input_id"],
                    "status": "error",
                    "transcript": None,
                    "error_type": f"{type(exc).__name__}: {exc}"[:200],
                }
            cache[key] = entry
            write_text_atomic(
                cache_path,
                "\n".join(json.dumps(c, ensure_ascii=False) for c in cache.values()) + "\n",
            )
        results.append(
            {
                "run_id": f"{system_name}-asr",
                "audio_id": row["input_id"],  # opaque input id; joined back gold-side
                "track": "asr",
                "status": entry["status"],
                "transcript": entry["transcript"],
                "predicted_slots": [],
                "error_type": entry["error_type"],
                "raw_artifact_path": None,
                "observed_final_state_path": None,
            }
        )
        if (i + 1) % 20 == 0:
            print(f"[run {system_name}] {i + 1}/{len(rows)}", flush=True)

    completed = sum(1 for r in results if r["status"] == "ok")
    failed = len(results) - completed
    write_text_atomic(
        out_dir / "predictions.jsonl",
        "\n".join(json.dumps(r, ensure_ascii=False) for r in results) + "\n",
    )

    # real provenance hashes: corpus manifest, git commit, core lock
    dataset_hash = "0" * 64
    corpus_manifest = Path("data/generated/corpus_manifest.json")
    if corpus_manifest.exists():
        cm = json.loads(corpus_manifest.read_text(encoding="utf-8"))
        dataset_hash = cm.get("corpus_hash", dataset_hash)
    from .provenance import code_commit

    lock_hash = "0" * 64
    if Path("uv-core.lock").exists():
        lock_hash = sha256_file(Path("uv-core.lock"))

    manifest = {
        "run_id": f"{system_name}-asr",
        "schema_version": "0.2",
        "suite_version": "0.1.0",
        "dataset_hash": dataset_hash,
        "eligible_audio_ids_hash": sha256_json([r["input_id"] for r in rows]),
        "code_commit": code_commit(),
        "dependency_lock_hash": lock_hash,
        "model_id": spec["model_id"],
        "model_revision": spec["revision"],
        "backend": system_name,
        "device": device,
        "precision": dtype,
        "decoding_config": decoding_config,
        "prompt_hash": None,
        "normalizer_version": "norm-1",
        "seed": 0,
        "input_audio_policy": "gold-free exported inputs (opaque ids)",
        "track": "asr",
        "expected_count": len(rows),
        "completed_count": completed,
        "failed_count": failed,
        "access_mode": "local",
        "charge_limit": 0.0,
        "observed_usage": {"wall_clock_seconds": round(time.time() - t_start, 1)},
        "incomplete": completed + failed != len(rows),
    }
    write_text_atomic(out_dir / "run_manifest.json", json.dumps(manifest, ensure_ascii=False, indent=1))
    return {
        "system": system_name,
        "rows": len(results),
        "completed": completed,
        "failed": failed,
        "out": str(out_dir),
    }


def cli_run(inputs: str, system: str, out: str, resume: bool = True) -> dict[str, Any]:
    from .contracts import RunManifest

    inputs_dir = Path(inputs)
    if not (inputs_dir / "inputs.jsonl").exists():
        raise InvalidInput(f"no inputs.jsonl under {inputs_dir}; run corpus export-inputs first")
    device = "cuda:0"
    dtype = "float16"
    if system == "voxtral-mini":
        dtype = "bfloat16"
    result = run_asr(inputs_dir, system, Path(out), device=device, dtype=dtype, resume=resume)
    # manifest re-validation through the contract
    manifest = json.loads((Path(out) / "run_manifest.json").read_text(encoding="utf-8"))
    RunManifest.model_validate(manifest)
    return result

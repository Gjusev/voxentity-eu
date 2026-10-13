"""FLEURS human control (P7): selective download, deterministic sampling.

Only de_de / fr_fr test rows are fetched, pinned to the revision recorded in
the source lock. Rows are chosen by sha256 of their id — never by looking at
results or transcripts. Telephone versions are derived with the same channel
recipe as the synthetic corpus; originals are preserved untouched. FLEURS is
treated as a KNOWN control (likely in ASR training), never as a
generalization test (docs/03 §E, docs/10 risk table).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ..commands import MissingDependency, QualityGateFailed
from ..contracts import SCHEMA_VERSION
from ..provenance import sha256_file, sha256_text, write_text_atomic

FLEURS_CONFIGS = {"de-DE": "de_de", "fr-FR": "fr_fr"}
SAMPLES_PER_LOCALE = 50


def _parquet_files(repo: str, config: str, revision: str, split: str = "test"):
    """Explicit parquet list from HF's official auto-conversion branch.

    The dataset's main branch at the pinned revision ships the legacy
    script+tar layout; docs/03 §E forbids executing dataset scripts, so we
    read the official parquet export (refs/convert/parquet) and pin its
    resolved commit instead.
    """

    try:
        from huggingface_hub import HfApi
    except ImportError as exc:
        raise MissingDependency(f"huggingface_hub unavailable: {exc}") from exc
    api = HfApi()
    parquet_rev = "refs/convert/parquet"
    info = api.dataset_info(repo, revision=parquet_rev)
    resolved = info.sha  # pin the conversion commit, not the moving ref name
    files = api.list_repo_files(repo, revision=resolved, repo_type="dataset")
    prefix = f"{config}/{split}/"
    return sorted(f for f in files if f.startswith(prefix) and f.endswith(".parquet")), resolved


def fleurs_row_key(row: dict[str, Any]) -> str:
    """Stable unique row key: the original audio path (the id column repeats)."""

    path = row.get("path") or row.get("audio", {}).get("path") or ""
    return str(path).rsplit("/", 1)[-1].rsplit(".", 1)[0]


def select_rows(
    rows: list[dict[str, Any]], locale: str, count: int
) -> list[dict[str, Any]]:
    """Deterministic selection by sha256 of the unique row key, ascending."""

    def key(row: dict[str, Any]) -> str:
        return sha256_text(f"fleurs:{locale}:{fleurs_row_key(row)}")

    return sorted(rows, key=key)[:count]


def build_human_control(out_dir: Path, source_lock: Path) -> dict[str, Any]:
    import numpy as np
    import soundfile as sf

    lock = json.loads(source_lock.read_text(encoding="utf-8"))
    fleurs = next(d for d in lock["datasets"] if d["id"] == "google/fleurs")
    revision = fleurs["revision"]

    try:
        from huggingface_hub import hf_hub_download
    except ImportError as exc:
        raise MissingDependency(f"huggingface_hub unavailable: {exc}") from exc

    out_dir.mkdir(parents=True, exist_ok=True)
    audio_root = out_dir / "audio" / "human_control"
    audio_root.mkdir(parents=True, exist_ok=True)

    manifest_rows: list[dict[str, Any]] = []
    per_locale_counts: dict[str, int] = {}
    parquet_revision: str | None = None

    for locale, config in FLEURS_CONFIGS.items():
        files, resolved = _parquet_files("google/fleurs", config, revision)
        parquet_revision = resolved
        if not files:
            raise QualityGateFailed(
                f"no parquet test files for {config} at revision {revision}; "
                "inspect the dataset format before proceeding"
            )
        rows: list[dict[str, Any]] = []
        for fname in files:
            local = hf_hub_download(
                "google/fleurs", fname, revision=resolved, repo_type="dataset"
            )
            import pyarrow.parquet as pq

            table = pq.read_table(local)
            df = table.to_pydict()
            for i in range(len(df["id"])):
                rows.append({k: df[k][i] for k in df.keys()})
        test_rows = [r for r in rows if str(r.get("raw_transcription", r.get("transcription", "")))]
        selected = select_rows(test_rows, locale, SAMPLES_PER_LOCALE)
        per_locale_counts[locale] = len(selected)

        for row in selected:
            rid = fleurs_row_key(row)
            audio_bytes = row["audio"]["bytes"]
            base = f"fleurs-{config}-{rid}"
            # original preserved untouched
            orig_path = audio_root / f"{base}-orig.wav"
            orig_path.write_bytes(audio_bytes)
            data, rate = sf.read(orig_path, dtype="float64", always_2d=False)
            if data.ndim > 1:
                data = data.mean(axis=1)

            from ..audio.channel import (
                MASTER_RATE,
                clean_from_master,
                noise_seed_for,
                telephone_from_master,
            )

            clean = clean_from_master(data, rate)
            clean_path = audio_root / f"{base}-clean.wav"
            sf.write(clean_path, clean.astype(np.int16), MASTER_RATE, subtype="PCM_16")

            tel = telephone_from_master(data, rate, noise_seed=noise_seed_for(base))
            tel_path = audio_root / f"{base}-tel.wav"
            sf.write(tel_path, tel.samples.astype(np.int16), 8000, subtype="PCM_16")

            transcript = str(row.get("raw_transcription", row.get("transcription", "")))
            common = {
                "scenario_id": None,
                "corpus": "human_control",
                "source_id": "S04",
                "external_row_id": rid,
                "external_split": "test",
                "transcript": transcript,
                "qa_status": "accepted",
                "encoding": "pcm_s16le",
                "channels": 1,
            }
            manifest_rows.append(
                {
                    "audio_id": f"{base}-clean",
                    "condition": "clean",
                    "path": f"human_control/{base}-clean.wav",
                    "sha256": sha256_file(clean_path),
                    "sample_rate_hz": MASTER_RATE,
                    "num_samples": int(len(clean)),
                    "duration_seconds": len(clean) / MASTER_RATE,
                    **common,
                }
            )
            manifest_rows.append(
                {
                    "audio_id": f"{base}-tel",
                    "condition": "telephone",
                    "parent_audio_id": f"{base}-clean",
                    "path": f"human_control/{base}-tel.wav",
                    "sha256": sha256_file(tel_path),
                    "sample_rate_hz": 8000,
                    "num_samples": int(len(tel.samples)),
                    "duration_seconds": len(tel.samples) / 8000,
                    **common,
                }
            )

    write_text_atomic(
        out_dir / "human_control_manifest.jsonl",
        "\n".join(json.dumps(r, ensure_ascii=False) for r in manifest_rows) + "\n",
    )
    attribution = {
        "schema_version": SCHEMA_VERSION,
        "source": "google/fleurs",
        "revision": revision,
        "parquet_export_revision": parquet_revision,
        "parquet_note": (
            "main branch ships the legacy script format; rows were read from HF's "
            "official auto-converted parquet branch at the commit above, no dataset "
            "scripts executed"
        ),
        "license": fleurs["declared_license"],
        "license_url": "https://creativecommons.org/licenses/by/4.0/",
        "rights_holder": "Google (FLEURS authors)",
        "modification_note": (
            "clean copies peak-normalized to -6 dBFS and resampled to 16 kHz PCM16; "
            "telephone copies pass the voxentity-eu simulated channel recipe; "
            "originals preserved as *-orig.wav"
        ),
        "selection": "50 rows per locale by ascending sha256(fleurs:<locale>:<id>)",
        "per_locale_selected": per_locale_counts,
    }
    write_text_atomic(out_dir / "attribution.json", json.dumps(attribution, ensure_ascii=False, indent=1))
    return {"rows": len(manifest_rows), "per_locale": per_locale_counts}


def cli_human_control(source_lock: str, out: str) -> dict[str, Any]:
    lock_path = Path(source_lock)
    if not lock_path.exists():
        lock_path = Path("research/artifacts.json")
    return build_human_control(Path(out), lock_path)

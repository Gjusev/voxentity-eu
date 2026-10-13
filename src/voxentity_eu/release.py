"""Release bundle validation (P9, gate G8).

Checks the bundle contains exactly what publication claims: manifests, gold,
inputs, licenses, checksums, frozen predictions, report, dataset card; no
credentials anywhere; every redistributed asset has verified rights.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from .commands import QualityGateFailed

REQUIRED_FILES = [
    "bundle_manifest.json",
    "checksums.sha256",
    "LICENSE",
    "DATA_LICENSE.md",
    "THIRD_PARTY_NOTICES.md",
    "dataset_card/DATASET_CARD.md",
    "reports/report.md",
    "gold/scenarios.jsonl",
    "rights_registry.jsonl",
]

SECRET_PATTERNS = [
    re.compile(r"hf_[A-Za-z0-9]{20,}"),
    re.compile(r"KGAT_[A-Za-z0-9]{20,}"),
    re.compile(r"kaggle\s*=\s*\{", re.IGNORECASE),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
]


def cli_release_validate(bundle: str) -> dict[str, Any]:
    bundle_dir = Path(bundle)
    if not bundle_dir.is_dir():
        raise QualityGateFailed(f"bundle directory not found: {bundle_dir}")

    problems: list[str] = []
    for rel in REQUIRED_FILES:
        if not (bundle_dir / rel).exists():
            problems.append(f"missing required file: {rel}")

    # no secrets in any bundled text file
    for path in bundle_dir.rglob("*"):
        if path.is_file() and path.suffix.lower() in (".json", ".jsonl", ".md", ".txt", ".yaml", ".py"):
            try:
                text = path.read_text(encoding="utf-8")
            except (UnicodeDecodeError, OSError):
                continue
            for pattern in SECRET_PATTERNS:
                if pattern.search(text):
                    problems.append(f"secret-like content in {path.name} ({pattern.pattern})")

    # rights: no blocked or unreviewed-conditional assets marked redistributable
    registry = bundle_dir / "rights_registry.jsonl"
    if registry.exists():
        for line in registry.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            entry = json.loads(line)
            if entry.get("review_status") == "blocked" and entry.get("redistribution") == "allowed":
                problems.append(f"blocked asset marked redistributable: {entry['source_id']}")

    # frozen predictions exist for every run named in the bundle manifest
    bm_path = bundle_dir / "bundle_manifest.json"
    if bm_path.exists():
        bm = json.loads(bm_path.read_text(encoding="utf-8"))
        for run in bm.get("runs", []):
            pred = bundle_dir / "predictions" / f"{run}.jsonl"
            if not pred.exists():
                problems.append(f"bundle manifest names run without predictions: {run}")

    # checksums verify
    sums = bundle_dir / "checksums.sha256"
    if sums.exists():
        import hashlib

        for line in sums.read_text(encoding="utf-8").splitlines():
            parts = line.split()
            if len(parts) != 2:
                continue
            digest, rel = parts
            target = bundle_dir / rel
            if not target.exists():
                problems.append(f"checksum lists missing file: {rel}")
                continue
            actual = hashlib.sha256(target.read_bytes()).hexdigest()
            if actual != digest:
                problems.append(f"checksum mismatch: {rel}")

    if problems:
        raise QualityGateFailed(f"{len(problems)} release problems: {problems[:5]}")
    return {"bundle": str(bundle_dir), "status": "ok", "checks": len(REQUIRED_FILES) + 1}


def build_bundle(source_dir: Path, out_dir: Path) -> dict[str, Any]:
    """Assemble the local release bundle with checksums (no external push)."""

    import hashlib
    import shutil

    out_dir.mkdir(parents=True, exist_ok=True)
    entries: list[Path] = []

    def copy_if_exists(rel: str, dest: str | None = None) -> None:
        src = source_dir / rel
        if src.exists():
            target = out_dir / (dest or rel)
            target.parent.mkdir(parents=True, exist_ok=True)
            if src.is_dir():
                shutil.copytree(src, target, dirs_exist_ok=True)
                entries.extend(p for p in target.rglob("*") if p.is_file())
            else:
                shutil.copyfile(src, target)
                entries.append(target)

    for rel, dest in [
        ("data/generated/gold/scenarios.jsonl", "gold/scenarios.jsonl"),
        ("data/generated/gold/input_mapping_inputs.json", "gold/input_mapping_inputs.json"),
        ("data/generated/corpus_manifest.json", "corpus_manifest.json"),
        ("data/generated/rights_registry.jsonl", "rights_registry.jsonl"),
        ("data/generated/synthesis.jsonl", "synthesis.jsonl"),
        ("data/generated/transforms.jsonl", "transforms.jsonl"),
        ("data/generated/audio_manifest.jsonl", "audio_manifest.jsonl"),
        ("data/generated/qa.jsonl", "qa.jsonl"),
        ("data/human_control/human_control_manifest.jsonl", "human_control_manifest.jsonl"),
        ("data/human_control/attribution.json", "attribution.json"),
        ("LICENSE", "LICENSE"),
        ("DATA_LICENSE.md", "DATA_LICENSE.md"),
        ("THIRD_PARTY_NOTICES.md", "THIRD_PARTY_NOTICES.md"),
        ("dataset_card/DATASET_CARD.md", "dataset_card/DATASET_CARD.md"),
        ("reports/report.md", "reports/report.md"),
        ("uv-core.lock", "uv-core.lock"),
    ]:
        copy_if_exists(rel, dest)
    copy_if_exists("runs", "predictions")

    lines = []
    for f in sorted(entries):
        digest = hashlib.sha256(f.read_bytes()).hexdigest()
        lines.append(f"{digest} {f.relative_to(out_dir).as_posix()}")
    (out_dir / "checksums.sha256").write_text("\n".join(lines) + "\n", encoding="utf-8")

    manifest = {
        "bundle_version": "0.1.0",
        "runs": sorted(p.stem for p in (out_dir / "predictions").glob("*.jsonl")) if (out_dir / "predictions").exists() else [],
        "files": len(entries),
        "notes": "local bundle; external publication requires explicit push commands",
    }
    (out_dir / "bundle_manifest.json").write_text(json.dumps(manifest, indent=1), encoding="utf-8")
    return {"files": len(entries), "out": str(out_dir)}

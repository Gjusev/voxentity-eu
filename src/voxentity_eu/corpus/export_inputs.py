"""Gold-free evaluation input export with opaque IDs.

The export directory is the ONLY thing inference workers ever see: audio
bytes, locale, requested slot type — no canonical values, no written text,
no difficulty tags, no filenames encoding answers (docs/04 §Aislamiento).
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

from ..contracts import AudioRecord, Scenario
from ..provenance import sha256_json, sha256_text, write_text_atomic
from ..scoring.normalize import canonical_form


def opaque_id(audio_id: str, run_scope: str) -> str:
    """Stable per-run opaque id; the audio_id -> opaque map stays gold-side."""

    return sha256_text(f"{run_scope}:{audio_id}")[:16]


def export_inputs(
    scenarios: list[Scenario],
    audio: list[AudioRecord],
    audio_root: Path,
    out_dir: Path,
    *,
    run_scope: str = "voxentity-eu-v1",
    corpus: str = "synthetic",
) -> dict[str, Any]:
    scenario_by_id = {s.scenario_id: s for s in scenarios}
    rows: list[dict[str, Any]] = []
    mapping: dict[str, str] = {}
    problems: list[str] = []

    (out_dir / "audio").mkdir(parents=True, exist_ok=True)
    # iteration order is by opaque input_id: ordering by audio_id would leak
    # the split/difficulty structure encoded in the audio_id string
    prepared = [a for a in audio if a.corpus == corpus and a.qa_status == "accepted"]
    for a in sorted(prepared, key=lambda r: opaque_id(r.audio_id, run_scope)):
        sc = scenario_by_id.get(a.scenario_id)
        if sc is None:
            problems.append(f"{a.audio_id}: no scenario (non-synthetic should use corpus=human_control)")
            continue
        src = audio_root / a.path
        if not src.exists():
            problems.append(f"{a.audio_id}: audio file missing {src}")
            continue
        # answers must not leak through the filename (case-insensitive)
        canon = str(canonical_form(sc.entities[0].canonical_value, sc.entity_type, sc.locale)).lower()
        if any(tok and tok.lower() in canon and len(tok) >= 3 for tok in src.stem.replace("-", " ").split()):
            problems.append(f"{a.audio_id}: filename appears to encode the answer ({src.stem})")
            continue
        oid = opaque_id(a.audio_id, run_scope)
        target = out_dir / "audio" / f"{oid}.wav"
        shutil.copyfile(src, target)
        mapping[oid] = a.audio_id
        rows.append(
            {
                "input_id": oid,
                "audio_relpath": f"audio/{oid}.wav",
                "sha256": a.sha256,
                "locale": sc.locale,
                "corpus": a.corpus,
                "condition": a.condition,
                "requested_slot_type": sc.entity_type,  # public knowledge, no answer
            }
        )

    write_text_atomic(out_dir / "inputs.jsonl", "\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n")
    # mapping is gold-side material: written next to the gold, never into inputs/
    return {
        "exported": len(rows),
        "eligible_hash": sha256_json([r["input_id"] for r in rows]),
        "problems": problems,
        "mapping": mapping,
    }


def cli_export_inputs(manifest_path: str, out_path: str) -> dict[str, Any]:
    from ..commands import InvalidInput, QualityGateFailed
    from ..contracts import read_jsonl

    manifest_file = Path(manifest_path)
    audio = list(read_jsonl(manifest_file, AudioRecord))
    gold_dir = manifest_file.parent / "gold"
    scenarios_file = gold_dir / "scenarios.jsonl"
    if not scenarios_file.exists():
        raise InvalidInput(f"gold scenarios not found at {scenarios_file}; run corpus build first")
    scenarios = list(read_jsonl(scenarios_file, Scenario))

    out_dir = Path(out_path)
    result = export_inputs(scenarios, audio, audio_root=manifest_file.parent.parent / "audio", out_dir=out_dir)
    if result["problems"]:
        raise QualityGateFailed(f"export problems: {result['problems'][:5]}")
    # gold-side mapping: keep beside gold, never inside the inputs dir
    write_text_atomic(
        gold_dir / f"input_mapping_{out_dir.name}.json",
        json.dumps(result.pop("mapping"), ensure_ascii=False, indent=1),
    )
    return result

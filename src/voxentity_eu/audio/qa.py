"""Automated audio QA (docs/03-data.md §C).

Checks: decodable, mono, finite amplitude, no material clipping (< 0.1%
saturated samples), non-zero energy, plausible duration (1-45 s), no
truncation-style ending (abrupt cut at the last sample of an active region).
ASR disagreement only ever produces alerts, never exclusions.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np

MIN_DURATION_S = 1.0
MAX_DURATION_S = 45.0
MAX_CLIPPING_FRACTION = 0.001


@dataclass
class QaVerdict:
    audio_id: str
    passed: bool
    checks: dict[str, Any] = field(default_factory=dict)
    failures: list[str] = field(default_factory=list)

    @property
    def qa_status(self) -> str:
        """accepted / truncated / wrong_synthesis / ambiguous / pending_review."""

        if self.passed:
            return "accepted"
        if "duration_out_of_range" in self.failures:
            return "truncated"
        if "zero_energy" in self.failures or "undecodable" in self.failures:
            return "wrong_synthesis"
        return "ambiguous"


def qa_audio(path: Path, expected_rate: int) -> QaVerdict:
    import soundfile as sf

    verdict = QaVerdict(audio_id=path.stem, passed=True)
    if not path.exists():
        verdict.passed = False
        verdict.failures.append("missing_file")
        return verdict
    try:
        info = sf.info(str(path))
    except Exception as exc:  # noqa: BLE001 - corrupt bytes land here
        verdict.passed = False
        verdict.failures.append(f"undecodable:{type(exc).__name__}")
        return verdict

    verdict.checks["format"] = info.format
    verdict.checks["sample_rate"] = info.samplerate
    verdict.checks["channels"] = info.channels
    if info.channels != 1:
        verdict.passed = False
        verdict.failures.append("not_mono")
    if info.samplerate != expected_rate:
        verdict.passed = False
        verdict.failures.append("sample_rate_mismatch")

    try:
        data, rate = sf.read(str(path), dtype="float64", always_2d=False)
    except Exception as exc:  # noqa: BLE001
        verdict.passed = False
        verdict.failures.append(f"undecodable_read:{type(exc).__name__}")
        return verdict

    duration = len(data) / rate
    verdict.checks["duration_seconds"] = round(duration, 3)
    if not (MIN_DURATION_S <= duration <= MAX_DURATION_S):
        verdict.passed = False
        verdict.failures.append("duration_out_of_range")

    if not np.all(np.isfinite(data)):
        verdict.passed = False
        verdict.failures.append("non_finite")

    peak = float(np.max(np.abs(data))) if data.size else 0.0
    saturated = float(np.mean(np.abs(data) >= 0.999)) if data.size else 1.0
    verdict.checks["peak"] = round(peak, 4)
    verdict.checks["clipping_fraction"] = round(saturated, 6)
    if saturated > MAX_CLIPPING_FRACTION:
        verdict.passed = False
        verdict.failures.append("material_clipping")
    if peak == 0.0 or float(np.mean(data * data)) < 1e-10:
        verdict.passed = False
        verdict.failures.append("zero_energy")

    # abrupt ending: energy in the last 50 ms close to speech level
    tail = data[-(rate // 20) :]
    tail_rms = float(np.sqrt(np.mean(tail * tail))) if tail.size else 0.0
    overall_rms = float(np.sqrt(np.mean(data * data)))
    verdict.checks["tail_rms_ratio"] = round(tail_rms / overall_rms, 3) if overall_rms > 0 else 1.0
    if overall_rms > 0 and tail_rms > 3.0 * overall_rms * 0.9:
        verdict.failures.append("abrupt_ending_alert")  # alert, not exclusion
    return verdict


def cli_qa(manifest_path: str, out_path: str) -> dict[str, Any]:
    from ..contracts import AudioRecord, read_jsonl
    from ..provenance import write_text_atomic

    manifest_file = Path(manifest_path)
    audio = list(read_jsonl(manifest_file, AudioRecord))
    audio_root = manifest_file.parent.parent / "audio"

    verdicts: list[dict[str, Any]] = []
    for a in audio:
        if a.corpus != "synthetic":
            continue
        v = qa_audio(audio_root / a.path, a.sample_rate_hz)
        verdicts.append(
            {
                "audio_id": a.audio_id,
                "qa_status": v.qa_status,
                "passed": v.passed,
                "failures": v.failures,
                "checks": v.checks,
            }
        )

    write_text_atomic(out_path, "\n".join(json.dumps(v, ensure_ascii=False) for v in verdicts) + "\n")
    # write statuses back into the manifest (eligibility freezes before inference)
    status_by_id = {v["audio_id"]: v["qa_status"] for v in verdicts}
    updated = []
    for a in audio:
        if a.audio_id in status_by_id and a.qa_status == "pending_review":
            data = a.model_dump()
            data["qa_status"] = status_by_id[a.audio_id]
            updated.append(AudioRecord.model_validate(data))
        else:
            updated.append(a)
    write_text_atomic(manifest_file, "\n".join(r.model_dump_json() for r in updated) + "\n")
    counts: dict[str, int] = {}
    for v in verdicts:
        counts[v["qa_status"]] = counts.get(v["qa_status"], 0) + 1
    return {"qa_total": len(verdicts), "counts": counts, "out": out_path, "manifest_updated": manifest_file}

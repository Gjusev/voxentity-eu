"""Freeze measured results into space/results.json (+ audio refs).

Deterministic; refuses to emit placeholder numbers: cases come only from
scored run files. Audio is referenced by relative path and copied under
space/audio/ (telephone at native 8 kHz; browsers handle it).
"""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

from voxentity_eu.contracts import Scenario, read_jsonl
from voxentity_eu.reporting.errors import enrich_with_taxonomy

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    results_dir = ROOT / "runs" / "scored"
    space_dir = ROOT / "space"
    scenarios_path = ROOT / "data/generated/gold/scenarios.jsonl"
    audio_root = ROOT / "data/audio"

    if not results_dir.exists():
        space_dir.joinpath("results.json").write_text(
            json.dumps({"cases": [], "systems": [], "empty_reason": "scored runs not available yet"}),
            encoding="utf-8",
        )
        print("empty state written (no scored runs)")
        return 0

    scenarios = {s.scenario_id: s for s in read_jsonl(scenarios_path, Scenario)}
    cases: list[dict] = []
    (space_dir / "audio").mkdir(parents=True, exist_ok=True)

    for scored_file in sorted(results_dir.glob("*.json")):
        scored = json.loads(scored_file.read_text(encoding="utf-8"))
        if scored.get("incomplete"):
            continue
        scored = enrich_with_taxonomy(scored, scenarios)
        system = scored.get("run_id", scored_file.stem)
        for r in scored.get("results", []):
            if r["split"] != "test":
                continue
            sc = scenarios.get(r["scenario_id"])
            if sc is None:
                continue
            audio_clean = audio_root / "synthetic/clean" / f"{sc.scenario_id}.wav"
            audio_tel = audio_root / "synthetic/telephone" / f"{sc.scenario_id}.wav"
            for src in (audio_clean, audio_tel):
                if src.exists():
                    shutil.copyfile(src, space_dir / "audio" / src.name)
            cases.append(
                {
                    "case_id": f"{system}::{r['scenario_id']}",
                    "system": system,
                    "scenario_id": r["scenario_id"],
                    "locale": r["locale"],
                    "entity_type": r["entity_type"],
                    "condition": r["condition"],
                    "corpus": "synthetic",
                    "difficulty_tags": r["difficulty_tags"],
                    "gold_value": r.get("gold_literal", ""),
                    "predicted_value": r.get("predicted_value"),
                    "transcript": r.get("transcript"),
                    "correct": r["outcome"] == "correct",
                    "error_taxonomy": r.get("error_taxonomy"),
                    "qa_status": "automated-QA/provisional",
                    "audio_clean": f"audio/{audio_clean.name}" if audio_clean.exists() else None,
                    "audio_telephone": f"audio/{audio_tel.name}" if audio_tel.exists() else None,
                    "condition_clean_ok": r["outcome"] if r["condition"] == "clean" else None,
                    "condition_telephone_ok": r["outcome"] if r["condition"] == "telephone" else None,
                }
            )

    cases.sort(key=lambda c: c["case_id"])
    systems = sorted({c["system"] for c in cases})
    (space_dir / "results.json").write_text(
        json.dumps({"cases": cases, "systems": systems}, ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"space data: {len(cases)} cases across {len(systems)} systems")
    return 0


if __name__ == "__main__":
    sys.exit(main())

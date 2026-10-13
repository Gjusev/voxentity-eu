"""Freeze measured results into space/results.json (+ audio refs).

Deterministic; refuses to emit placeholder numbers: cases come only from
scored run files. One case per (system, scenario, condition). Audio is
copied to space/audio/{clean,telephone}/<scenario>.wav (both versions share
the scenario file name, so they must live in separate folders) and stored
as paths relative to space/. Transcripts are joined from the frozen run
predictions (scored files do not carry them).
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
    to_audio_id: dict[str, str] = {}
    for f in sorted((ROOT / "data/generated/gold").glob("input_mapping_*.json")):
        to_audio_id.update(json.loads(f.read_text(encoding="utf-8")))
    cases: list[dict] = []
    shutil.rmtree(space_dir / "audio", ignore_errors=True)  # no stale or overwritten clips
    for cond in ("clean", "telephone"):
        (space_dir / "audio" / cond).mkdir(parents=True)

    for scored_file in sorted(results_dir.glob("*.json")):
        scored = json.loads(scored_file.read_text(encoding="utf-8"))
        if scored.get("incomplete"):
            continue
        scored = enrich_with_taxonomy(scored, scenarios)
        system = scored.get("run_id", scored_file.stem)
        pred_path = ROOT / "runs" / scored_file.stem / "predictions.jsonl"
        transcripts: dict[str, str | None] = {}
        if pred_path.exists():
            for line in pred_path.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    p = json.loads(line)
                    transcripts[to_audio_id.get(p["audio_id"], p["audio_id"])] = p.get("transcript")
        for r in scored.get("results", []):
            if r["split"] != "test":
                continue
            sc = scenarios.get(r["scenario_id"])
            if sc is None:
                continue
            rel = {c: f"audio/{c}/{sc.scenario_id}.wav" for c in ("clean", "telephone")}
            for cond, target in rel.items():
                src = audio_root / "synthetic" / cond / f"{sc.scenario_id}.wav"
                if src.exists():
                    shutil.copyfile(src, space_dir / target)
            cases.append(
                {
                    "case_id": f"{system}::{r['scenario_id']}::{r['condition']}",
                    "system": system,
                    "scenario_id": r["scenario_id"],
                    "locale": r["locale"],
                    "entity_type": r["entity_type"],
                    "condition": r["condition"],
                    "corpus": "synthetic",
                    "difficulty_tags": r["difficulty_tags"],
                    "gold_value": r.get("gold_literal", ""),
                    "predicted_value": r.get("predicted_value"),
                    "transcript": transcripts.get(r["audio_id"]),
                    "correct": r["outcome"] == "correct",
                    "error_taxonomy": r.get("error_taxonomy"),
                    "qa_status": "automated-QA/provisional",
                    "audio_clean": rel["clean"] if (space_dir / rel["clean"]).exists() else None,
                    "audio_telephone": rel["telephone"] if (space_dir / rel["telephone"]).exists() else None,
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

"""Score all runs: slots tracks, ceilings, agent, and WER/CER tables.

CPU-only, offline, deterministic. Every scored output lands in runs/scored/.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, "scripts")
sys.path.insert(0, "src")

from run_tracks import human_control_wer_cer  # noqa: E402

GOLD = Path("data/generated/gold/scenarios.jsonl")
MANIFEST = Path("data/generated/audio_manifest.jsonl")
SCORED = Path("runs/scored")
SCORED.mkdir(parents=True, exist_ok=True)

RUNS = {
    "whisper-turbo-slots": Path("runs/whisper-turbo-slots"),
    "gold-extractor": Path("runs/gold-extractor"),
    "reference-agent": Path("runs/reference-agent"),
    "voxtral-mini-slots": Path("runs/voxtral-mini-slots"),
}


def score_slots() -> None:
    from voxentity_eu.cli import main as cli_main

    for name, run_dir in RUNS.items():
        pred = run_dir / "predictions.jsonl"
        if not pred.exists():
            print(f"[skip] {name}: no predictions")
            continue
        rc = cli_main(
            [
                "score", "--gold", str(GOLD), "--predictions", str(pred),
                "--manifest", str(MANIFEST), "--out", str(SCORED / f"{name}.json"),
            ]
        )
        print(f"[score] {name}: exit {rc}")


def translate_human_predictions() -> Path:
    """Map opaque human-control input ids back to manifest audio ids."""

    manifest_rows = [
        json.loads(line)
        for line in Path("data/human_control/human_control_manifest.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    inputs = {
        json.loads(line)["input_id"]: json.loads(line)
        for line in Path("data/inputs_human/inputs.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    }
    by_sha = {r["sha256"]: r["audio_id"] for r in manifest_rows}
    mapping = {iid: by_sha[meta["sha256"]] for iid, meta in inputs.items() if meta["sha256"] in by_sha}

    src = Path("runs/whisper-human/predictions.jsonl")
    rows = [json.loads(l) for l in src.read_text(encoding="utf-8").splitlines() if l.strip()]
    out_rows = []
    for r in rows:
        r["audio_id"] = mapping[r["audio_id"]]
        out_rows.append(r)
    out = Path("runs/whisper-human/predictions_mapped.jsonl")
    out.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in out_rows) + "\n", encoding="utf-8")
    return out


def human_wer() -> None:
    if not Path("runs/whisper-human/predictions.jsonl").exists():
        print("[skip] human control: no whisper run")
        return
    mapped_dir = Path("runs/whisper-human-mapped")
    mapped_dir.mkdir(exist_ok=True)
    mapped = translate_human_predictions()
    (mapped_dir / "predictions.jsonl").write_text(mapped.read_text(encoding="utf-8"), encoding="utf-8")
    report = human_control_wer_cer(
        mapped_dir,
        Path("data/human_control/human_control_manifest.jsonl"),
        SCORED / "human_control_wer.json",
    )
    print("[human]", json.dumps(report)[:220])


def synthetic_wer() -> None:
    """Corpus WER/CER of ASR transcripts against the spoken synthesis_text."""

    import jiwer

    from voxentity_eu.contracts import Scenario, read_jsonl
    from voxentity_eu.provenance import sha256_file

    scenarios = {s.scenario_id: s for s in read_jsonl(GOLD, Scenario)}
    mapping = {}
    for f in sorted(Path("data/generated/gold").glob("input_mapping_*.json")):
        mapping.update(json.loads(f.read_text(encoding="utf-8")))

    for system in ("whisper-turbo", "voxtral-mini"):
        pred_path = Path(f"runs/{system}/predictions.jsonl")
        if not pred_path.exists():
            continue
        rows = [json.loads(l) for l in pred_path.read_text(encoding="utf-8").splitlines() if l.strip()]
        refs, hyps = [], []
        for r in rows:
            aid = mapping.get(r["audio_id"], r["audio_id"])
            sid = aid.removesuffix("-tel")
            sc = scenarios.get(sid)
            if sc is None:
                continue
            refs.append(sc.synthesis_text)
            hyps.append(r["transcript"] or "" if r["status"] == "ok" else "")
        out = jiwer.process_words(reference=refs, hypothesis=hyps)
        cer = jiwer.cer(reference=" ".join(refs), hypothesis=" ".join(hyps))
        block = {
            "system": system,
            "wer": out.wer,
            "words": out.hits + out.deletions + out.substitutions,
            "cer": float(cer),
            "utterances": len(refs),
        }
        (SCORED / f"synthetic_wer_{system}.json").write_text(
            json.dumps(block, ensure_ascii=False, indent=1), encoding="utf-8"
        )
        print(f"[wer] {system}: WER {out.wer:.3f} CER {float(cer):.3f} n={len(refs)}")


if __name__ == "__main__":
    score_slots()
    synthetic_wer()
    human_wer()

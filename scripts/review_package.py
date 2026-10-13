"""Human listening review of the clean synthetic clips (docs/03-data.md §QA).

    python scripts/review_package.py build            -> review/index.html + review/review.csv
    python scripts/review_package.py apply --reviewer NAME [review/review.csv]

The reviewer listens to each clean clip and checks it says synthesis_text,
with the target entity pronounced as intended. ASR transcripts are not shown:
the verdict must not depend on the evaluated systems (docs/03, docs/10).

apply validates every row, writes data/generated/human_review.jsonl and sets
qa_status of rejected clean clips AND their telephone children in the audio
manifest, which removes them from scoring. The gold is never edited. The
corpus may be called "verified" only when all clean clips have a verdict.
"""

from __future__ import annotations

import argparse
import csv
import html
import json
import os
import sys
from pathlib import Path

from voxentity_eu.contracts import AudioRecord, Scenario, read_jsonl
from voxentity_eu.provenance import write_text_atomic

ROOT = Path(__file__).resolve().parents[1]
GOLD = ROOT / "data/generated/gold/scenarios.jsonl"
MANIFEST = ROOT / "data/generated/audio_manifest.jsonl"
AUDIO_ROOT = ROOT / "data/audio"
REVIEW_DIR = ROOT / "review"
OUT = ROOT / "data/generated/human_review.jsonl"
VERDICTS = {"accepted", "wrong_synthesis", "ambiguous", "truncated"}
FIELDS = ["audio_id", "locale", "entity_type", "target", "synthesis_text", "verdict", "note"]


def _clean_clips() -> list[tuple[AudioRecord, Scenario]]:
    scenarios = {s.scenario_id: s for s in read_jsonl(GOLD, Scenario)}
    audio = read_jsonl(MANIFEST, AudioRecord)
    return [
        (a, scenarios[a.scenario_id])
        for a in sorted(audio, key=lambda a: a.audio_id)
        if a.corpus == "synthetic" and a.condition == "clean"
    ]


def build() -> int:
    REVIEW_DIR.mkdir(exist_ok=True)
    clips = _clean_clips()
    csv_path = REVIEW_DIR / "review.csv"
    if csv_path.exists():
        print(f"refusing to overwrite {csv_path} (may hold verdicts); move it first")
        return 1
    with open(csv_path, "w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS)
        w.writeheader()
        for a, s in clips:
            target = s.entities[-1].mention_text
            w.writerow({"audio_id": a.audio_id, "locale": s.locale, "entity_type": s.entity_type,
                        "target": target, "synthesis_text": s.synthesis_text, "verdict": "", "note": ""})
    rows = []
    for a, s in clips:
        src = Path(os.path.relpath(AUDIO_ROOT / a.path, REVIEW_DIR)).as_posix()
        rows.append(
            f"<tr><td>{html.escape(a.audio_id)}</td><td><audio controls preload='none' src='{html.escape(src)}'></audio></td>"
            f"<td><b>{html.escape(s.entities[-1].mention_text)}</b><br><small>{html.escape(s.synthesis_text)}</small></td></tr>"
        )
    page = (
        "<!doctype html><meta charset='utf-8'><title>VoxEntity-EU listening review</title>"
        "<style>body{font-family:sans-serif}td{border-bottom:1px solid #ddd;padding:6px;vertical-align:top}</style>"
        f"<h1>Listening review: {len(clips)} clean clips</h1>"
        "<p>Does the clip say the small text, with the bold target entity pronounced as intended "
        "(digits, letters, spelling, correction)? Record one verdict per row in review.csv: "
        "accepted, wrong_synthesis, ambiguous or truncated, plus a note for anything not accepted.</p>"
        "<table>" + "".join(rows) + "</table>"
    )
    write_text_atomic(REVIEW_DIR / "index.html", page)
    print(f"{len(clips)} clips -> {REVIEW_DIR / 'index.html'}, {csv_path}")
    return 0


def apply(csv_path: Path, reviewer: str) -> int:
    clips = {a.audio_id for a, _ in _clean_clips()}
    with open(csv_path, encoding="utf-8-sig", newline="") as fh:
        rows = list(csv.DictReader(fh))
    problems = []
    seen: dict[str, dict[str, str]] = {}
    for r in rows:
        aid, verdict = r["audio_id"].strip(), r["verdict"].strip().lower()
        if aid not in clips:
            problems.append(f"unknown audio_id {aid}")
        elif aid in seen:
            problems.append(f"duplicate row {aid}")
        elif verdict and verdict not in VERDICTS:
            problems.append(f"{aid}: verdict {verdict!r} not in {sorted(VERDICTS)}")
        elif verdict and verdict != "accepted" and not r["note"].strip():
            problems.append(f"{aid}: {verdict} needs a note (reason for exclusion)")
        seen[aid] = {"verdict": verdict, "note": r["note"].strip()}
    if problems:
        print("\n".join(problems[:20]))
        return 1

    reviewed = {aid: v for aid, v in seen.items() if v["verdict"]}
    write_text_atomic(
        OUT,
        "\n".join(
            json.dumps({"audio_id": aid, "verdict": v["verdict"], "note": v["note"], "reviewer": reviewer}, ensure_ascii=False)
            for aid, v in sorted(reviewed.items())
        ) + "\n",
    )
    # rejected clean clip -> same status on its telephone child; never touch gold
    status = {aid: v["verdict"] for aid, v in reviewed.items()}
    updated = []
    for a in read_jsonl(MANIFEST, AudioRecord):
        verdict = status.get(a.audio_id) or status.get(a.parent_audio_id or "")
        if a.corpus == "synthetic" and verdict:
            a = AudioRecord.model_validate({**a.model_dump(), "qa_status": verdict})
        updated.append(a)
    write_text_atomic(MANIFEST, "\n".join(r.model_dump_json() for r in updated) + "\n")

    counts: dict[str, int] = {}
    for v in reviewed.values():
        counts[v["verdict"]] = counts.get(v["verdict"], 0) + 1
    complete = len(reviewed) == len(clips)
    print(f"reviewed {len(reviewed)}/{len(clips)} {counts}")
    print("corpus status:", "verified (all clean clips listened)" if complete else "provisional (review incomplete)")
    if any(v != "accepted" for v in status.values()):
        print("rejected clips are now excluded from scoring: rerun scripts/score_all.py and the report")
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("build")
    ap = sub.add_parser("apply")
    ap.add_argument("csv", nargs="?", default=str(REVIEW_DIR / "review.csv"))
    ap.add_argument("--reviewer", required=True)
    args = p.parse_args(argv)
    return build() if args.cmd == "build" else apply(Path(args.csv), args.reviewer)


if __name__ == "__main__":
    sys.exit(main())

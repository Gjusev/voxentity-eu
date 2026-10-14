"""Run the offline release gates (docs/10-validation.md) and print evidence.

    python scripts/release_gates.py            # exit 1 if any gate fails

G4 (run integrity) and G6 (full offline regeneration of every report, then
`git diff --exit-code reports`). G1/G3/G7 have their own commands; the
consolidated evidence lives in reports/release_gates.md.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PY = sys.executable


def run(*args: str) -> None:
    subprocess.run([PY, *args], cwd=ROOT, check=True, capture_output=True)


def g4() -> bool:
    ok = True
    for f in sorted((ROOT / "runs/scored").glob("*.json")):
        d = json.loads(f.read_text(encoding="utf-8"))
        if "results" not in d:
            continue
        o = d["summary"]["overall"]
        good = not d["incomplete"] and not d["missing_audio_ids"] and d["scored_count"] == d["expected_count"]
        ok &= good
        print(f"G4 {f.stem}: scored {d['scored_count']}/{d['expected_count']} incomplete={d['incomplete']} "
              f"coverage={o['operational_coverage']} failure_rate={o['failure_rate']} {'ok' if good else 'FAIL'}")
    return ok


def g6() -> bool:
    run("scripts/run_tracks.py")
    run("scripts/score_all.py")
    run("-m", "voxentity_eu.cli", "compare", "runs/scored/whisper-turbo-slots.json",
        "runs/scored/voxtral-mini-slots.json", "--out", "runs/scored/system_comparison.json")
    run("-m", "voxentity_eu.cli", "report", "--results", "runs/scored", "--out", "reports/report.md")
    for suite in ("codeswitch", "es", "multiturn", "voices", "piper"):
        run("scripts/ext_suites.py", suite)
    diff = subprocess.run(["git", "diff", "--stat", "--exit-code", "reports"], cwd=ROOT, capture_output=True, text=True)
    print("G6 regenerated core + 5 extension reports;", "byte-identical" if diff.returncode == 0 else f"DIFF:\n{diff.stdout}")
    return diff.returncode == 0


if __name__ == "__main__":
    import io
    from contextlib import redirect_stdout

    buf = io.StringIO()
    with redirect_stdout(buf):
        results = {"G4": g4(), "G6": g6()}
    evidence = buf.getvalue()
    print(evidence, end="")
    print(results)
    (ROOT / "reports/release_gates.md").write_text(
        f"# Release-gate evidence\n\n"
        f"Regenerate with `python scripts/release_gates.py` (exit 1 if any gate fails).\n"
        f"Committed so the gate output itself is versioned alongside reports/.\n\n"
        f"```\n{evidence}{results}\n```\n",
        encoding="utf-8",
    )
    sys.exit(0 if all(results.values()) else 1)

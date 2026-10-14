"""Automated synthesis-failure alert for the core clean clips (alert, never a filter).

A clip is flagged when BOTH independent ASR systems (whisper-turbo, voxtral-mini)
are far (character error rate > 0.6) from BOTH the written and the spoken
reference text. Two unrelated systems failing the same way against both text
forms points at the audio rather than the recognizer. It cannot replace
listening, and flagged clips are not excluded from scoring (docs/03, docs/10).

    python scripts/tts_alert.py
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

import jiwer

from voxentity_eu.contracts import Scenario, read_jsonl

ROOT = Path(__file__).resolve().parents[1]
THRESHOLD = 0.6


def _norm(text: str) -> str:
    return " ".join("".join(c.lower() if c.isalnum() else " " for c in text).split()) or "_"


def main() -> int:
    scenarios = {s.scenario_id: s for s in read_jsonl(ROOT / "data/generated/gold/scenarios.jsonl", Scenario)}
    mapping = json.loads((ROOT / "data/generated/gold/input_mapping_inputs.json").read_text(encoding="utf-8"))

    def load(run: str) -> dict[str, str]:
        rows = (json.loads(x) for x in (ROOT / f"runs/{run}/predictions.jsonl").read_text(encoding="utf-8").splitlines() if x.strip())
        return {mapping[r["audio_id"]]: r["transcript"] or "" for r in rows}

    whisper, voxtral = load("whisper-turbo"), load("voxtral-mini")
    flagged, total = Counter(), Counter()
    for aid in sorted(a for a in whisper if not a.endswith("-tel")):
        s = scenarios[aid]
        refs = (_norm(s.written_text), _norm(s.synthesis_text))
        worst = [min(jiwer.cer(r, _norm(hyp[aid])) for r in refs) for hyp in (whisper, voxtral)]
        total[s.entity_type] += 1
        if all(c > THRESHOLD for c in worst):
            flagged[s.entity_type] += 1
            print(f"{aid}\twhisper={worst[0]:.2f}\tvoxtral={worst[1]:.2f}\t{whisper[aid][:70]}")
    print(f"flagged {sum(flagged.values())}/{sum(total.values())} clean clips:",
          {e: f"{flagged[e]}/{total[e]}" for e in sorted(total)})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

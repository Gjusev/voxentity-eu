"""Score and report the extension suites from frozen ASR transcripts (CPU).

    python scripts/ext_suites.py codeswitch
    python scripts/ext_suites.py multiturn

Prerequisite per suite (GPU, run once): synthesize -> transform -> qa ->
export-inputs -> `voxentity run --system whisper-turbo` into
runs/ext-<suite>/whisper-turbo. Reports land in reports/ext-<suite>/.
Extension numbers are never merged into the core tables.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from run_tracks import build_asr_slots_run, build_gold_extractor_run  # noqa: E402

from voxentity_eu.adapters.slots import EXTRACTOR_VERSION  # noqa: E402
from voxentity_eu.provenance import write_text_atomic  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]


def _paths(suite: str) -> dict[str, Path]:
    base = ROOT / "data/ext" / suite
    return {"gen": base / "generated", "gold": base / "generated/gold/scenarios.jsonl",
            "manifest": base / "generated/audio_manifest.jsonl", "inputs": base / "inputs",
            "runs": ROOT / "runs" / f"ext-{suite}", "report": ROOT / "reports" / f"ext-{suite}"}


def _transcripts(p: dict[str, Path]) -> dict[str, str | None]:
    """Frozen whisper transcripts keyed by audio id (gold-side mapping)."""

    mapping = json.loads((p["gen"] / "gold/input_mapping_inputs.json").read_text(encoding="utf-8"))
    rows = [json.loads(x) for x in (p["runs"] / "whisper-turbo/predictions.jsonl").read_text(encoding="utf-8").splitlines() if x.strip()]
    return {mapping[r["audio_id"]]: (r["transcript"] if r["status"] == "ok" else None) for r in rows}


def codeswitch() -> int:
    from voxentity_eu.cli import main as cli_main
    from voxentity_eu.reporting.render import render_report

    p = _paths("codeswitch")
    scored = p["runs"] / "scored"
    build_asr_slots_run(p["runs"] / "whisper-turbo", p["inputs"], p["runs"] / "whisper-turbo-slots")
    build_gold_extractor_run(p["gold"], p["manifest"], p["inputs"], p["runs"] / "gold-extractor")
    build_gold_extractor_run(p["gold"], p["manifest"], p["inputs"], p["runs"] / "gold-written-extractor", "written_text")
    for run in ("gold-extractor", "gold-written-extractor", "whisper-turbo-slots"):
        rc = cli_main(["score", "--gold", str(p["gold"]), "--predictions", str(p["runs"] / run / "predictions.jsonl"),
                       "--manifest", str(p["manifest"]), "--out", str(scored / f"{run}.json")])
        if rc:
            return rc
    out = p["report"] / "report.md"
    render_report(scored, p["gold"], out)
    intro = (
        "# Extension: code-switching (DE/FR with English pieces)\n\n"
        "Separate suite, not part of the core 180 scenarios: 56 scenarios (16 dev / 40 test), "
        "emails with English separators, phone digits in English, NATO spelling in German, "
        "non-DE/FR names. Synthetic speech (Qwen3-TTS), clean + simulated telephone, automated QA only. "
        f"Whisper large-v3-turbo through extractor {EXTRACTOR_VERSION} (frozen before this suite's ASR "
        "scoring; its rules come from this suite's dev split only). Test N = 40 scenarios x 2 conditions.\n\n"
    )
    body = out.read_text(encoding="utf-8").split("\n", 1)[1]
    write_text_atomic(out, intro + body)
    print(out)
    return 0


def multiturn() -> int:
    import tempfile

    from voxentity_eu.ext import multiturn as mt

    p = _paths("multiturn")
    cases = mt.build_cases()
    asr = _transcripts(p)
    results: dict[str, dict] = {}
    gold_tx = {
        "gold-written": {t.scenario_id + sfx: t.written_text for c in cases for t in c.turns for sfx in ("", "-tel")},
        "gold-spoken": {t.scenario_id + sfx: t.synthesis_text for c in cases for t in c.turns for sfx in ("", "-tel")},
        "whisper-turbo": asr,
    }
    all_rows = {}
    for name, tx in gold_tx.items():
        store = Path(tempfile.mkdtemp()) if name.startswith("gold") else p["runs"] / "agent_store"
        if not name.startswith("gold"):
            import shutil

            shutil.rmtree(store, ignore_errors=True)  # strict reset
        rows = []
        for cond in ("clean", "telephone"):
            rows += mt.run_agent(cases, tx, store, cond)
        scored = mt.score_rows(cases, rows)
        all_rows[name] = scored
        results[name] = mt.summarize(scored, "test")
    p["runs"].mkdir(parents=True, exist_ok=True)
    write_text_atomic(p["runs"] / "scored.json", json.dumps(results, indent=1))
    write_text_atomic(p["runs"] / "agent_rows.jsonl",
                      "\n".join(json.dumps(r, ensure_ascii=False) for r in all_rows["whisper-turbo"]) + "\n")

    def pct(x):
        return "-" if x is None else f"{100 * x:.1f}"

    lines = [
        "# Extension: cross-turn corrections (DE/FR)", "",
        "Separate suite, not part of the core 180 scenarios. 48 two-turn cases (16 dev / 32 test), same "
        "synthetic voice for both turns; kinds: correction (turn 2 replaces the value with a near-miss), "
        "confirmation (turn 2 confirms without restating), repeat (turn 2 restates the same value). "
        "Reference agent: ASR -> extractor -> store_slot per turn (replacement semantics) -> persisted final "
        f"state read back. Extractor {EXTRACTOR_VERSION}. Synthetic speech, simulated telephone channel, "
        "automated QA only. Test N = 32 cases x 2 conditions = 64.", "",
        "| input | final-state accuracy | 95% CI | stale | spurious change | omission | wrong value | "
        "accuracy when both turns extracted correctly (n) |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for name, r in results.items():
        o = r["overall"]
        ci = "-" if o["ci95"] is None else f"[{pct(o['ci95'][0])}, {pct(o['ci95'][1])}]"
        lines.append(f"| {name} | {pct(o['final_state_accuracy'])} | {ci} | {o['outcomes']['stale']} | "
                     f"{o['outcomes']['spurious_change']} | {o['outcomes']['omission']} | {o['outcomes']['wrong_value']} | "
                     f"{pct(o['final_state_accuracy_given_turns_ok'])} ({o['n_turns_extracted_ok']}) |")
    w = results["whisper-turbo"]
    lines += ["", "## Whisper-turbo agent by kind / condition / entity (test)", "",
              "| group | n | final-state accuracy | stale | spurious change |", "| --- | --- | --- | --- | --- |"]
    for label, group in (("kind", w["by_kind"]), ("condition", w["by_condition"]), ("entity", w["by_entity"])):
        for k, b in group.items():
            lines.append(f"| {label}: {k} | {b['n']} | {pct(b['final_state_accuracy'])} | "
                         f"{b['outcomes']['stale']} | {b['outcomes']['spurious_change']} |")
    lines += ["", "Rows with stale or spurious outcomes (test, whisper-turbo):", ""]
    for r in all_rows["whisper-turbo"]:
        if r["split"] == "test" and r["outcome"] in ("stale", "spurious_change"):
            lines.append(f"- `{r['case_id']}` {r['condition']} {r['kind']}: turn values {r['turn_values']} -> "
                         f"final `{r['final_value']}` ({r['outcome']})")
    out = p["report"] / "report.md"
    write_text_atomic(out, "\n".join(lines) + "\n")
    print(out)
    return 0


def voices() -> int:
    """Paired voice analysis: same core test scenarios, four voices.

    serena/dylan come from the core whisper run (one voice per scenario);
    vivian/ryan from this suite (both voices on every scenario).
    """

    from dataclasses import replace

    from voxentity_eu.cli import main as cli_main
    from voxentity_eu.ext.voices import core_id
    from voxentity_eu.scoring.bootstrap import bootstrap_paired_difference
    from voxentity_eu.scoring.match import ExampleResult

    p = _paths("voices")
    scored = p["runs"] / "scored"
    build_asr_slots_run(p["runs"] / "whisper-turbo", p["inputs"], p["runs"] / "whisper-turbo-slots")
    rc = cli_main(["score", "--gold", str(p["gold"]), "--predictions", str(p["runs"] / "whisper-turbo-slots/predictions.jsonl"),
                   "--manifest", str(p["manifest"]), "--out", str(scored / "whisper-turbo-slots.json")])
    if rc:
        return rc
    new = [ExampleResult(**r) for r in json.loads((scored / "whisper-turbo-slots.json").read_text(encoding="utf-8"))["results"]]
    core = [ExampleResult(**r) for r in json.loads((ROOT / "runs/scored/whisper-turbo-slots.json").read_text(encoding="utf-8"))["results"]]
    core_voice = {json.loads(x)["synthesis_id"][3:]: json.loads(x)["speaker_id"]
                  for x in (ROOT / "data/generated/synthesis.jsonl").read_text(encoding="utf-8").splitlines() if x.strip()}
    by_voice = {v: [replace(r, scenario_id=core_id(r.scenario_id)[1]) for r in new if core_id(r.scenario_id)[0] == v]
                for v in ("vivian", "ryan")}

    def acc(rs):
        return sum(r.outcome == "correct" for r in rs) / len(rs) if rs else None

    def pct(x):
        return "-" if x is None else f"{100 * x:.1f}"

    lines = ["# Extension: voice coverage (DE/FR core test scenarios, four voices)", "",
             "The 120 core test scenarios (x clean/telephone) re-synthesized with Qwen3-TTS voices vivian and "
             "ryan; serena/dylan are the core corpus voices (one per scenario). Whisper large-v3-turbo -> "
             f"extractor {EXTRACTOR_VERSION}. Synthetic speech, simulated telephone channel, automated QA only.", "",
             "| voice | scenarios covered | N items | exact slot accuracy |", "| --- | --- | --- | --- |"]
    groups = {"serena (core)": [r for r in core if core_voice[r.scenario_id] == "serena"],
              "dylan (core)": [r for r in core if core_voice[r.scenario_id] == "dylan"],
              "vivian": by_voice["vivian"], "ryan": by_voice["ryan"]}
    for name, rs in groups.items():
        lines.append(f"| {name} | {len({r.scenario_id for r in rs})} | {len(rs)} | {pct(acc(rs))} |")
    d = bootstrap_paired_difference(by_voice["vivian"], by_voice["ryan"])
    lines += ["", f"Paired vivian - ryan (same scenarios and conditions, n={d['n']}): "
              f"{100 * d['point_difference']:+.1f} pp [{100 * d['ci95'][0]:+.1f}, {100 * d['ci95'][1]:+.1f}].", "",
              "Confound check: the core gap serena vs dylan could come from the scenarios each voice got. "
              "Same split, but scored with the new voices:", "",
              "| scenarios originally voiced by | vivian accuracy | ryan accuracy | core voice accuracy |",
              "| --- | --- | --- | --- |"]
    for orig in ("serena", "dylan"):
        ids = {sid for sid, v in core_voice.items() if v == orig}
        lines.append(f"| {orig} | {pct(acc([r for r in by_voice['vivian'] if r.scenario_id in ids]))} | "
                     f"{pct(acc([r for r in by_voice['ryan'] if r.scenario_id in ids]))} | "
                     f"{pct(acc([r for r in core if r.scenario_id in ids]))} |")
    lines += ["", "If vivian and ryan also score higher on dylan's scenarios, the core voice gap reflects "
              "scenario difficulty, not the voice."]
    out = p["report"] / "report.md"
    write_text_atomic(out, "\n".join(lines) + "\n")
    print(out)
    return 0


if __name__ == "__main__":
    sys.exit({"codeswitch": codeswitch, "multiturn": multiturn, "voices": voices}[sys.argv[1]]())

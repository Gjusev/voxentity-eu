"""Report rendering: markdown from frozen scored runs, offline and deterministic."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ..provenance import write_text_atomic
from .errors import enrich_with_taxonomy
from .tables import cell_matrix, system_table


def load_scored(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _to_example_results(scored: dict[str, Any]) -> list[Any]:
    from ..scoring.match import ExampleResult

    out = []
    for r in scored.get("results", []):
        if isinstance(r, dict):
            fields = {f: r.get(f) for f in ExampleResult.__dataclass_fields__}
            fields.pop("correct", None)
            out.append(ExampleResult(**fields))
        else:
            out.append(r)
    return out


def render_report(results_dir: Path, scenarios_path: Path, out_path: Path) -> dict[str, Any]:
    from ..contracts import Scenario, read_jsonl

    scenarios = {s.scenario_id: s for s in read_jsonl(scenarios_path, Scenario)}
    scored_runs: dict[str, dict[str, Any]] = {}
    taxonomy_tables: dict[str, dict[str, int]] = {}
    for f in sorted(results_dir.glob("*.json")):
        scored = load_scored(f)
        if "results" not in scored:
            continue  # wer blocks and other non-run artifacts
        scored = enrich_with_taxonomy(scored, scenarios)  # works on dicts
        from collections import Counter

        taxonomy_tables[f.stem] = dict(
            sorted(
                Counter((r.get("error_taxonomy") or "correct") for r in scored["results"]).items(),
                key=lambda kv: -kv[1],
            )
        )
        scored["results"] = _to_example_results(scored)  # aggregate needs objects
        scored_runs[f.stem] = scored

    lines: list[str] = ["# VoxEntity-EU measured results", ""]
    lines.append(
        "Synthetic speech, simulated telephone channel. All numbers come from "
        "frozen prediction files; corpus-level provisional status is tracked in "
        "IMPLEMENTATION_STATUS.md. N counts scenarios, not audio files."
    )
    lines.append("")

    rows = system_table(scored_runs)
    lines.append("## Systems")
    lines.append("")
    lines.append("| system | track | N | slot accuracy | 95% CI | coverage | macro12 clean | macro12 tel | stale-rate |")
    lines.append("| --- | --- | --- | --- | --- | --- | --- | --- | --- |")
    for r in rows:
        if r.get("status"):
            lines.append(f"| {r['system']} | - | - | {r['status']} | | | | | |")
            continue

        def fmt(x: float | None) -> str:
            return "-" if x is None else f"{100 * x:.1f}"

        ci = r["ci95"]
        ci_s = "-" if ci is None else f"[{100 * ci[0]:.1f}, {100 * ci[1]:.1f}]"
        lines.append(
            f"| {r['system']} | {r['track']} | {r['n']} | {fmt(r['slot_accuracy'])} | {ci_s} | "
            f"{fmt(r['coverage'])} | {fmt(r['macro12_clean'])} | {fmt(r['macro12_telephone'])} | "
            f"{fmt(r['stale_value_rate'])} |"
        )
    lines.append("")

    for name, scored in scored_runs.items():
        if scored.get("incomplete") or "summary" not in scored:
            continue
        pd = scored["summary"]["paired_degradation"]
        lines.append(f"## Paired degradation — {name}")
        lines.append("")
        lines.append(f"- N pairs: {pd['n_pairs']}")
        if pd["accuracy_clean"] is not None:
            lines.append(f"- accuracy clean: {100 * pd['accuracy_clean']:.1f}")
            lines.append(f"- accuracy telephone: {100 * pd['accuracy_telephone']:.1f}")
            lines.append(f"- delta: {pd['delta_percentage_points']:+.1f} percentage points")
        lines.append(f"- transitions: {json.dumps(pd['transition_matrix'])}")
        lines.append("")
        lines.append("### 12-cell matrix (accuracy clean / telephone)")
        lines.append("")
        matrix = cell_matrix(scored)
        lines.append("| cell | N | clean % | telephone % |")
        lines.append("| --- | --- | --- | --- |")
        for row in matrix[1:]:
            cell, n, c, t = row
            lines.append(
                f"| {cell} | {n} | {'-' if c is None else f'{100 * c:.0f}'} | "
                f"{'-' if t is None else f'{100 * t:.0f}'} |"
            )
        lines.append("")

    tax = taxonomy_tables
    lines.append("## Error taxonomy (heuristic, revisable)")
    lines.append("")
    for name, counts in tax.items():
        lines.append(f"- **{name}**: {json.dumps(counts, ensure_ascii=False)}")
    lines.append("")

    human_path = results_dir / "human_control_wer.json"
    if human_path.exists():
        human = json.loads(human_path.read_text(encoding="utf-8"))
        lines.append("## Human control (FLEURS, known corpus)")
        lines.append("")
        lines.append(
            "FLEURS is likely present in ASR training data; this control measures "
            "channel transfer on human speech, not generalization."
        )
        for key in ("wer_clean", "wer_telephone", "cer_clean", "cer_telephone"):
            block = human.get(key, {})
            lines.append(f"- {key}: {block.get('error_rate')}  (denominator {block.get('denominator_units')}, {block.get('utterances')} utterances)")
        lines.append("")

    write_text_atomic(out_path, "\n".join(lines))
    return {"runs": sorted(scored_runs), "out": str(out_path)}


def cli_report(results: str, out: str) -> dict[str, Any]:
    results_dir = Path(results)
    scenarios_path = Path("data/generated/gold/scenarios.jsonl")
    if not scenarios_path.exists():
        from ..commands import InvalidInput

        raise InvalidInput("gold scenarios not found; run corpus build first")
    return render_report(results_dir, scenarios_path, Path(out))

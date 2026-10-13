"""Aggregation: rates with explicit denominators, macro cells, paired degradation."""

from __future__ import annotations

import json
from collections import defaultdict
from collections.abc import Iterable
from typing import Any

from .match import ExampleResult


def _rate(numerator: int, denominator: int) -> float | None:
    """Never shrink the denominator: absent denominator -> None, not 0."""
    return numerator / denominator if denominator else None


def summarize(results: Iterable[ExampleResult]) -> dict[str, Any]:
    results = list(results)
    len(results)

    def block(rows: list[ExampleResult]) -> dict[str, Any]:
        k = len(rows)
        correct = sum(r.correct for r in rows)
        completed = sum(r.status == "ok" for r in rows)
        omission = sum(r.outcome == "omission" for r in rows)
        substitution = sum(r.outcome == "substitution" for r in rows)
        failure = sum(r.outcome == "failure" for r in rows)
        extra = sum(r.extra_output for r in rows)
        stale_den = sum(r.is_correction_case for r in rows)
        stale = sum(r.stale_value for r in rows)
        literal = sum(r.literal_correct for r in rows)
        return {
            "n": k,
            "correct": correct,
            "slot_accuracy": _rate(correct, k),
            "literal_accuracy": _rate(literal, k),
            "operational_coverage": _rate(completed, k),
            "conditional_accuracy": _rate(correct, completed),
            "omission_rate": _rate(omission, k),
            "substitution_rate": _rate(substitution, k),
            "failure_rate": _rate(failure, k),
            "extra_output_rate": _rate(extra, k),
            "stale_value_rate": _rate(stale, stale_den),
            "stale_denominator": stale_den,
        }

    def group(key: str) -> dict[str, Any]:
        buckets: dict[str, list[ExampleResult]] = defaultdict(list)
        for r in results:
            buckets[getattr(r, key)].append(r)
        return dict(sorted(buckets.items()))

    summary: dict[str, Any] = {
        "overall": block(results),
        "by_locale": {k: block(v) for k, v in group("locale").items()},
        "by_entity": {k: block(v) for k, v in group("entity_type").items()},
        "by_condition": {k: block(v) for k, v in group("condition").items()},
        "by_difficulty": {
            tag: block([r for r in results if tag in r.difficulty_tags])
            for tag in sorted({t for r in results for t in r.difficulty_tags})
        },
    }

    # 12 cells locale × entity, macro average per condition (primary macro)
    cells: dict[tuple[str, str], list[ExampleResult]] = defaultdict(list)
    for r in results:
        cells[(r.locale, r.entity_type)].append(r)
    cell_blocks = {f"{loc}|{ent}": block(rows) for (loc, ent), rows in sorted(cells.items())}
    summary["cells_locale_entity"] = cell_blocks

    for condition in ("clean", "telephone"):
        cond_cells = [
            block([r for r in rows if r.condition == condition]) for rows in cells.values()
        ]
        vals = [c["slot_accuracy"] for c in cond_cells if c["n"]]
        summary[f"macro12_{condition}"] = sum(vals) / len(vals) if vals else None

    summary["paired_degradation"] = paired_degradation(results)
    return summary


def paired_degradation(results: Iterable[ExampleResult]) -> dict[str, Any]:
    """Same scenario list on both conditions; accuracy_clean - accuracy_telephone."""

    by_scenario: dict[str, dict[str, ExampleResult]] = defaultdict(dict)
    for r in results:
        by_scenario[r.scenario_id][r.condition] = r
    pairs = [v for v in by_scenario.values() if "clean" in v and "telephone" in v]

    def acc(rows: list[dict[str, ExampleResult]], cond: str) -> float | None:
        flags = [v[cond].correct for v in rows]
        return _rate(sum(flags), len(flags)) if flags else None

    matrix = {"fail->pass": 0, "pass->fail": 0, "pass->pass": 0, "fail->fail": 0}
    for v in pairs:
        c, t = v["clean"].correct, v["telephone"].correct
        key = ("pass" if c else "fail") + "->" + ("pass" if t else "fail")
        matrix[key] += 1

    acc_clean, acc_tel = acc(pairs, "clean"), acc(pairs, "telephone")
    return {
        "n_pairs": len(pairs),
        "accuracy_clean": acc_clean,
        "accuracy_telephone": acc_tel,
        "delta_percentage_points": (
            (acc_clean - acc_tel) * 100.0 if acc_clean is not None and acc_tel is not None else None
        ),
        "transition_matrix": matrix,
    }


# --- comparison ----------------------------------------------------------------


def compare_runs(scored_a: dict[str, Any], scored_b: dict[str, Any]) -> dict[str, Any]:
    """Paired comparison over the same (scenario, condition) cohort; keying by
    scenario alone would collapse conditions and drop half the rows."""

    def key(r: Any) -> tuple[str, str]:
        return (r.scenario_id, r.condition)

    ra = {key(r): r for r in scored_a.get("results", [])}
    rb = {key(r): r for r in scored_b.get("results", [])}
    shared = sorted(set(ra) & set(rb))
    only_a = sorted(set(ra) - set(rb))
    only_b = sorted(set(rb) - set(ra))
    agree_correct = sum(ra[s].correct == rb[s].correct for s in shared)
    a_better = sum(ra[s].correct and not rb[s].correct for s in shared)
    b_better = sum(not ra[s].correct and rb[s].correct for s in shared)
    return {
        "run_a": scored_a.get("run_id"),
        "run_b": scored_b.get("run_id"),
        "n_shared": len(shared),
        "only_in_a": only_a,
        "only_in_b": only_b,
        "accuracy_a": _rate(sum(ra[s].correct for s in shared), len(shared)) if shared else None,
        "accuracy_b": _rate(sum(rb[s].correct for s in shared), len(shared)) if shared else None,
        "both_agree": agree_correct,
        "a_better": a_better,
        "b_better": b_better,
        "cohorts_identical": not only_a and not only_b,
    }


def cli_compare(run_a_path: str, run_b_path: str, out_path: str) -> dict[str, Any]:
    from ..provenance import write_text_atomic

    with open(run_a_path, encoding="utf-8") as fh:
        scored_a = json.load(fh)
    with open(run_b_path, encoding="utf-8") as fh:
        scored_b = json.load(fh)
    comparison = compare_runs(scored_a, scored_b)
    write_text_atomic(out_path, json.dumps(comparison, ensure_ascii=False, indent=1))
    return comparison

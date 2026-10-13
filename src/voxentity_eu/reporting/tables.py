"""Result tables with explicit denominators and frozen-value provenance."""

from __future__ import annotations

from collections import Counter
from typing import Any

from dataclasses import fields as _dc_fields

from ..scoring.aggregate import summarize
from ..scoring.bootstrap import bootstrap_ci


def _g(row: Any, key: str) -> Any:
    """Attribute access for dataclasses, item access for dicts."""
    if isinstance(row, dict):
        return row.get(key)
    if hasattr(row, key):
        return getattr(row, key)
    return None


def system_table(scored_runs: dict[str, dict[str, Any]], *, replicates: int = 2000, seed: int = 20260101) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for name, scored in scored_runs.items():
        if scored.get("incomplete"):
            rows.append({"system": name, "status": "incomplete_run_not_ranked"})
            continue
        results = scored["results"]
        summary = summarize(results)
        ci = bootstrap_ci(results, replicates=replicates, seed=seed)
        rows.append(
            {
                "system": name,
                "track": scored.get("track_hint", "asr_slots"),
                "n": summary["overall"]["n"],
                "slot_accuracy": summary["overall"]["slot_accuracy"],
                "ci95": ci["ci95"],
                "literal_accuracy": summary["overall"]["literal_accuracy"],
                "coverage": summary["overall"]["operational_coverage"],
                "macro12_clean": summary.get("macro12_clean"),
                "macro12_telephone": summary.get("macro12_telephone"),
                "stale_value_rate": summary["overall"]["stale_value_rate"],
                "extra_output_rate": summary["overall"]["extra_output_rate"],
            }
        )
    return rows


def error_taxonomy_table(scored_runs: dict[str, dict[str, Any]]) -> dict[str, dict[str, int]]:
    out: dict[str, dict[str, int]] = {}
    for name, scored in scored_runs.items():
        counts = Counter(
            (_g(r, "error_taxonomy") or "correct") for r in scored.get("results", [])
        )
        out[name] = dict(sorted(counts.items(), key=lambda kv: -kv[1]))
    return out


def cell_matrix(scored: dict[str, Any]) -> list[list[Any]]:
    """12-cell locale x entity accuracies per condition for one run."""

    header = ["cell", "n", "acc_clean", "acc_telephone"]
    rows: list[list[Any]] = [header]
    by_cell: dict[str, dict[str, Any]] = {}
    for r in scored["results"]:
        key = f"{_g(r, 'locale')}|{_g(r, 'entity_type')}"
        by_cell.setdefault(key, {"clean": [], "telephone": []})
        by_cell[key][_g(r, "condition")].append(_g(r, "correct"))
    for key in sorted(by_cell):
        c = by_cell[key]["clean"]
        t = by_cell[key]["telephone"]
        rows.append(
            [
                key,
                len(c) + len(t),
                sum(c) / len(c) if c else None,
                sum(t) / len(t) if t else None,
            ]
        )
    return rows

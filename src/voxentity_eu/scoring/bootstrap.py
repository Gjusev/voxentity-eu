"""Cluster bootstrap: percentile 95% CIs with fixed seed.

Clusters are scenario_ids (a scenario carries its acoustic variants and every
system's rows), stratified by locale × entity. Resampling the *same* clusters
for two systems gives a paired difference interval. Duplicate acoustic
variants of one scenario never increase the independent N.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable
from typing import Any

import numpy as np

from .match import ExampleResult

DEFAULT_REPLICATES = 2000
DEFAULT_SEED = 20260101


def _clusters(results: Iterable[ExampleResult]) -> list[list[ExampleResult]]:
    by_scenario: dict[str, list[ExampleResult]] = defaultdict(list)
    for r in results:
        by_scenario[r.scenario_id].append(r)
    return list(by_scenario.values())


def _accuracy(rows: Iterable[ExampleResult]) -> float | None:
    rows = list(rows)
    return sum(r.correct for r in rows) / len(rows) if rows else None


def _strata(results: list[ExampleResult]) -> dict[tuple[str, str], list[list[ExampleResult]]]:
    """locale × entity stratum -> list of scenario clusters."""

    out: dict[tuple[str, str], list[list[ExampleResult]]] = defaultdict(list)
    for cluster in _clusters(results):
        key = (cluster[0].locale, cluster[0].entity_type)
        out[key].append(cluster)
    return out


def _resample(
    strata: dict[tuple[str, str], list[list[ExampleResult]]], rng: np.random.Generator
) -> list[ExampleResult]:
    drawn: list[ExampleResult] = []
    for clusters in strata.values():
        idx = rng.integers(0, len(clusters), size=len(clusters))
        for i in idx:
            drawn.extend(clusters[int(i)])
    return drawn


def bootstrap_ci(
    results: list[ExampleResult],
    *,
    metric: str = "slot_accuracy",
    replicates: int = DEFAULT_REPLICATES,
    seed: int = DEFAULT_SEED,
) -> dict[str, Any]:
    """Percentile bootstrap interval for the slot accuracy of one run."""

    point = _accuracy(results)
    if point is None:
        return {"metric": metric, "n": 0, "point": None, "ci95": None, "replicates": replicates, "seed": seed}
    strata = _strata(results)
    rng = np.random.default_rng(seed)
    stats = np.empty(replicates, dtype=float)
    for b in range(replicates):
        stats[b] = _accuracy(_resample(strata, rng))
    lo, hi = np.percentile(stats, [2.5, 97.5])
    return {
        "metric": metric,
        "n": len(results),
        "point": point,
        "ci95": [float(lo), float(hi)],
        "replicates": replicates,
        "seed": seed,
    }


def bootstrap_paired_difference(
    results_a: list[ExampleResult],
    results_b: list[ExampleResult],
    *,
    replicates: int = DEFAULT_REPLICATES,
    seed: int = DEFAULT_SEED,
) -> dict[str, Any]:
    """CI for accuracy(A) - accuracy(B) resampling the SAME scenario clusters."""

    # clusters are (scenario, condition) rows of BOTH systems resampled
    # together; collapsing conditions would drop half the data
    by_key_a = {(r.scenario_id, r.condition): r for r in results_a}
    by_key_b = {(r.scenario_id, r.condition): r for r in results_b}
    shared = sorted(set(by_key_a) & set(by_key_b))
    point = _accuracy([by_key_a[s] for s in shared])
    point_b = _accuracy([by_key_b[s] for s in shared])
    if point is None or point_b is None:
        return {"n": 0, "point_difference": None, "ci95": None}

    pairs = [(by_key_a[s], by_key_b[s]) for s in shared]
    strata: dict[tuple[str, str], list[tuple[ExampleResult, ExampleResult]]] = defaultdict(list)
    for pair in pairs:
        key = (pair[0].locale, pair[0].entity_type)
        strata[key].append(pair)

    rng = np.random.default_rng(seed)
    stats = np.empty(replicates, dtype=float)
    for b in range(replicates):
        left: list[ExampleResult] = []
        right: list[ExampleResult] = []
        for pairs in strata.values():
            idx = rng.integers(0, len(pairs), size=len(pairs))
            for i in idx:
                left.append(pairs[int(i)][0])
                right.append(pairs[int(i)][1])
        stats[b] = _accuracy(left) - _accuracy(right)
    lo, hi = np.percentile(stats, [2.5, 97.5])
    return {
        "n": len(shared),
        "point_accuracy_a": point,
        "point_accuracy_b": point_b,
        "point_difference": point - point_b,
        "ci95": [float(lo), float(hi)],
        "replicates": replicates,
        "seed": seed,
    }

"""Report figures as self-contained SVG (stdlib only; core stays dependency-light).

Two figures, both computed from the same scored runs as the tables:
- cells: slot accuracy per locale x entity cell for two ASR systems, with the
  written-gold extractor ceiling as a reference tick (where ASR, not the
  extractor, is the limit).
- deltas: paired differences with bootstrap 95% CIs (system vs system,
  clean vs telephone per system).

Palette: reference dataviz slots 1-2 (blue/orange), validated light and dark
(CVD dE 24.7 / 26.8). Hover = native SVG <title>; values also in the tables.
"""

from __future__ import annotations

from dataclasses import replace
from html import escape
from pathlib import Path
from typing import Any

from ..scoring.bootstrap import bootstrap_paired_difference

STYLE = """<style>
svg{--surface:#fcfcfb;--ink:#0b0b0b;--ink2:#52514e;--muted:#898781;--grid:#e1e0d9;--base:#c3c2b7;--s1:#2a78d6;--s2:#eb6834;--ref:#52514e}
@media (prefers-color-scheme:dark){svg{--surface:#1a1a19;--ink:#f0efec;--ink2:#c3c2b7;--muted:#898781;--grid:#2c2c2a;--base:#383835;--s1:#3987e5;--s2:#d95926;--ref:#c3c2b7}}
text{font-family:system-ui,-apple-system,"Segoe UI",sans-serif;fill:var(--ink2);font-size:12px}
.t{fill:var(--ink);font-size:14px;font-weight:600}.m{fill:var(--muted);font-size:11px;font-variant-numeric:tabular-nums}
.g{stroke:var(--grid);stroke-width:1}.b{stroke:var(--base);stroke-width:1}
</style>"""


def _svg(width: int, height: int, body: list[str], label: str) -> str:
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" role="img" aria-label="{escape(label)}">'
        f"{STYLE}<rect width='100%' height='100%' fill='var(--surface)'/>" + "".join(body) + "</svg>\n"
    )


def _bar(x0: float, y: float, w: float, h: float, color: str, tip: str) -> str:
    """Horizontal bar: square at the baseline, 4px rounded data end."""

    r = min(4.0, w / 2, h / 2)
    if w <= 0:
        return f"<g><title>{escape(tip)}</title><rect x='{x0}' y='{y}' width='2' height='{h}' fill='{color}'/></g>"
    path = (f"M{x0},{y}H{x0 + w - r}Q{x0 + w},{y} {x0 + w},{y + r}V{y + h - r}"
            f"Q{x0 + w},{y + h} {x0 + w - r},{y + h}H{x0}Z")
    return f"<g><title>{escape(tip)}</title><path d='{path}' fill='{color}'/></g>"


def cell_accuracy_svg(runs: dict[str, dict[str, Any]], series: list[tuple[str, str]], ceiling: str) -> str:
    """runs: name -> scored summary; series: [(run name, label)] for slots 1-2."""

    cells = sorted(runs[series[0][0]]["cells_locale_entity"])
    left, plot_w, row_h, bar_h, top = 190, 420, 34, 10, 90
    height = top + row_h * len(cells) + 40
    x = lambda acc: left + plot_w * acc  # noqa: E731
    body = ["<text x='16' y='24' class='t'>Exact slot accuracy by cell (test, n=20 per cell: 10 scenarios x clean+telephone)</text>",
            "<text x='16' y='42' class='m'>Synthetic speech (Qwen3-TTS), simulated telephone channel, automated QA only (provisional). "
            "Same extractor for every row.</text>"]
    # legend: always present for 2 series
    lx = left
    for (_, label), var in zip(series, ("--s1", "--s2"), strict=True):
        body.append(f"<rect x='{lx}' y='58' width='10' height='10' rx='2' fill='var({var})'/><text x='{lx + 14}' y='67'>{escape(label)}</text>")
        lx += 14 + 7 * len(label) + 24
    body.append(f"<rect x='{lx}' y='56' width='2' height='14' fill='var(--ref)'/><text x='{lx + 8}' y='67'>written-gold extractor ceiling</text>")
    for pct in (0, 25, 50, 75, 100):
        gx = x(pct / 100)
        body.append(f"<line x1='{gx}' y1='{top - 6}' x2='{gx}' y2='{top + row_h * len(cells)}' class='{'b' if pct == 0 else 'g'}'/>")
        body.append(f"<text x='{gx}' y='{top + row_h * len(cells) + 16}' text-anchor='middle' class='m'>{pct}%</text>")
    for i, cell in enumerate(cells):
        y0 = top + i * row_h + (row_h - 2 * bar_h - 2) / 2
        locale, entity = cell.split("|")
        body.append(f"<text x='{left - 10}' y='{y0 + bar_h + 5}' text-anchor='end'>{escape(locale)} {escape(entity.replace('_', ' '))}</text>")
        for j, ((run, label), var) in enumerate(zip(series, ("--s1", "--s2"), strict=True)):
            blk = runs[run]["cells_locale_entity"][cell]
            acc = blk["slot_accuracy"] or 0.0
            tip = f"{label} · {cell}: {100 * acc:.0f}% ({blk['correct']}/{blk['n']})"
            body.append(_bar(left, y0 + j * (bar_h + 2), plot_w * acc, bar_h, f"var({var})", tip))
        ceil = runs[ceiling]["cells_locale_entity"][cell]
        cx = x(ceil["slot_accuracy"] or 0.0)
        body.append(f"<g><title>ceiling · {escape(cell)}: {100 * (ceil['slot_accuracy'] or 0):.0f}% ({ceil['correct']}/{ceil['n']})</title>"
                    f"<rect x='{cx - 1}' y='{y0 - 3}' width='2' height='{2 * bar_h + 8}' fill='var(--ref)'/></g>")
    return _svg(left + plot_w + 40, height, body, "Slot accuracy by locale and entity cell")


def _pair_rows(results: list[Any], a_cond: str, b_cond: str) -> tuple[list[Any], list[Any]]:
    """Same-scenario rows of two conditions, relabeled so they pair by scenario."""

    a = [replace(r, condition="pair") for r in results if r.condition == a_cond]
    b = [replace(r, condition="pair") for r in results if r.condition == b_cond]
    return a, b


def paired_deltas(scored_runs: dict[str, dict[str, Any]], systems: list[tuple[str, str]]) -> list[dict[str, Any]]:
    (ra, la), (rb, lb) = systems
    rows = [{"label": f"{la} − {lb} (both conditions)",
             **bootstrap_paired_difference(scored_runs[ra]["results"], scored_runs[rb]["results"])}]
    for run, label in systems:
        rows.append({"label": f"{label}: clean − telephone",
                     **bootstrap_paired_difference(*_pair_rows(scored_runs[run]["results"], "clean", "telephone"))})
    return rows


def deltas_svg(rows: list[dict[str, Any]]) -> str:
    left, plot_w, row_h, top, span = 320, 300, 40, 64, 0.20  # axis -20..+20 pp
    height = top + row_h * len(rows) + 36
    x = lambda d: left + plot_w * (d + span) / (2 * span)  # noqa: E731
    body = ["<text x='16' y='24' class='t'>Paired differences, percentage points (bootstrap 95% CI, stratified)</text>",
            "<text x='16' y='44' class='m'>A CI crossing 0 means no conclusive difference.</text>"]
    for pp in (-20, -10, 0, 10, 20):
        gx = x(pp / 100)
        body.append(f"<line x1='{gx}' y1='{top - 8}' x2='{gx}' y2='{top + row_h * len(rows)}' class='{'b' if pp == 0 else 'g'}'/>")
        body.append(f"<text x='{gx}' y='{top + row_h * len(rows) + 16}' text-anchor='middle' class='m'>{pp:+d}</text>" if pp else
                    f"<text x='{gx}' y='{top + row_h * len(rows) + 16}' text-anchor='middle' class='m'>0</text>")
    for i, r in enumerate(rows):
        cy = top + i * row_h + row_h / 2
        lo, hi = r["ci95"]
        d = r["point_difference"]
        label = f"{100 * d:+.1f} [{100 * lo:+.1f}, {100 * hi:+.1f}] n={r['n']}"
        body.append(f"<text x='{left - 12}' y='{cy + 4}' text-anchor='end'>{escape(r['label'])}</text>")
        body.append(f"<g><title>{escape(r['label'])}: {escape(label)}</title>"
                    f"<line x1='{x(lo)}' y1='{cy}' x2='{x(hi)}' y2='{cy}' stroke='var(--s1)' stroke-width='2' stroke-linecap='round'/>"
                    f"<circle cx='{x(d)}' cy='{cy}' r='5' fill='var(--s1)' stroke='var(--surface)' stroke-width='2'/></g>")
        body.append(f"<text x='{left + plot_w + 12}' y='{cy + 4}' class='m'>{escape(label)}</text>")
    return _svg(left + plot_w + 230, height, body, "Paired accuracy differences with 95% confidence intervals")


def write_figures(scored_runs: dict[str, dict[str, Any]], out_dir: Path) -> list[str]:
    """Writes figures when the needed runs exist; returns markdown lines to embed."""

    systems = [("whisper-turbo-slots", "Whisper turbo"), ("voxtral-mini-slots", "Voxtral Mini")]
    needed = [s for s, _ in systems] + ["gold-written-extractor"]
    if any(n not in scored_runs for n in needed):
        return []
    out_dir.mkdir(parents=True, exist_ok=True)
    summaries = {n: scored_runs[n]["summary"] for n in needed}
    (out_dir / "cell_accuracy.svg").write_text(
        cell_accuracy_svg(summaries, systems, "gold-written-extractor"), encoding="utf-8")
    rows = paired_deltas(scored_runs, systems)
    (out_dir / "paired_deltas.svg").write_text(deltas_svg(rows), encoding="utf-8")
    table = ["| comparison | Δ pp | 95% CI | n |", "| --- | --- | --- | --- |"] + [
        f"| {r['label']} | {100 * r['point_difference']:+.1f} | [{100 * r['ci95'][0]:+.1f}, {100 * r['ci95'][1]:+.1f}] | {r['n']} |"
        for r in rows
    ]
    rel = out_dir.name
    return ["## Figures", "",
            f"![Slot accuracy by cell]({rel}/cell_accuracy.svg)", "",
            "Bars: exact slot accuracy per locale × entity cell (values in the 12-cell tables below). "
            "Gray tick: extractor fed the written gold text; where bars sit far below it the loss is ASR, "
            "where the tick itself is low the extractor is the limit.", "",
            f"![Paired differences]({rel}/paired_deltas.svg)", "", *table, ""]

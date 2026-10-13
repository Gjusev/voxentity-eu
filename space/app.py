"""VoxEntity-EU results Space: CPU-only browser over precalculated results.

Loads a frozen results.json produced by scripts/build_space_data.py. No GPU,
no token, no generation: every number shown comes from measured runs or an
explicit empty state.
"""

from __future__ import annotations

import csv
import json
import tempfile
from pathlib import Path
from typing import Any

import gradio as gr

ROOT = Path(__file__).resolve().parent
RESULTS = ROOT / "results.json"
AUDIO_ROOT = ROOT / "audio"


def load_results() -> dict[str, Any]:
    if not RESULTS.exists():
        return {"cases": [], "systems": [], "empty_reason": "no frozen results yet"}
    return json.loads(RESULTS.read_text(encoding="utf-8"))


DATA = load_results()
CASES = DATA.get("cases", [])


def filter_cases(
    locale: str, entity: str, condition: str, system: str, error_type: str, search_id: str
) -> list[dict[str, Any]]:
    out = []
    for case in CASES:
        if locale != "all" and case["locale"] != locale:
            continue
        if entity != "all" and case["entity_type"] != entity:
            continue
        if system != "all" and case["system"] != system:
            continue
        if condition == "clean_only" and case["condition_clean_ok"] is None:
            continue
        if condition == "telephone_only" and case["condition_telephone_ok"] is None:
            continue
        if error_type == "correct" and not case["correct"]:
            continue
        if error_type == "error" and case["correct"]:
            continue
        if error_type not in ("all", "correct", "error") and case.get("error_taxonomy") != error_type:
            continue
        if search_id and search_id.lower() not in case["case_id"].lower():
            continue
        out.append(case)
    return out


def render_page(
    locale: str, entity: str, condition: str, system: str, error_type: str, search_id: str, page: int
) -> tuple[Any, ...]:
    cases = filter_cases(locale, entity, condition, system, error_type, search_id)
    per_page = 10
    pages = max(1, (len(cases) + per_page - 1) // per_page)
    page = max(0, min(page, pages - 1))
    rows = cases[page * per_page : (page + 1) * per_page]

    table = [[
        c["case_id"], c["locale"], c["entity_type"], c["system"],
        "correct" if c["correct"] else (c.get("error_taxonomy") or "incorrect"),
        c.get("qa_status", ""),
    ] for c in rows]
    header = ["case", "locale", "entity", "system", "outcome", "QA"]

    selected = rows[0] if rows else None
    if selected is None:
        return (
            gr.update(choices=[], value=None),
            "", "", "", None, None, "", "", "",
            f"**{len(cases)} cases match** (page {page + 1}/{pages}) — select a case above",
            page,
        )
    details = f"""**Case `{selected['case_id']}`** — {selected['locale']} / {selected['entity_type']} / corpus **{selected.get('corpus', 'synthetic')}** / QA: {selected.get('qa_status', 'n/a')}

- **Gold (final value):** `{selected['gold_value']}`
- **Captured slot:** `{selected.get('predicted_value') or '—'}` ({'correct' if selected['correct'] else 'INCORRECT'})
- **System transcript:** {selected.get('transcript') or '—'}
- **Difficulty:** {', '.join(selected.get('difficulty_tags', []))}"""
    clean_path = AUDIO_ROOT / selected["audio_clean"] if selected.get("audio_clean") else None
    tel_path = AUDIO_ROOT / selected["audio_telephone"] if selected.get("audio_telephone") else None
    return (
        gr.update(choices=[c["case_id"] for c in rows], value=selected["case_id"]),
        header,
        table,
        details,
        str(clean_path) if clean_path and clean_path.exists() else None,
        str(tel_path) if tel_path and tel_path.exists() else None,
        f"{len(cases)} cases (page {page + 1}/{pages})",
        page,
    )


def on_case_select(case_id: str) -> tuple[Any, ...]:
    for case in CASES:
        if case["case_id"] == case_id:
            details = f"""**Case `{case['case_id']}`** — {case['locale']} / {case['entity_type']} / corpus **{case.get('corpus', 'synthetic')}** / QA: {case.get('qa_status', 'n/a')}

- **Gold (final value):** `{case['gold_value']}`
- **Captured slot:** `{case.get('predicted_value') or '—'}` ({'correct' if case['correct'] else 'INCORRECT'})
- **System transcript:** {case.get('transcript') or '—'}
- **Difficulty:** {', '.join(case.get('difficulty_tags', []))}"""
            clean_path = AUDIO_ROOT / case["audio_clean"] if case.get("audio_clean") else None
            tel_path = AUDIO_ROOT / case["audio_telephone"] if case.get("audio_telephone") else None
            return (
                details,
                str(clean_path) if clean_path and clean_path.exists() else None,
                str(tel_path) if tel_path and tel_path.exists() else None,
            )
    return "", None, None


def deterministic_example(kind: str):
    pool = [c for c in CASES if c["correct"] == (kind == "correct")]
    if not pool:
        return gr.update(choices=[], value=None), "no such example available", None, None
    chosen = sorted(pool, key=lambda c: c["case_id"])[0]
    return (
        gr.update(choices=[c["case_id"] for c in pool], value=chosen["case_id"]),
        f"deterministic pick: {chosen['case_id']}",
        chosen,
    )


def export_csv() -> str:
    with tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False, newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(CASES[0].keys()) if CASES else ["empty"])
        writer.writeheader()
        writer.writerows(CASES)
        return fh.name


def export_json() -> str:
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as fh:
        json.dump(CASES, fh, ensure_ascii=False, indent=1)
        return fh.name


def build_ui() -> gr.Blocks:
    systems = sorted({c["system"] for c in CASES}) or ["none"]
    with gr.Blocks(title="VoxEntity-EU results") as demo:
        gr.Markdown(
            "# VoxEntity-EU — measured spoken-entity capture (DE/FR)\n"
            "Synthetic speech corpus with simulated telephone channel; separate "
            "human-speech control. All numbers are precalculated from frozen runs; "
            "nothing is generated or inferred in this Space."
        )
        if not CASES:
            gr.Markdown(
                f"**Empty state:** {DATA.get('empty_reason', 'no results')} — "
                "this Space shows measured results only and refuses placeholders."
            )
            return demo
        with gr.Row():
            locale = gr.Dropdown(["all", "de-DE", "fr-FR"], value="all", label="Language")
            entity = gr.Dropdown(
                ["all", "person_name", "phone", "email", "calendar_value", "postal_address", "reference_code"],
                value="all", label="Entity type",
            )
            system = gr.Dropdown(["all", *systems], value="all", label="System")
            condition = gr.Dropdown(
                ["all", "clean_only", "telephone_only"], value="all", label="Condition"
            )
            error_type = gr.Dropdown(
                ["all", "correct", "error", "digit_swap", "correction_ignored",
                 "address_component_loss", "spelling_loss", "accent_loss", "omission"],
                value="all", label="Outcome",
            )
            search_id = gr.Textbox(label="Case id contains")
        case_selector = gr.Dropdown(choices=[], label="Case")
        table = gr.Dataframe(headers=["case", "locale", "entity", "system", "outcome", "QA"], interactive=False)
        with gr.Row():
            prev_btn = gr.Button("< prev")
            next_btn = gr.Button("next >")
            correct_btn = gr.Button("show a correct example")
            error_btn = gr.Button("show an error example")
        counter = gr.Markdown()
        page_state = gr.State(0)
        details = gr.Markdown()
        with gr.Row():
            clean_audio = gr.Audio(label="clean (16 kHz)", type="filepath")
            tel_audio = gr.Audio(label="telephone (8 kHz simulated channel)", type="filepath")
        with gr.Row():
            csv_btn, csv_file = gr.Button("download CSV"), gr.File()
            json_btn, json_file = gr.Button("download JSON"), gr.File()

        inputs = [locale, entity, condition, system, error_type, search_id, page_state]
        outputs = [case_selector, table, details, clean_audio, tel_audio, details, counter, page_state]
        for widget in inputs[:6]:
            widget.change(
                lambda *a: render_page(*a, 0), inputs=inputs, outputs=[case_selector, table, details, clean_audio, tel_audio, counter, page_state]
            )
        prev_btn.click(lambda *a: render_page(*a[:6], max(0, a[6] - 1)), inputs=inputs, outputs=[case_selector, table, details, clean_audio, tel_audio, counter, page_state])
        next_btn.click(lambda *a: render_page(*a[:6], a[6] + 1), inputs=inputs, outputs=[case_selector, table, details, clean_audio, tel_audio, counter, page_state])
        case_selector.change(on_case_select, inputs=case_selector, outputs=[details, clean_audio, tel_audio])
        csv_btn.click(export_csv, outputs=csv_file)
        json_btn.click(export_json, outputs=json_file)
    return demo


if __name__ == "__main__":
    build_ui().launch()

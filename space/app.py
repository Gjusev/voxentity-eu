"""VoxEntity-EU results Space: CPU-only browser over precalculated results.

Loads a frozen results.json produced by scripts/build_space_data.py. No GPU,
no token, no generation: every number shown comes from measured runs or an
explicit empty state. One case = one (system, scenario, condition) row.
"""

from __future__ import annotations

import csv
import json
import tempfile
from pathlib import Path
from typing import Any

import gradio as gr

ROOT = Path(__file__).resolve().parent  # audio paths in results.json are relative to here
AUDIO_PUBLISHED = (ROOT / "audio").is_dir()  # tier-1 deploys exclude audio/ (PUBLISHING.md)
RESULTS = ROOT / "results.json"
PER_PAGE = 10
ENTITIES = ["person_name", "phone", "email", "calendar_value", "postal_address", "reference_code"]


def load_results() -> dict[str, Any]:
    if not RESULTS.exists():
        return {"cases": [], "systems": [], "empty_reason": "no frozen results yet"}
    return json.loads(RESULTS.read_text(encoding="utf-8"))


DATA = load_results()
CASES = DATA.get("cases", [])
BY_ID = {c["case_id"]: c for c in CASES}
OUTCOMES = ["correct", "error", *sorted({c["error_taxonomy"] for c in CASES if c.get("error_taxonomy")})]


def filter_cases(locale: str, entity: str, condition: str, system: str, outcome: str, search: str) -> list[dict[str, Any]]:
    def keep(c: dict[str, Any]) -> bool:
        if outcome == "correct":
            ok = c["correct"]
        elif outcome == "error":
            ok = not c["correct"]
        else:
            ok = outcome == "all" or c.get("error_taxonomy") == outcome
        return (
            ok
            and locale in ("all", c["locale"])
            and entity in ("all", c["entity_type"])
            and condition in ("all", c["condition"])
            and system in ("all", c["system"])
            and search.lower() in c["case_id"].lower()
        )

    return [c for c in CASES if keep(c)]


def _audio(rel: str | None) -> str | None:
    if not rel:
        return None
    path = (ROOT / rel).resolve()
    # only files inside the Space bundle; a missing file shows as an empty player
    return str(path) if path.is_relative_to(ROOT) and path.exists() else None


def case_view(case_id: str | None) -> tuple[str, str | None, str | None]:
    c = BY_ID.get(case_id or "")
    if c is None:
        return "Select a case.", None, None
    details = f"""**Case `{c['case_id']}`**: {c['locale']} / {c['entity_type']} / scored condition **{c['condition']}** / corpus **{c['corpus']}** (synthetic speech) / QA: {c['qa_status']}

- **Gold (final value):** `{c['gold_value']}`
- **Captured slot:** `{c.get('predicted_value') or '(none)'}` ({'correct' if c['correct'] else 'INCORRECT: ' + (c.get('error_taxonomy') or 'error')})
- **{'Gold text fed to the extractor (control, no ASR)' if c['system'].startswith('gold-') else 'System transcript'}:** {c.get('transcript') or '(none)'}
- **Difficulty:** {', '.join(c.get('difficulty_tags', []))}"""
    if AUDIO_PUBLISHED and ((c["audio_clean"] and not _audio(c["audio_clean"]))
                            or (c["audio_telephone"] and not _audio(c["audio_telephone"]))):
        details += "\n\n**Audio file missing from this bundle.**"
    return details, _audio(c["audio_clean"]), _audio(c["audio_telephone"])


def render_page(locale, entity, condition, system, outcome, search, page: int) -> tuple[Any, ...]:
    cases = filter_cases(locale, entity, condition, system, outcome, search)
    pages = max(1, -(-len(cases) // PER_PAGE))
    page = max(0, min(page, pages - 1))
    rows = cases[page * PER_PAGE : (page + 1) * PER_PAGE]
    table = [
        [c["case_id"], c["locale"], c["entity_type"], c["condition"], c["system"],
         "correct" if c["correct"] else (c.get("error_taxonomy") or "error")]
        for c in rows
    ]
    selected = rows[0]["case_id"] if rows else None
    counter = f"{len(cases)} cases match (page {page + 1}/{pages})"
    return (gr.update(choices=[c["case_id"] for c in rows], value=selected), table, *case_view(selected), counter, page)


def deterministic_example(kind: str) -> tuple[Any, ...]:
    """Deterministic pick: ASR systems before gold-text controls, then first case id."""

    pool = [c["case_id"] for c in sorted(CASES, key=lambda c: (c["system"].startswith("gold-"), c["case_id"]))
            if c["correct"] == (kind == "correct")]
    if not pool:
        return gr.update(choices=[], value=None), f"No {kind} example available.", None, None
    return (gr.update(choices=[pool[0]], value=pool[0]), *case_view(pool[0]))


def _export(suffix: str) -> str:
    with tempfile.NamedTemporaryFile("w", suffix=suffix, delete=False, newline="", encoding="utf-8") as fh:
        if suffix == ".json":
            json.dump(CASES, fh, ensure_ascii=False, indent=1)
        else:
            writer = csv.DictWriter(fh, fieldnames=list(CASES[0]) if CASES else ["empty"])
            writer.writeheader()
            writer.writerows(CASES)
        return fh.name


def build_ui() -> gr.Blocks:
    with gr.Blocks(title="VoxEntity-EU results") as demo:
        gr.Markdown(
            "# VoxEntity-EU: measured spoken-entity capture (DE/FR)\n"
            "Synthetic speech corpus (automated QA only, no human listening review yet) with a "
            "simulated telephone channel; a separate "
            "human-speech control is reported in the technical report. All numbers are "
            "precalculated from frozen runs; nothing is generated or inferred here."
        )
        if not AUDIO_PUBLISHED:
            gr.Markdown(
                "**Audio is not part of this deployment:** redistribution of the synthetic clips "
                "awaits a rights decision. Gold values, transcripts and scores are complete; the "
                "audio can be regenerated locally from the published text and pinned models."
            )
        if not CASES:
            gr.Markdown(f"**Empty state:** {DATA.get('empty_reason', 'no results')}. "
                        "This Space shows measured results only and refuses placeholders.")
            return demo
        with gr.Row():
            locale = gr.Dropdown(["all", "de-DE", "fr-FR"], value="all", label="Language")
            entity = gr.Dropdown(["all", *ENTITIES], value="all", label="Entity type")
            condition = gr.Dropdown(["all", "clean", "telephone"], value="all", label="Condition")
            system = gr.Dropdown(["all", *DATA["systems"]], value="all", label="System")
            outcome = gr.Dropdown(["all", *OUTCOMES], value="all", label="Outcome")
            search = gr.Textbox(label="Case id contains")
        table = gr.Dataframe(headers=["case", "locale", "entity", "condition", "system", "outcome"],
                             interactive=False)
        with gr.Row():
            prev_btn = gr.Button("< prev")
            next_btn = gr.Button("next >")
            correct_btn = gr.Button("show a correct example")
            error_btn = gr.Button("show an error example")
        counter = gr.Markdown()
        page = gr.State(0)
        case = gr.Dropdown(choices=[], label="Case (exact link: paste its id in 'Case id contains')")
        details = gr.Markdown()
        with gr.Row():
            clean_audio = gr.Audio(label="clean (16 kHz)", type="filepath", visible=AUDIO_PUBLISHED)
            tel_audio = gr.Audio(label="telephone (8 kHz, simulated channel)", type="filepath", visible=AUDIO_PUBLISHED)
        with gr.Row():
            csv_btn, csv_file = gr.Button("download CSV"), gr.File()
            json_btn, json_file = gr.Button("download JSON"), gr.File()

        filters = [locale, entity, condition, system, outcome, search]
        page_out = [case, table, details, clean_audio, tel_audio, counter, page]
        for widget in filters:
            widget.change(lambda *a: render_page(*a, 0), inputs=filters, outputs=page_out)
        prev_btn.click(lambda *a: render_page(*a[:6], a[6] - 1), inputs=[*filters, page], outputs=page_out)
        next_btn.click(lambda *a: render_page(*a[:6], a[6] + 1), inputs=[*filters, page], outputs=page_out)
        example_out = [case, details, clean_audio, tel_audio]
        correct_btn.click(lambda: deterministic_example("correct"), outputs=example_out)
        error_btn.click(lambda: deterministic_example("error"), outputs=example_out)
        case.input(case_view, inputs=case, outputs=[details, clean_audio, tel_audio])
        csv_btn.click(lambda: _export(".csv"), outputs=csv_file)
        json_btn.click(lambda: _export(".json"), outputs=json_file)
        demo.load(lambda *a: render_page(*a, 0), inputs=filters, outputs=page_out)
    return demo


if __name__ == "__main__":
    build_ui().launch()

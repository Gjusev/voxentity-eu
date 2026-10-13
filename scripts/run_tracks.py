"""Track orchestration after ASR runs exist (importable; notebooks stay thin).

- track asr_slots: shared extractor over each ASR run's transcripts
  (gold-free: locale + requested type come from inputs.jsonl).
- gold->extractor ceiling run: extractor over gold synthesis_text (E2 control).
- reference agent run: whisper -> extractor -> store_slot -> observed state (E3).
- human control WER/CER: jiwer, clean vs telephone, corpus-level sums.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from voxentity_eu.adapters.agent import AgentStore, ReferenceAgent
from voxentity_eu.adapters.slots import EXTRACTOR_VERSION, extract
from voxentity_eu.contracts import read_jsonl
from voxentity_eu.provenance import write_text_atomic


def _load_inputs(inputs_dir: Path) -> dict[str, dict[str, Any]]:
    rows = [
        json.loads(line)
        for line in (inputs_dir / "inputs.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    return {r["input_id"]: r for r in rows}


def build_asr_slots_run(asr_run_dir: Path, inputs_dir: Path, out_dir: Path) -> dict[str, Any]:
    """Shared extractor over ASR transcripts; one predictions.jsonl per system."""

    inputs = _load_inputs(inputs_dir)
    predictions = [
        json.loads(line)
        for line in (asr_run_dir / "predictions.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    out: list[dict[str, Any]] = []
    for p in predictions:
        row = inputs[p["audio_id"]]
        if p["status"] == "ok":
            r = extract(p["transcript"] or "", row["requested_slot_type"], row["locale"])
            slots = [{"type": row["requested_slot_type"], "value": s["value"]} for s in r.slots] if r.status == "ok" else []
        else:
            slots = []
        out.append(
            {
                "run_id": f"{p['run_id']}-slots",
                "audio_id": p["audio_id"],
                "track": "asr_slots",
                "status": p["status"],
                "transcript": p["transcript"],
                "predicted_slots": slots,
                "error_type": p["error_type"],
                "raw_artifact_path": None,
                "observed_final_state_path": None,
            }
        )
    out_dir.mkdir(parents=True, exist_ok=True)
    write_text_atomic(
        out_dir / "predictions.jsonl",
        "\n".join(json.dumps(r, ensure_ascii=False) for r in out) + "\n",
    )
    return {"rows": len(out), "extractor": EXTRACTOR_VERSION}


def build_gold_extractor_run(
    scenarios_path: Path,
    audio_manifest_path: Path,
    inputs_dir: Path,
    out_dir: Path,
    text_field: str = "synthesis_text",
) -> dict[str, Any]:
    """E2 control: extractor over gold text (ceiling estimate).

    text_field="synthesis_text" is the spoken form the TTS read;
    text_field="written_text" is the written form an ideal ASR would emit.
    Report both: the spoken ceiling alone is circular (rex-2 lesson).
    """

    from voxentity_eu.contracts import AudioRecord, Scenario

    scenarios = {s.scenario_id: s for s in read_jsonl(scenarios_path, Scenario)}
    audio = read_jsonl(audio_manifest_path, AudioRecord)
    inputs = _load_inputs(inputs_dir)
    id_to_scenario: dict[str, str] = {}
    for gold_dir in (inputs_dir.parent / "gold", inputs_dir.parent / "generated" / "gold", Path("data/generated/gold")):
        for mapping_path in sorted(gold_dir.glob("input_mapping_*.json")):
            id_to_scenario.update(json.loads(mapping_path.read_text(encoding="utf-8")))
    if not id_to_scenario:
        # fall back: manifest audio_id == scenario_id pre-export
        id_to_scenario = {a.audio_id: a.scenario_id for a in audio if a.scenario_id}

    out: list[dict[str, Any]] = []
    for input_id, meta in inputs.items():
        if meta["corpus"] != "synthetic":
            continue
        sid = id_to_scenario.get(input_id, input_id).removesuffix("-tel")
        sc = scenarios.get(sid)
        if sc is None:
            continue
        text = getattr(sc, text_field)
        r = extract(text, sc.entity_type, sc.locale)
        slots = [{"type": sc.entity_type, "value": s["value"]} for s in r.slots] if r.status == "ok" else []
        out.append(
            {
                "run_id": "gold-extractor-ceiling" if text_field == "synthesis_text" else "gold-written-extractor-ceiling",
                "audio_id": input_id,
                "track": "asr_slots",
                "status": "ok",
                "transcript": text,
                "predicted_slots": slots,
                "error_type": None,
                "raw_artifact_path": None,
                "observed_final_state_path": None,
            }
        )
    out_dir.mkdir(parents=True, exist_ok=True)
    write_text_atomic(
        out_dir / "predictions.jsonl",
        "\n".join(json.dumps(r, ensure_ascii=False) for r in out) + "\n",
    )
    return {"rows": len(out)}


class FrozenAsr:
    """Replays a finished ASR run by input id (file stem); never runs a model.

    Lets the agent and extractor tracks be rebuilt on CPU from frozen
    transcripts. A missing id is an error row, not a silent skip.
    """

    name = "frozen"

    def __init__(self, predictions_path: Path) -> None:
        self.rows = {
            r["audio_id"]: r
            for r in (json.loads(line) for line in predictions_path.read_text(encoding="utf-8").splitlines() if line.strip())
        }

    def load(self) -> None:
        pass

    def transcribe(self, audio_path: str, locale: str, **config: Any):
        from voxentity_eu.adapters.base import AsrResult

        row = self.rows[Path(audio_path).stem]
        return AsrResult(status=row["status"], transcript=row["transcript"], error_type=row["error_type"])


def run_reference_agent(
    inputs_dir: Path, out_dir: Path, asr_factory, corpus_filter: str = "synthetic"
) -> dict[str, Any]:
    """E3: reference agent over the same exported inputs, store under out_dir."""

    inputs = _load_inputs(inputs_dir)
    store = AgentStore(out_dir / "agent_store")
    agent = ReferenceAgent(asr_factory(), store)
    predictions: list[dict[str, Any]] = []
    for input_id, meta in sorted(inputs.items()):
        if meta["corpus"] != corpus_filter:
            continue
        audio_path = inputs_dir / meta["audio_relpath"]
        try:
            result = agent.evaluate(
                str(audio_path), meta["requested_slot_type"], meta["locale"], session_id=f"sess-{input_id}"
            )
            state = store.read_state(f"sess-{input_id}")
            slots = [
                {"type": s["type"], "value": s["value"]}
                for s in state["final_slots"]
                if s["type"] == meta["requested_slot_type"]
            ]
            predictions.append(
                {
                    "run_id": "reference-agent",
                    "audio_id": input_id,
                    "track": "agent_slots",
                    "status": "ok",
                    "transcript": result["transcript"],
                    "predicted_slots": slots,
                    "error_type": None,
                    "raw_artifact_path": None,
                    "observed_final_state_path": result["observed_final_state_path"],
                }
            )
        except Exception as exc:  # noqa: BLE001 - error rows participate as failures
            predictions.append(
                {
                    "run_id": "reference-agent",
                    "audio_id": input_id,
                    "track": "agent_slots",
                    "status": "error",
                    "transcript": None,
                    "predicted_slots": [],
                    "error_type": f"{type(exc).__name__}: {exc}"[:200],
                    "raw_artifact_path": None,
                    "observed_final_state_path": None,
                }
            )
    out_dir.mkdir(parents=True, exist_ok=True)
    write_text_atomic(
        out_dir / "predictions.jsonl",
        "\n".join(json.dumps(r, ensure_ascii=False) for r in predictions) + "\n",
    )
    return {"rows": len(predictions)}


def human_control_wer_cer(
    asr_run_dir: Path, human_manifest: Path, out_path: Path
) -> dict[str, Any]:
    """Corpus-level WER/CER (sum errors / sum words), clean vs telephone."""

    import jiwer

    from voxentity_eu.contracts import AudioRecord

    manifest = read_jsonl(human_manifest, AudioRecord)
    truth = {a.audio_id: (a.transcript or "") for a in manifest}
    predictions = [
        json.loads(line)
        for line in (asr_run_dir / "predictions.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]

    def corpus_wer(rows, cer: bool) -> dict[str, Any]:
        refs, hyps = [], []
        missing = 0
        for p in rows:
            ref = truth.get(p["audio_id"])
            if ref is None:
                missing += 1
                continue
            if p["status"] != "ok" or p["transcript"] is None:
                hyp = ""
            else:
                hyp = p["transcript"]
            refs.append(ref)
            hyps.append(hyp)
        if cer:
            measure = jiwer.cer(reference=" ".join(refs), hypothesis=" ".join(hyps))
            denom = sum(len(r) for r in refs)
        else:
            # jiwer returns a dict with aggregated counts in recent versions
            out = jiwer.process_words(reference=refs, hypothesis=hyps)
            denom = out.hits + out.deletions + out.substitutions
            measure = out.wer
        return {
            "error_rate": measure if isinstance(measure, float) else float(measure),
            "denominator_units": denom,
            "utterances": len(refs),
            "missing_rows": missing,
        }

    clean_rows = [p for p in predictions if p["audio_id"].endswith("-clean")]
    tel_rows = [p for p in predictions if p["audio_id"].endswith("-tel")]
    report = {
        "wer_clean": corpus_wer(clean_rows, cer=False),
        "wer_telephone": corpus_wer(tel_rows, cer=False),
        "cer_clean": corpus_wer(clean_rows, cer=True),
        "cer_telephone": corpus_wer(tel_rows, cer=True),
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    write_text_atomic(out_path, json.dumps(report, ensure_ascii=False, indent=1))
    return report


def main() -> int:
    """Rebuild every extractor-dependent track from frozen ASR transcripts."""

    import shutil

    inputs = Path("data/inputs")
    for system in ("whisper-turbo", "voxtral-mini"):
        print(system, build_asr_slots_run(Path(f"runs/{system}"), inputs, Path(f"runs/{system}-slots")))
    gold, manifest = Path("data/generated/gold/scenarios.jsonl"), Path("data/generated/audio_manifest.jsonl")
    print("gold-extractor", build_gold_extractor_run(gold, manifest, inputs, Path("runs/gold-extractor")))
    print(
        "gold-written-extractor",
        build_gold_extractor_run(gold, manifest, inputs, Path("runs/gold-written-extractor"), "written_text"),
    )
    agent_dir = Path("runs/reference-agent")
    shutil.rmtree(agent_dir / "agent_store", ignore_errors=True)  # strict reset: fresh sessions
    frozen = Path("runs/whisper-turbo/predictions.jsonl")
    print("reference-agent", run_reference_agent(inputs, agent_dir, lambda: FrozenAsr(frozen)))
    print("extractor", EXTRACTOR_VERSION)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

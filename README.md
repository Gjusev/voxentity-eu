# VoxEntity-EU

Open evaluation of German and French spoken entity capture.

**Status: implemented and measured locally; not yet published externally.** The repository contains a working CPU/offline CLI, a 180-scenario synthetic corpus (360 paired audio files, automated-QA **provisional** — no human listening review yet), measured baselines (Whisper large-v3-turbo, Voxtral Mini via Kaggle), a reference agent with observable slot persistence, an independent FLEURS human-speech control, and reproducible scoring. No external site, dataset or Space has been published from this work yet; every public artifact referenced below exists only as a local file until the release gates pass.

The benchmark asks whether a system captures the exact name, telephone number, email address, calendar value, postal address or reference code spoken by a caller. Its main corpus is controlled synthetic speech. A separate, licensed human-speech control measures transfer limitations without requiring new speaker recruitment.

## Results (measured, test split)

Synthetic speech (Qwen3-TTS, two voices) in two conditions: clean 16 kHz and a
simulated telephone channel (band-pass, noise, G.711 A-law, 8 kHz). 120 test
scenarios × 2 conditions = 240 scored items per system. Corpus status:
automated QA only, **no human listening review yet**. Exact slot accuracy with
stratified bootstrap 95% CIs:

| system | exact slot accuracy | 95% CI |
| --- | --- | --- |
| written gold text → extractor (ceiling) | 90.8% | [87.5, 94.2] |
| Voxtral Mini 3B → extractor | 37.1% | [30.0, 43.8] |
| Whisper large-v3-turbo → extractor | 34.2% | [28.3, 40.4] |

- Whisper minus Voxtral: −2.9 pp [−7.1, +1.3], not a conclusive difference.
- Clean minus telephone, paired by scenario: Whisper +5.0 pp [+0.8, +10.0];
  Voxtral +4.2 pp [−0.8, +9.2], not conclusive.
- Emails and phone numbers are the weakest cells. French postal addresses are
  limited by the extractor itself (written-gold ceiling 20%), not by ASR.
- **The synthesizer matters.** The same test scenarios synthesized with a
  second TTS family (Piper) score +10.0 pp higher with Whisper (paired
  [+4.2, +15.4]); phone numbers rise from 15% to 55–70%. Absolute numbers
  above are conditional on Qwen3-TTS; emails stay near 0% with both.
- Human-speech control (FLEURS, 100 utterances per condition, likely seen in
  ASR training): Whisper WER 0.115 clean vs 0.221 telephone. Reported
  separately and not comparable with the synthetic numbers.

![Slot accuracy by cell](reports/figures/cell_accuracy.svg)

Full tables, error taxonomy and caveats are in [reports/report.md](reports/report.md).

Extension suites (separate data and reports; never merged into the core tables):

| suite | what it tests | headline (test, Whisper turbo) |
| --- | --- | --- |
| [Piper TTS](reports/ext-piper/report.md) | second TTS family, same scenarios | 44.2% vs 34.2% Qwen, paired +10.0 pp [+4.2, +15.4] |
| [Multi-turn](reports/ext-multiturn/report.md) | correction / confirmation across two turns | final state 42.2% [29.7, 54.7]; 0 stale; 19/19 when both turns heard right |
| [Code-switching](reports/ext-codeswitch/report.md) | English pieces in DE/FR speech | 31.2% [22.5, 38.8] vs 65.0% extractor ceiling |
An earlier extractor version (rex-2) supported a wrong "ASR bottleneck"
conclusion; the retraction is documented in
[IMPLEMENTATION_STATUS.md](IMPLEMENTATION_STATUS.md).

## Reproduce locally

```bash
uv venv --python 3.11 .venv && uv pip install --python .venv/Scripts/python.exe -r uv-core.lock -e ".[dev]"
.venv/Scripts/python.exe -m pytest -q                                  # offline suite
.venv/Scripts/python.exe -m voxentity_eu.cli doctor --profile local    # preflight
# from frozen ASR transcripts (CPU, no inference): tracks, scoring, comparison, report
.venv/Scripts/python.exe scripts/run_tracks.py
.venv/Scripts/python.exe scripts/score_all.py
.venv/Scripts/python.exe -m voxentity_eu.cli compare runs/scored/whisper-turbo-slots.json \
    runs/scored/voxtral-mini-slots.json --out runs/scored/system_comparison.json
.venv/Scripts/python.exe -m voxentity_eu.cli report --results runs/scored --out reports/report.md
```

`notebooks/reproduce/reproduce.ipynb` rescores the release bundle's frozen
predictions and checks that every summary is identical.

Inference profiles (Qwen3-TTS synthesis, Whisper, Voxtral) need the GPU extra and pinned revisions; see `IMPLEMENTATION_STATUS.md` for the exact runs behind every number.

## Implementation handoff

Start with [START_HERE.md](START_HERE.md), then follow [the implementation backlog](docs/09-implementation.md). Internal specifications are in Spanish; public-facing artifacts are in English.

| Specification | Purpose |
| --- | --- |
| [Product](docs/01-product.md) | Scope, deliverables, exclusions and honest claims |
| [Research](docs/02-research.md) | Primary sources, decisions, uncertainties |
| [Data and rights](docs/03-data.md) | Acquisition, synthetic corpus, human control, provenance |
| [Contracts](docs/04-contracts.md) | Records, predictions, manifests and normalization |
| [Evaluation](docs/05-evaluation.md) | Metrics, experiments, uncertainty and failure accounting |
| [Architecture](docs/06-architecture.md) | Package structure, CLI and voice-evals bridge |
| [Compute](docs/07-compute.md) | Kaggle, Hugging Face PRO, reproducibility |
| [Public release](docs/08-publication.md) | Dataset, demo, report and career evidence |
| [Implementation](docs/09-implementation.md) | Ordered tasks with acceptance criteria |
| [Validation](docs/10-validation.md) | Test matrix, release gates, risks |
| [Decisions](docs/11-decisions.md) | Fixed decisions, fallbacks, conditional extensions |

Measured results live in `reports/report.md` (regenerable offline from frozen predictions with `python scripts/score_all.py` and `voxentity report`). Model/dataset references are recorded in [research/artifacts.json](research/artifacts.json); resolved rights per asset in `data/generated/rights_registry.jsonl` and `DATA_LICENSE.md`.

The initial public target is 180 independent scenarios and 360 paired audio files. A second synthesis family, human control and real final-slot evaluation have separate gates. No ranking or production-reliability claim may be invented.

## Proposed public artifacts

- This independent GitHub project.
- A Hugging Face dataset with audio, labels and provenance.
- A CPU-friendly Space for browsing measured failures.
- Kaggle notebooks for generation and reproducible evaluation.
- A technical report with paired degradation measurements and limitations.

No remote has been created yet. Publication commands are prepared in [PUBLISHING.md](PUBLISHING.md) and have not been run.

# VoxEntity-EU

Open evaluation of German and French spoken entity capture.

**Status: implemented and measured locally; not yet published externally.** The repository contains a working CPU/offline CLI, a 180-scenario synthetic corpus (360 paired audio files, automated-QA **provisional** — no human listening review yet), measured baselines (Whisper large-v3-turbo, Voxtral Mini via Kaggle), a reference agent with observable slot persistence, an independent FLEURS human-speech control, and reproducible scoring. No external site, dataset or Space has been published from this work yet; every public artifact referenced below exists only as a local file until the release gates pass.

The benchmark asks whether a system captures the exact name, telephone number, email address, calendar value, postal address or reference code spoken by a caller. Its main corpus is controlled synthetic speech. A separate, licensed human-speech control measures transfer limitations without requiring new speaker recruitment.

## Reproduce locally

```bash
uv venv --python 3.11 .venv && uv pip install --python .venv/Scripts/python.exe -e ".[dev]"
.venv/Scripts/python.exe -m pytest -q                                  # offline suite
.venv/Scripts/python.exe -m voxentity_eu.cli doctor --profile local    # preflight
.venv/Scripts/python.exe -m voxentity_eu.cli score --gold data/generated/gold/scenarios.jsonl \
    --predictions runs/whisper-turbo-slots/predictions.jsonl \
    --manifest data/generated/audio_manifest.jsonl --out runs/scored/whisper-turbo-slots.json
.venv/Scripts/python.exe -m voxentity_eu.cli report --results runs/scored --out reports/report.md
```

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

No remote has been created as part of this planning handoff.

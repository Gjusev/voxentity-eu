# VoxEntity-EU

Open evaluation of German and French spoken entity capture.

**Status: implementation specification only.** No audio corpus, model results, working CLI, published dataset or hosted demo exists in this repository yet.

The benchmark asks whether a system captures the exact name, telephone number, email address, calendar value, postal address or reference code spoken by a caller. Its main corpus is controlled synthetic speech. A separate, licensed human-speech control measures transfer limitations without requiring new speaker recruitment.

## Implementation handoff

Start with [START_HERE.md](START_HERE.md), then follow [the implementation backlog](docs/09-implementation.md). Internal specifications are in Spanish; public-facing artifacts should be in English.

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

Model/dataset references are recorded in [research/artifacts.json](research/artifacts.json). They are research observations, not a tested dependency lock.

The initial public target is 180 independent scenarios and 360 paired audio files. A second synthesis family, human control and real final-slot evaluation have separate gates. No ranking or production-reliability claim may be invented.

## Proposed public artifacts

- This independent GitHub project.
- A Hugging Face dataset with audio, labels and provenance.
- A CPU-friendly Space for browsing measured failures.
- Kaggle notebooks for generation and reproducible evaluation.
- A technical report with paired degradation measurements and limitations.

No remote has been created as part of this planning handoff.

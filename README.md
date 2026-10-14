<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="docs/brand/logo-lockup-dark.png">
    <img src="docs/brand/logo-lockup-light.png" alt="VoxEntity-EU: a waveform inside a form-field slot, one bar out of place" width="540">
  </picture>
</p>

<p align="center">
  <a href="https://github.com/Gjusev/voxentity-eu/actions/workflows/ci.yml"><img src="https://github.com/Gjusev/voxentity-eu/actions/workflows/ci.yml/badge.svg" alt="CI"></a>
  <a href="https://huggingface.co/datasets/Gjusev/voxentity-eu"><img src="https://img.shields.io/badge/dataset-Hugging%20Face-ffcc4d" alt="Dataset on Hugging Face"></a>
  <a href="https://huggingface.co/spaces/Gjusev/voxentity-eu-results"><img src="https://img.shields.io/badge/demo-results%20browser-2a78d6" alt="Results browser"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/code-Apache--2.0-0b0b0b" alt="Code license Apache-2.0"></a>
  <img src="https://img.shields.io/badge/status-provisional-eb6834" alt="Status provisional">
</p>

A caller says `+33 6 05 36 23 71`. On a simulated phone line, Whisper wrote down
`+33 6 75 36 23 71`. The transcript reads fine and the phone number is still wrong.

VoxEntity-EU scores that: whether a speech system captures a dictated name, phone
number, email, date, postal address or reference code **exactly**, in German and
French, on clean audio and through a simulated telephone channel. One wrong
character fails the slot.

<p align="center">
  <a href="docs/media/voxentity-eu-demo.mp4"><img src="docs/media/voxentity-eu-hook.gif" alt="A dictated French phone number and Whisper's capture with one wrong digit; the slot fails" width="720"></a>
  <br><sub><a href="docs/media/voxentity-eu-demo.mp4">Watch the 21-second demo</a> · every value in it is a real output from the test set</sub>
</p>

> **Read this first.** The speech is synthetic (Qwen3-TTS), the telephone channel
> is simulated, and no human has listened to the clips yet (automated QA only), so
> the corpus is labelled provisional. Absolute numbers depend on the synthesizer;
> see the Piper result below.

## Results

120 test scenarios × 2 conditions (clean 16 kHz, simulated telephone 8 kHz) =
240 scored items per system. Exact slot accuracy, stratified bootstrap 95% CIs:

| system | exact slot accuracy | 95% CI |
| --- | --- | --- |
| correct written text → extractor (ceiling) | 90.8% | [87.5, 94.2] |
| Voxtral Mini 3B → extractor | 37.1% | [30.0, 43.8] |
| Whisper large-v3-turbo → extractor | 34.2% | [28.3, 40.4] |

- The two ASR systems are statistically indistinguishable: Whisper minus
  Voxtral is −2.9 pp [−7.1, +1.3].
- The simulated phone line costs Whisper 5 points (clean minus telephone
  +5.0 pp, [+0.8, +10.0]). Voxtral's drop is not conclusive (+4.2 pp, [−0.8, +9.2]).
- Emails fail almost everywhere (0 to 20% per language and system), and phone
  numbers reach only 10 to 25%. French postal addresses are limited by the
  extractor itself (ceiling 20%), not by ASR.
- When a second TTS family (Piper) voices the same scenarios, Whisper scores
  10 points higher (paired [+4.2, +15.4]) and phone numbers rise from 15% to 55
  to 70%. The absolute numbers above therefore depend on Qwen3-TTS.
- Human-speech control (FLEURS, 100 utterances per condition, probably seen in
  ASR training): Whisper WER 0.115 clean vs 0.221 telephone. Reported on its own,
  never mixed with the synthetic numbers.

![Exact slot accuracy by language and entity cell, with the extractor ceiling](reports/figures/cell_accuracy.svg)

Full tables, error taxonomy and caveats: [reports/report.md](reports/report.md).

### Extension suites

Each one has its own data and report and never enters the tables above.

| suite | question | result (test, Whisper turbo) |
| --- | --- | --- |
| [Piper TTS](reports/ext-piper/report.md) | does a second TTS family change the score? | 44.2% vs 34.2% with Qwen, paired +10.0 pp [+4.2, +15.4] |
| [Multi-turn](reports/ext-multiturn/report.md) | does a correction in turn two reach the stored value? | final state 42.2% [29.7, 54.7]; 0 stale values; 19/19 when both turns were heard right |
| [Code-switching](reports/ext-codeswitch/report.md) | English pieces inside German and French speech | 31.2% [22.5, 38.8] vs a 65.0% extractor ceiling |
| [Voices](reports/ext-voices/report.md) | is the voice or the scenario harder? | vivian vs ryan +0.8 pp [−3.3, +5.0]; core voice gap ≈ 3 pp scenario + 7 pp voice |
| [Spanish](reports/ext-es/report.md) | the same six entity types in es-ES | 50.8% [41.7, 60.0] vs a 96.7% extractor ceiling (different scenarios, not comparable to DE/FR) |

An earlier extractor version (rex-2) led to a wrong "ASR bottleneck" conclusion.
The retraction and what was fixed are documented in
[IMPLEMENTATION_STATUS.md](IMPLEMENTATION_STATUS.md) and [CHANGELOG.md](CHANGELOG.md).

## Data and demo

- Dataset with audio: [huggingface.co/datasets/Gjusev/voxentity-eu](https://huggingface.co/datasets/Gjusev/voxentity-eu)
  (release bundle with gold, manifests, predictions and checksums, plus 1,864 WAV files).
- Results browser: [huggingface.co/spaces/Gjusev/voxentity-eu-results](https://huggingface.co/spaces/Gjusev/voxentity-eu-results)
  (CPU; filter by language, entity, condition and system; listen to clean and telephone audio).
- Verified URLs and revisions: [RELEASE_MANIFEST.json](RELEASE_MANIFEST.json).

## Reproduce on a CPU

You need no GPU and no network: everything below rescores frozen transcripts.

```bash
uv venv --python 3.11
uv pip install -r uv-core.lock -e ".[dev]"
uv run pytest -q                                   # offline test suite
uv run python scripts/run_tracks.py                # extractor tracks from frozen transcripts
uv run python scripts/score_all.py                 # scoring
uv run python scripts/release_gates.py             # run integrity + byte-identical report regeneration
```

`notebooks/reproduce/reproduce.ipynb` rescores the release bundle and checks every
summary against the published one. Synthesis and ASR inference need the GPU extras
and the pinned model revisions listed in [IMPLEMENTATION_STATUS.md](IMPLEMENTATION_STATUS.md).

## Evaluate your own system

Run your system over the exported inputs only (opaque ids, no gold), write one
prediction row per input, and score it with `voxentity score`. Failed rows stay in
the denominator. Details and the submission template: [CONTRIBUTING.md](CONTRIBUTING.md).

## Rights

Code: Apache-2.0. Annotations: CC-BY-4.0. Synthetic audio is published by the
project owner's recorded decision on the model licenses (not a legal opinion);
the French Piper voice carries the SIWIS CC BY 4.0 attribution; FLEURS audio is
CC-BY-4.0 with modifications flagged. Details: [DATA_LICENSE.md](DATA_LICENSE.md),
[THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md). Rights or takedown requests:
open an issue. Demo music: ende.app, CC BY 4.0.

## Project documentation

The design specifications are in Spanish; everything public-facing is in English.

| document | covers |
| --- | --- |
| [Product](docs/01-product.md) | scope, deliverables, exclusions, honest claims |
| [Research](docs/02-research.md) | primary sources, decisions, open questions |
| [Data and rights](docs/03-data.md) | synthetic corpus, human control, provenance |
| [Contracts](docs/04-contracts.md) | records, predictions, manifests, normalization |
| [Evaluation](docs/05-evaluation.md) | metrics, uncertainty, failure accounting |
| [Architecture](docs/06-architecture.md) | package, CLI, voice-evals bridge |
| [Validation](docs/10-validation.md) | test matrix and release gates |
| [Decisions](docs/11-decisions.md) | fixed decisions and fallbacks |
| [Publishing](PUBLISHING.md) and [launch](docs/launch/LAUNCH.md) | how the release was made and verified |

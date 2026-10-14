# Contributing to VoxEntity-EU

## Ground rules

- **Never feed gold to evaluated systems.** Predictions and truth use separate
  access paths: inference consumes the exported inputs directory (opaque ids,
  no canonical values, no written text). If your change leaks `scenarios.jsonl`
  into an adapter, tests will fail it.
- **Never replace a real model run with a fixture.** Fixtures are for software
  regression only (docs/10). Measured results come from measured runs; failed
  or partial runs keep their denominators.
- **Synthetic and human-control corpora stay separate.** FLEURS rows never
  join synthetic scores.

## Adding cases

Cases are generated deterministically from `src/voxentity_eu/corpus/` pools and
templates. To add cases: extend pools/templates, regenerate with
`voxentity corpus build`, and make sure `voxentity corpus validate` passes
(counts, split separation, correction semantics). Values must be original
constructions; emails use example.com/example.org; no scraped personal data;
no claims that fictional values are verified non-existent.

## Adding models

Implement an `Asr` adapter (see `adapters/base.py`), pin the model revision in
`SYSTEMS`, and run through the exported inputs. Smoke-test one clip per
locale before a full run. Report the run as system+extractor, never ASR alone.

## Submitting a system's predictions (no code needed)

Run your system over the exported inputs only (`data/inputs/inputs.jsonl` plus
audio; opaque ids, no gold), write one `predictions.jsonl` row per input in the
contract of `docs/04-contracts.md`, and score it with
`voxentity score --gold data/generated/gold/scenarios.jsonl --predictions <file>
--manifest data/generated/audio_manifest.jsonl --out <scored.json>`. Open a
"Submit a system" issue with the predictions, the scored file and the exact
model id + revision. Missing or failed rows stay in the denominator.

## Corrections and policies

Normalization and extractor rules are versioned (currently `norm-2`, `rex-4`; history in CHANGELOG.md). Changes
require a new version and re-freezing on dev before test comparisons. Gold is
never edited to match a prediction.

## Running tests

```
python -m pytest          # offline CPU suite, no torch/network needed
python -m ruff check .
python scripts/check_links.py
python scripts/release_gates.py   # G4 run integrity + G6 offline regeneration
```

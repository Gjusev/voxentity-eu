---
language:
  - de
  - fr
  - es
license:
  - apache-2.0
  - cc-by-4.0
multilinguality:
  - multilingual
size_categories:
  - n<1K
task_categories:
  - automatic-speech-recognition
  - speech-processing
tags:
  - spoken-entity-capture
  - telephone-channel
  - evaluation
---

# VoxEntity-EU dataset card

## Composition

- **synthetic_core**: 180 independent scenarios (12 cells: 2 locales × 6 entity
  types × 15 cases), two acoustic conditions each → 360 paired audio files.
  Splits: 60 dev / 120 test with disjoint values and template families.
  Difficulty mix per cell: 5 direct, 4 orthographic/phonetic, 3
  segmented/spelled, 3 containing a within-utterance self-correction.
- **human_control**: 50 FLEURS test rows per language (deterministic selection
  by `sha256(fleurs:<locale>:<id>)`), clean + simulated-telephone versions.
  Kept strictly separate from synthetic scores.

Entity types: person_name, phone, email, calendar_value, postal_address,
reference_code. Every case has exactly one final target value; correction
cases additionally record the superseded previous mention.

## Source and generation

- Synthetic speech: Qwen3-TTS-12Hz-0.6B-CustomVoice (revision
  `85e237c12c027371202489a0ec509ded67b5e4b5`), predefined voices `serena` and
  `dylan`, fp32 on a GTX 1080, sdpa attention. Masters are frozen at 24 kHz;
  clean is the peak-normalized 16 kHz PCM16 derivation; telephone passes the
  documented simulated channel (Butterworth-6 300–3400 Hz → 8 kHz → seeded
  Gaussian noise at 20 dB active-speech SNR → G.711 A-law round trip).
- The telephone condition is a **simulation**, not a PSTN call, and does not
  represent every codec.
- Human control: FLEURS de_de / fr_fr test split at the pinned revision,
  transformed as flagged in DATA_LICENSE.md.

## Labels

Per scenario: written text, exact synthesis text, canonical value, accepted
variants, mention text, difficulty tags, template family, split, seed, plus
per-audio provenance (synthesis and transform records with hashes).

## QA status

- Automated QA: decodability, mono, clipping fraction < 0.1%, energy, duration
  1–45 s, abrupt-ending alerts. ASR disagreement produces alerts only, never
  exclusions.
- Human listening review status is tracked in IMPLEMENTATION_STATUS.md; until
  completed, the corpus is labeled `automated-QA/provisional`, not `verified`.

## Splits

`dev` exists to freeze extractors and policies; `test` is the reporting split.
Public availability of test references may contaminate future ASR models.

## Extension suites (separate configs, never merged into the core tables)

Under `ext/<suite>/` (gold, manifests, provenance) with their own reports:

- `codeswitch`: 56 DE/FR scenarios with English separators/digits, NATO
  spelling in German and non-DE/FR names.
- `multiturn`: 48 DE/FR two-turn cases (correction, confirmation, repeat);
  scored on the agent's persisted final state.
- `voices`: the 120 core test scenarios re-voiced by two more Qwen3-TTS voices.
- `piper`: the 120 core test scenarios synthesized by a second TTS family
  (Piper; French voice trained on CC BY 4.0 SIWIS data, attribution required).
- `es`: 90 Spanish scenarios with the core entity types and difficulty mix.

All are synthetic, with the simulated telephone channel and automated QA only.

## Licenses and attribution

See DATA_LICENSE.md and THIRD_PARTY_NOTICES.md: annotations CC-BY-4.0;
synthetic audio rights conditional on the generator's output terms; FLEURS
audio CC-BY-4.0 with modifications flagged.

## Intended use and limitations

- Intended: evaluation of exact spoken-entity capture (transcription,
  extraction, and persisted-slot perspectives) in German and French; Spanish
  as a separate extension suite.
- NOT intended: claims about real caller populations, causal hiring impact,
  production readiness, or generalization to unseen human accents. The corpus
  is small by design (a diagnostic, not a leaderboard); null results are
  published as results.
- Absolute accuracies depend on the synthesizer: the same test scenarios
  synthesized by a second TTS family (Piper) scored +10 pp higher with the same
  ASR. Treat numbers as conditional on Qwen3-TTS, not as properties of speech.
- The 360 files are 180 paired observations, not independent samples;
  uncertainty is reported with cluster bootstrap over scenario ids.

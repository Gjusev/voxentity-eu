# Product and scope

## Question

Does a system preserve the exact value a user communicates in German or French, including a correction, when the audio passes through a simulated telephone channel?

Three distinct outcomes: transcription; entity extraction from text; the final state actually stored by an agent. None substitutes for the others.

## Audience

Voice agent engineers and teams that receive bookings, delivery addresses or support references. For hiring, the asset demonstrates experimental design, data work, model adaptation and debugging of observable failures.

## Mandatory deliverables

- Installable package and CLI with offline scoring.
- Main synthetic dataset: 180 scenarios, two conditions, 360 audios.
- Gold, metadata and provenance in JSONL/Parquet.
- Two open ASR baselines from different families.
- Shared extraction over gold and predicted transcripts.
- Reference agent with local slot storage and instrumentation.
- Exporter for voice-evals fixtures, without modifying that project.
- Independent human control with FLEURS or a verifiable explanation of its blockage.
- Kaggle generation notebook; evaluation notebook; CPU reproduction notebook.
- CPU Space with precomputed errors.
- Report with uncertainty, denominators, failures and audible examples.
- Dataset card, rights report and publication commands.

## Explicit extended scope

A second TTS family for synthesizer sensitivity; up to two accessible provider adapters; cross-turn corrections; DE/EN or FR/EN code-switching; Spanish. Only after the core, in separate suites with their own IDs and results.

The initial version already includes corrections within an utterance. It does not measure interruptions or end-of-turn detection. A scripted reference policy is not presented as a commercial agent nor ranked alongside them without stating its nature.

## Size and claims

The 360 files represent 180 paired cases, not 360 independent observations. Each language × entity cell has 15 scenarios. This is a small diagnostic, with no guaranteed power for small differences.

There is no guarantee that a model fails more in one condition. A null result is published too. No headlines are set before measuring.

## Target licenses

Original code: Apache-2.0. Original annotations: CC-BY-4.0. Audio: license per source with verified rights; never apply the code license to audios automatically. Prepare LICENSE, DATA_LICENSE.md and THIRD_PARTY_NOTICES during implementation with official texts.

# Data and audio rights (per component)

This file separates rights per component; the code license (Apache-2.0, see
LICENSE) does NOT automatically apply to data or audio. Every redistribution
status below traces to the rights registry (`data/generated/rights_registry.jsonl`),
where each entry carries URL, revision, license text URL and review status.

## Original annotations (gold, metadata, manifests)

- License: **CC-BY-4.0** (text in `licenses/CC-BY-4.0.txt`).
- Rights holder: VoxEntity-EU contributors.
- Covers: scenario definitions, canonical values, difficulty tags, corpus
  manifests, transform/synthesis provenance records, scoring outputs.

## Synthetic audio (Qwen3-TTS generated)

- Generator: Qwen/Qwen3-TTS-12Hz-0.6B-CustomVoice, revision
  `85e237c12c027371202489a0ec509ded67b5e4b5`, declared model license Apache-2.0
  (S03 in the rights registry).
- Status: **provisional / conditional**. A model license alone does not prove
  unrestricted rights over all generated audio. Until the voice-output terms of
  the served model revision are verified end-to-end, synthetic WAV files are
  distributed as part of the public dataset **only after** the corresponding
  rights-registry entry moves to `verified`; otherwise this repository ships
  the generation pipeline, text corpus and metadata so anyone can regenerate
  audio locally under their own acceptance of the model terms.
- Voices: predefined speakers `serena` and `dylan` selected via the official
  API; no cloned or personally recorded voices (decision D03).

## Extension-suite audio (data/ext/*)

- `codeswitch`, `multiturn`, `voices`: Qwen3-TTS, same terms and the same
  provisional / conditional status as the core synthetic audio above (voices
  serena, dylan, vivian, ryan; predefined speakers only).
- `piper`: Piper voices (THIRD_PARTY_NOTICES.md). The French voice's training
  data is CC-BY 4.0 (SIWIS): any redistributed `piper` French audio carries that
  attribution. Status: **conditional**, same rule as above: audio ships only
  after the rights-registry entry is verified; otherwise the pipeline and text
  are the distributed artifacts.

## Human-control audio (FLEURS)

- Source: google/fleurs, revision `70bb2e84b976b7e960aa89f1c648e09c59f894dd`,
  CC-BY-4.0 (S04).
- Attribution: Google (FLEURS authors). Modifications flagged per CC-BY-4.0
  §3(b): clean copies are peak-normalized and resampled to 16 kHz PCM16;
  telephone copies pass the documented simulated-channel recipe. Original
  bytes are preserved alongside (`*-orig.wav`). FLEURS row ids and the test
  split are retained.

## Software dependencies

- See THIRD_PARTY_NOTICES.md. Weights are never redistributed; adapters
  download pinned revisions from their official repositories.

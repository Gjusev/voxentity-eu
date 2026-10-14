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
- Status: **distributed by owner decision** (registry S03 `verified`). Basis:
  Apache-2.0 at the pinned revision on both the model card and the code
  repository, with no usage or output-ownership terms found; predefined voices
  only; invented values. This records the project owner's decision on that
  evidence and is **not a legal opinion**; a model license alone does not prove
  rights over every generated output. Audio is released under CC-BY-4.0 as part
  of the dataset, to the extent the project can grant it. Takedown or rights
  concerns: open an issue on GitHub `Gjusev/voxentity-eu`; affected files are
  removed and the release notes record the removal.
- Quality: automated QA only, no human listening review. An automated alert
  (both independent ASR systems far from both the written and the spoken text)
  flags 7 of 180 clean core clips as likely synthesis failures; unverified by
  ear (`scripts/tts_alert.py`).
- Voices: predefined speakers `serena` and `dylan` selected via the official
  API; no cloned or personally recorded voices (decision D03).

## Extension-suite audio (data/ext/*)

- `codeswitch`, `multiturn`, `voices`, `es`: Qwen3-TTS, same terms and the same
  owner-decision status as the core synthetic audio above (voices serena,
  dylan, vivian, ryan; predefined speakers only).
- `piper`: Piper voices (THIRD_PARTY_NOTICES.md; registry S17). The French
  voice's training data is CC BY 4.0 (SIWIS): the French `piper` audio carries
  that attribution (Yamagishi, Honnet, Garner, Lazaridis 2017,
  doi:10.7488/ds/1705). Distributed by owner decision, same terms and takedown
  route as above.

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

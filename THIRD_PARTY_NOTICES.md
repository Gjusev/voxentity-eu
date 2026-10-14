# Third-party notices

VoxEntity-EU integrates the following external components. Weights are never
redistributed by this project; the adapters fetch pinned revisions from the
official repositories. Declared licenses were read from the official model
cards / repositories at the revisions pinned below (rights registry:
`data/generated/rights_registry.jsonl`).

## Qwen3-TTS-12Hz-0.6B-CustomVoice (S03)

- Source: https://huggingface.co/Qwen/Qwen3-TTS-12Hz-0.6B-CustomVoice
- Revision: 85e237c12c027371202489a0ec509ded67b5e4b5
- Declared license: Apache-2.0 (model card)
- Used for: synthetic speech generation with predefined voices.
- Runtime package: `qwen-tts` (https://github.com/QwenLM/Qwen3-TTS).
- Note: the model license does not by itself settle output-audio rights; see
  DATA_LICENSE.md.

## Whisper large-v3-turbo (S05)

- Source: https://huggingface.co/openai/whisper-large-v3-turbo
- Revision: 41f01f3fe87f28c78e2fbf8b568835947dd65ed9
- Declared license: MIT (model card)
- Used for: ASR baseline (track A) and the reference agent's perception.

## Voxtral Mini 3B (S06)

- Source: https://huggingface.co/mistralai/Voxtral-Mini-3B-2507
- Revision: 3060fe34b35ba5d44202ce9ff3c097642914f8f3
- Declared license: Apache-2.0 (model card)
- Used for: second ASR family baseline (track A).

## FLEURS (S04)

- Source: https://huggingface.co/datasets/google/fleurs
- Revision: 70bb2e84b976b7e960aa89f1c648e09c59f894dd
- License: CC-BY-4.0; attribution and modification flagging obligations are
  documented in DATA_LICENSE.md and the dataset card.
- Used for: independent human-speech control; never mixed into synthetic
  scores.

## Piper voices (extension suite `piper`, second TTS family)

- Source: https://huggingface.co/rhasspy/piper-voices (repo tag MIT)
- Revision: c10ece1aade47bb51c153c893d14e5bf8e5b7117; `.onnx` SHA-256 pinned in
  `src/voxentity_eu/ext/piper_tts.py`.
- `de_DE-thorsten-medium`: trained on Thorsten-Voice
  (https://github.com/thorstenMueller/Thorsten-Voice), dataset license CC0.
- `fr_FR-siwis-medium`: trained on the SIWIS French Speech Synthesis Database
  (University of Edinburgh, https://datashare.is.ed.ac.uk/handle/10283/2353),
  dataset license CC BY 4.0 (verified in the dataset's end-user licence file).
  Attribution: Yamagishi, J.; Honnet, P.-E.; Garner, P.; Lazaridis, A. (2017).
  The SIWIS French Speech Synthesis Database [dataset]. University of Edinburgh,
  CSTR. https://doi.org/10.7488/ds/1705
- Runtime: `piper-tts` 1.8.0 (OHF-Voice/piper1-gpl, GPL-3.0-or-later), run as an
  external tool from an isolated virtual environment; not a dependency of this
  package and not redistributed. Gate and exclusions: research/second-tts-gate.md.

## voice-evals (S16)

- Source: https://github.com/Gjusev/voice-evals
- Commit inspected: 3f6f9dd6412cbbaf8842405d6444fb2d74b8790e (local checkout)
- License: Apache-2.0 (LICENSE at the pinned commit, confirmed against the raw
  file and the GitHub license API).
- Integration: optional export adapter producing `FixtureCallerVoice`-compatible
  manifests; the upstream repository is never modified and nothing from it is
  redistributed in the release bundle. The integration stays optional and
  isolated (core scoring works without it).

## Demo video and brand assets

Used in `brag-output/composition/` and `brag-output/social-4x5/` (the demo sources) and `docs/brand/`, `docs/media/`:

- IBM Plex Sans and IBM Plex Mono (IBM), SIL Open Font License 1.1, from Google
  Fonts; bundled as woff2 for the offline render.
- Music: "Happy Beats / Business Moves" vol. 12 by ende.app, CC BY 4.0
  (https://ende.app/en/standard-license); credited in the video.
- Sound effects: Kenney.nl, CC0 1.0 (public domain).
- GSAP 3.14.2 (GreenSock), under the GSAP standard "no charge" license, used to
  animate the demo composition; rendered with HyperFrames.

## Python dependencies

Core: pydantic, numpy, scipy, soundfile, jiwer. Optional profiles: torch,
transformers, accelerate, qwen-tts, huggingface_hub, datasets, librosa,
gradio, pandas, pyarrow. Exact pins live in the per-profile lock files.

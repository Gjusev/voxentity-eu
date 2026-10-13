# Gate: second TTS family (P7)

Status: **conditional — not executed.** The core release does not depend on it
(docs/11: without a second family, the main analysis stands with an explicit
limitation).

Purpose (docs/03): re-synthesize the same 180 scenarios with an unrelated TTS
family to see whether ASR/entity errors track the synthesizer. It is a separate
analysis on the same cases, never extra statistical independence.

## Candidate: Piper (VITS, CPU, fixed voices, no cloning)

Verified at source (Hugging Face `rhasspy/piper-voices`, revision
`c10ece1aade47bb51c153c893d14e5bf8e5b7117`, repo tag MIT):

| voice | locale | training data | data license (MODEL_CARD) | verdict |
| --- | --- | --- | --- | --- |
| `de_DE-thorsten-medium` | de-DE | Thorsten-Voice | CC0 | usable |
| `fr_FR-siwis-medium` | fr-FR | SIWIS (Univ. Edinburgh datashare 10283/2353) | CC-BY 4.0 | usable with attribution |
| `fr_FR-upmc-medium` | fr-FR | MaryTTS upmc-pierre | CC-BY-SA 4.0 | **excluded**: share-alike could attach to generated audio and the dataset |

Runtime: the original `rhasspy/piper` code (MIT) was archived on 2025-10-06;
development moved to `OHF-Voice/piper1-gpl`, whose name indicates GPL (license
not yet verified at source). Prefer running the pinned ONNX voice files with
`onnxruntime` from an isolated optional extra, so no GPL code enters the core.

## Open conditions before running

1. Rights in generated audio: a model or dataset license is not proof of rights
   in every output (AGENTS.md). Record per voice in `rights_registry.jsonl` as
   `conditional` with attribution text (SIWIS: CC-BY 4.0 credit) before any
   redistribution.
2. Voice coverage: one voice per locale versus two Qwen voices; report it as a
   limitation, not a balanced comparison.
3. Pin file hashes of each `.onnx` / `.onnx.json` at the revision above.
4. Same QA gates (automated + listening) as the Qwen corpus; no filtering on ASR
   results.
5. Network access to download weights (unavailable in the current sandbox).

## Excluded earlier (docs/02)

- MMS-TTS German (S14): non-commercial model license.
- Chatterbox (S13): cloning-oriented; unresolved voice attribution.

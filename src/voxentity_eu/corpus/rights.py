"""Rights registry: per-source license chain and review status (docs/03 §F)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ..contracts import RightsEntry

# Registered sources; review_status reflects evidence collected so far.
# "conditional" = declared license seen on the official page/model card but the
# full chain (training data -> checkpoint -> generated audio) not yet audited.
DEFAULT_REGISTRY: list[dict[str, Any]] = [
    {
        "source_id": "S03",
        "url": "https://huggingface.co/Qwen/Qwen3-TTS-12Hz-0.6B-CustomVoice",
        "revision": "85e237c12c027371202489a0ec509ded67b5e4b5",
        "declared_license": "apache-2.0",
        # the HF repo at this revision ships no LICENSE file; the text lives in the code repo
        "license_url": "https://github.com/QwenLM/Qwen3-TTS/blob/main/LICENSE",
        "rights_holder": "Alibaba (Qwen team)",
        "transformations": "text-to-speech synthesis with predefined voices",
        "redistribution": "conditional",
        "review_status": "conditional",
        "notes": "Checked: model card at this revision declares apache-2.0 and states no "
        "usage restriction or output-ownership term; QwenLM/Qwen3-TTS is Apache-2.0 with no "
        "extra terms in its README. A model license still does not by itself prove rights "
        "over all generated audio, so audio redistribution stays closed until the project "
        "owner records an explicit decision.",
    },
    {
        "source_id": "S05",
        "url": "https://huggingface.co/openai/whisper-large-v3-turbo",
        "revision": "41f01f3fe87f28c78e2fbf8b568835947dd65ed9",
        "declared_license": "mit",
        "license_url": "https://huggingface.co/openai/whisper-large-v3-turbo/blob/main/LICENSE",
        "rights_holder": "OpenAI",
        "transformations": "inference only (transcription); no redistribution of weights",
        "redistribution": "allowed",
        "review_status": "verified",
        "notes": "Used as ASR baseline; outputs are our own measurements.",
    },
    {
        "source_id": "S06",
        "url": "https://huggingface.co/mistralai/Voxtral-Mini-3B-2507",
        "revision": "3060fe34b35ba5d44202ce9ff3c097642914f8f3",
        "declared_license": "apache-2.0",
        "license_url": "https://huggingface.co/mistralai/Voxtral-Mini-3B-2507/blob/main/LICENSE",
        "rights_holder": "Mistral AI",
        "transformations": "inference only (transcription); no redistribution of weights",
        "redistribution": "allowed",
        "review_status": "verified",
        "notes": "Second ASR family; outputs are our own measurements.",
    },
    {
        "source_id": "S04",
        "url": "https://huggingface.co/datasets/google/fleurs",
        "revision": "70bb2e84b976b7e960aa89f1c648e09c59f894dd",
        "declared_license": "cc-by-4.0",
        "license_url": "https://creativecommons.org/licenses/by/4.0/",
        "rights_holder": "Google (FLEURS authors)",
        "transformations": "selective download de_de/fr_fr test split; telephone-channel "
        "simulation applied to derived copies; originals preserved",
        "redistribution": "allowed",
        "review_status": "verified",
        "notes": "CC-BY-4.0 requires attribution and flagging modifications; human_control "
        "exports keep external_row_id and attribution.",
    },
    {
        "source_id": "S16",
        "url": "https://github.com/Gjusev/voice-evals",
        "revision": "3f6f9dd6412cbbaf8842405d6444fb2d74b8790e",
        "declared_license": "apache-2.0",
        "license_url": "https://github.com/Gjusev/voice-evals/blob/main/LICENSE",
        "rights_holder": "Gjusev",
        "transformations": "export adapter only; voice-evals repo untouched",
        "redistribution": "allowed",
        "review_status": "verified",
        "notes": "Checked: LICENSE at the pinned revision is Apache-2.0 (raw file and "
        "GitHub license API). Nothing from voice-evals is redistributed in the "
        "bundle; this project ships only its own export adapter.",
    },
]


def build_registry() -> list[RightsEntry]:
    return [RightsEntry.model_validate(entry) for entry in DEFAULT_REGISTRY]


def write_registry(out_path: Path | str) -> list[RightsEntry]:
    entries = build_registry()
    payload = "\n".join(e.model_dump_json() for e in entries) + "\n"
    from ..provenance import write_text_atomic

    write_text_atomic(out_path, payload)
    return entries

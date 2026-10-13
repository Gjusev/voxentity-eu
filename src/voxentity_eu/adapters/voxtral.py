"""Voxtral Mini 3B baseline (S06): audio+instruction model, transcription route.

Runs where VRAM allows (Kaggle T4/P100 in bf16, or CPU slowly); the adapter
records backend and precision honestly. Transcription prompt is fixed; no
entity hints.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ..commands import MissingDependency
from .base import Asr, AsrResult

MODEL_ID = "mistralai/Voxtral-Mini-3B-2507"
MODEL_REVISION = "3060fe34b35ba5d44202ce9ff3c097642914f8f3"
TRANSCRIBE_PROMPTS = {
    "de-DE": "Transkribiere dieses Audio wörtlich. Gib nur den Text aus.",
    "fr-FR": "Transcris cet audio littéralement. Donne uniquement le texte.",
}


class VoxtralMini(Asr):
    name = "voxtral-mini-3b"

    def __init__(self, device: str = "cuda:0", dtype: str = "bfloat16") -> None:
        self.device = device
        self.dtype = dtype
        self._model = None
        self._processor = None

    def load(self) -> None:
        if self._model is not None:
            return
        try:
            import torch
            from transformers import AutoProcessor, VoxtralForConditionalGeneration
        except ImportError as exc:
            raise MissingDependency(f"transformers>=4.53 unavailable: {exc}") from exc
        dtype = getattr(torch, self.dtype)
        self._processor = AutoProcessor.from_pretrained(MODEL_ID, revision=MODEL_REVISION)
        self._model = VoxtralForConditionalGeneration.from_pretrained(
            MODEL_ID, revision=MODEL_REVISION, torch_dtype=dtype, device_map=self.device
        )
        self._model.eval()

    def transcribe(self, audio_path: str, locale: str, **config: Any) -> AsrResult:
        import torch

        self.load()
        prompt = TRANSCRIBE_PROMPTS[locale]
        conversation = [
            {
                "role": "user",
                "content": [
                    {"type": "audio", "audio_url": str(Path(audio_path).resolve())},
                    {"type": "text", "text": prompt},
                ],
            }
        ]
        inputs = self._processor.apply_chat_template(
            conversation, add_generation_prompt=True, return_tensors="pt"
        )
        inputs = {k: (v.to(self._model.device) if hasattr(v, "to") else v) for k, v in inputs.items()}
        with torch.no_grad():
            out = self._model.generate(
                **inputs,
                do_sample=False,
                max_new_tokens=config.get("max_new_tokens", 512),
            )
        if hasattr(out, "sequences"):
            tokens = out.sequences
        else:
            tokens = out
        text = self._processor.decode(tokens[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True)
        return AsrResult(status="ok", transcript=text.strip(), raw={"model": MODEL_ID})

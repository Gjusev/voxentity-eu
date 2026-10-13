"""Whisper large-v3-turbo baseline (S05): pinned revision, explicit language.

No timestamps, no initial_prompt (entities must not be hinted), greedy
decoding frozen for the release.
"""

from __future__ import annotations

from typing import Any

from ..commands import MissingDependency
from .base import Asr, AsrResult

MODEL_ID = "openai/whisper-large-v3-turbo"
MODEL_REVISION = "41f01f3fe87f28c78e2fbf8b568835947dd65ed9"
WHISPER_LANGUAGES = {"de-DE": "german", "fr-FR": "french", "es-ES": "spanish"}


class WhisperTurbo(Asr):
    name = "whisper-large-v3-turbo"

    def __init__(self, device: str = "cuda:0", dtype: str = "float16") -> None:
        self.device = device
        self.dtype = dtype
        self._model = None
        self._processor = None

    def load(self) -> None:
        if self._model is not None:
            return
        try:
            import torch
            from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor
        except ImportError as exc:
            raise MissingDependency(f"transformers/torch unavailable: {exc}") from exc
        dtype = getattr(torch, self.dtype)
        self._processor = AutoProcessor.from_pretrained(MODEL_ID, revision=MODEL_REVISION)
        self._model = AutoModelForSpeechSeq2Seq.from_pretrained(
            MODEL_ID, revision=MODEL_REVISION, torch_dtype=dtype
        ).to(self.device)
        self._model.eval()

    def transcribe(self, audio_path: str, locale: str, **config: Any) -> AsrResult:
        import librosa  # noqa: F401  (ensures the audio backend import error surfaces early)
        import torch

        self.load()
        import librosa as lb

        language = WHISPER_LANGUAGES[locale]
        audio, sr = lb.load(audio_path, sr=16000, mono=True)
        inputs = self._processor(
            audio, sampling_rate=16000, language=language, return_tensors="pt"
        )
        features = inputs.input_features.to(
            self.device, next(self._model.parameters()).dtype
        )
        with torch.no_grad():
            predicted_ids = self._model.generate(
                features,
                language=language,
                task="transcribe",
                do_sample=False,
                num_beams=1,
                **{k: v for k, v in config.items() if k in ("max_new_tokens", "temperature")},
            )
        text = self._processor.batch_decode(predicted_ids, skip_special_tokens=True)[0]
        return AsrResult(status="ok", transcript=text.strip(), raw={"model": MODEL_ID})

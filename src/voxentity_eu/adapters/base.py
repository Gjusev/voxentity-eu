"""Backend-agnostic system interfaces (docs/06 §Interfaces)."""

from __future__ import annotations

import abc
from dataclasses import dataclass, field
from typing import Any


@dataclass
class AsrResult:
    status: str  # ok | error | timeout | unsupported
    transcript: str | None = None
    error_type: str | None = None
    raw: dict[str, Any] = field(default_factory=dict)


class Asr(abc.ABC):
    """transcribe(audio, locale, config) -> transcript/status; no gold params."""

    name: str = "asr"

    @abc.abstractmethod
    def load(self) -> None: ...

    @abc.abstractmethod
    def transcribe(self, audio_path: str, locale: str, **config: Any) -> AsrResult: ...


@dataclass
class SlotResult:
    status: str  # ok | unsupported_parse | empty
    slots: list[dict[str, str]] = field(default_factory=list)
    raw: dict[str, Any] = field(default_factory=dict)


class SlotExtractor(abc.ABC):
    name: str = "extractor"

    @abc.abstractmethod
    def extract(self, transcript: str, requested_type: str, locale: str) -> SlotResult: ...

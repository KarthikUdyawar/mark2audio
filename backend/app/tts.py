"""TTS engine interface + deterministic fake (tests, demo without model weights)."""

import os
from dataclasses import dataclass
from typing import Protocol

import numpy as np
import numpy.typing as npt

from app.config import Settings
from app.errors import AppError

SPEED_RANGE = (0.8, 1.2)


@dataclass(frozen=True)
class Voice:
    id: str
    name: str
    language: str


@dataclass(frozen=True)
class Audio:
    samples: npt.NDArray[np.float32]  # mono, -1..1
    rate: int


class TtsEngine(Protocol):
    def voices(self) -> list[Voice]: ...

    def synthesize(self, text: str, voice_id: str, speed: float, language: str) -> Audio: ...


class FakeTts:
    """Sine tone whose length follows the text length. No model needed."""

    RATE = 24000

    def voices(self) -> list[Voice]:
        return [Voice("fake_a", "Fake A", "en-us")]

    def synthesize(self, text: str, voice_id: str, speed: float, language: str) -> Audio:
        if voice_id not in {v.id for v in self.voices()}:
            raise AppError("VOICE_NOT_FOUND", "Voice is not installed.")
        seconds = max(0.1, len(text) * 0.02 / speed)
        t = np.linspace(0, seconds, int(self.RATE * seconds), dtype=np.float32)
        return Audio((0.2 * np.sin(2 * np.pi * 220 * t)).astype(np.float32), self.RATE)


def load_engine(settings: Settings) -> TtsEngine:
    if os.environ.get("M2A_FAKE_TTS") == "1":
        return FakeTts()
    from app.tts_kokoro import KokoroTts  # heavy optional dependency, imported lazily

    return KokoroTts(settings.model_dir)

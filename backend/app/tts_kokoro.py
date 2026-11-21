"""Kokoro ONNX adapter. Needs `pip install '.[tts]'` and model files in M2A_MODEL_DIR.

Verified locally against the real model (docs/DECISION.md, D-017). CI uses a stub
(tests/test_kokoro_adapter.py); tests/test_smoke_kokoro.py needs the real model files.
"""

from pathlib import Path
from typing import Protocol

import numpy as np
import numpy.typing as npt

from app.errors import AppError
from app.tts import Audio, Voice

MODEL_FILE = "kokoro-v1.0.onnx"
VOICES_FILE = "voices-v1.0.bin"
# Only English voice prefixes verified; extend per language after checking espeak codes.
LANGUAGE_BY_PREFIX = {"a": "en-us", "b": "en-gb"}


class _Kokoro(Protocol):
    def create(
        self, text: str, voice: str, speed: float, lang: str
    ) -> tuple[npt.NDArray[np.float32], int]: ...


class KokoroTts:
    def __init__(self, model_dir: Path) -> None:
        self._model = model_dir / MODEL_FILE
        self._voices_file = model_dir / VOICES_FILE
        self._voices: list[Voice] = []
        self._kokoro: _Kokoro | None = None

    def voices(self) -> list[Voice]:
        """Voices whose assets exist on disk; empty if model files are missing."""
        if not self._voices and self._model.is_file() and self._voices_file.is_file():
            with np.load(self._voices_file) as archive:  # voices-v1.0.bin is an npz archive
                names = sorted(archive.files)
            self._voices = [
                Voice(n, n, LANGUAGE_BY_PREFIX[n[0]]) for n in names if n[:1] in LANGUAGE_BY_PREFIX
            ]
        return self._voices

    def synthesize(self, text: str, voice_id: str, speed: float, language: str) -> Audio:
        if voice_id not in {v.id for v in self.voices()}:
            raise AppError("VOICE_NOT_FOUND", "Voice is not installed.")
        if self._kokoro is None:  # load once per process
            from kokoro_onnx import Kokoro  # type: ignore[import-not-found,unused-ignore]

            self._kokoro = Kokoro(str(self._model), str(self._voices_file))
        samples, rate = self._kokoro.create(text, voice=voice_id, speed=speed, lang=language)
        return Audio(np.asarray(samples, dtype=np.float32), int(rate))

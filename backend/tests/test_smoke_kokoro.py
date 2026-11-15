"""Optional smoke test: real Kokoro + real ffmpeg. Skipped unless model files exist."""

import os
from pathlib import Path

import pytest

from app.tts_kokoro import KokoroTts

MODEL_DIR = Path(os.environ.get("M2A_MODEL_DIR", "models/kokoro"))


@pytest.mark.skipif(not (MODEL_DIR / "kokoro-v1.0.onnx").is_file(), reason="model not installed")
def test_real_model_produces_audio() -> None:
    engine = KokoroTts(MODEL_DIR)
    voice = engine.voices()[0]
    audio = engine.synthesize("Hello from Mark two audio.", voice.id, 1.0, voice.language)
    assert audio.samples.size > audio.rate // 2

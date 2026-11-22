"""Optional smoke test: real Kokoro model + real FFmpeg. Skipped unless both are installed."""

import os
import shutil
from pathlib import Path

import pytest

from app.encoder import WavSink, encode_mp3, probe_mp3
from app.tts_kokoro import MODEL_FILE, VOICES_FILE, KokoroTts

# Repo root, so the default works from any working directory (pytest runs in backend/).
REPO_ROOT = Path(__file__).resolve().parents[2]
MODEL_DIR = Path(os.environ.get("M2A_MODEL_DIR", REPO_ROOT / "models" / "kokoro"))
INSTALLED = all(
    [
        (MODEL_DIR / MODEL_FILE).is_file(),
        (MODEL_DIR / VOICES_FILE).is_file(),
        shutil.which("ffmpeg"),
        shutil.which("ffprobe"),
    ]
)


@pytest.mark.skipif(not INSTALLED, reason="model files or ffmpeg not installed")
def test_real_model_to_valid_mp3(tmp_path: Path) -> None:
    engine = KokoroTts(MODEL_DIR)
    voices = engine.voices()
    assert voices, "model files present but no voices listed"
    voice = voices[0]
    audio = engine.synthesize("Hello from Mark two audio.", voice.id, 1.0, voice.language)
    assert audio.samples.size > audio.rate // 2

    wav, mp3 = tmp_path / "book.wav", tmp_path / "book.mp3"
    with WavSink(wav) as sink:
        sink.write(audio.samples, audio.rate)
        sink.silence(50)
    encode_mp3(wav, mp3, 128, "Smoke")
    assert probe_mp3(mp3) > 0.5

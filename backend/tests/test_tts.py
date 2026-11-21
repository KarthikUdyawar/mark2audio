import pytest

from app.config import Settings
from app.tts import FakeTts, load_engine
from app.tts_kokoro import KokoroTts


def test_load_engine_switches_on_fake_flag(
    settings: Settings, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("M2A_FAKE_TTS", "1")
    assert isinstance(load_engine(settings), FakeTts)
    monkeypatch.delenv("M2A_FAKE_TTS")
    assert isinstance(load_engine(settings), KokoroTts)

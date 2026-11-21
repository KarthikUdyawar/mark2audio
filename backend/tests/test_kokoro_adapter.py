"""Kokoro adapter contract tests with a stub model. No real model needed."""

import inspect
from pathlib import Path

import numpy as np
import numpy.typing as npt
import pytest

from app.errors import AppError
from app.tts_kokoro import MODEL_FILE, VOICES_FILE, KokoroTts


class StubKokoro:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str, float, str]] = []

    def create(
        self, text: str, voice: str, speed: float, lang: str
    ) -> tuple[npt.NDArray[np.float32], int]:
        self.calls.append((text, voice, speed, lang))
        return np.zeros(240, dtype=np.float32), 24000


@pytest.fixture
def model_dir(tmp_path: Path) -> Path:
    (tmp_path / MODEL_FILE).write_bytes(b"")
    with (tmp_path / VOICES_FILE).open("wb") as f:
        np.savez(f, af_test=np.zeros(1), bm_test=np.zeros(1), zf_test=np.zeros(1))
    return tmp_path


@pytest.fixture
def stubbed(model_dir: Path) -> tuple[KokoroTts, StubKokoro]:
    engine, stub = KokoroTts(model_dir), StubKokoro()
    engine._kokoro = stub
    return engine, stub


def test_missing_model_files_list_no_voices(tmp_path: Path) -> None:
    assert KokoroTts(tmp_path).voices() == []


def test_voices_keep_only_verified_languages(stubbed: tuple[KokoroTts, StubKokoro]) -> None:
    engine, _ = stubbed
    assert [(v.id, v.language) for v in engine.voices()] == [
        ("af_test", "en-us"),
        ("bm_test", "en-gb"),
    ]


def test_synthesize_forwards_arguments(stubbed: tuple[KokoroTts, StubKokoro]) -> None:
    engine, stub = stubbed
    audio = engine.synthesize("Hi.", "af_test", 1.1, "en-us")
    assert stub.calls == [("Hi.", "af_test", 1.1, "en-us")]
    assert audio.rate == 24000 and audio.samples.dtype == np.float32


def test_unknown_voice_never_reaches_the_model(stubbed: tuple[KokoroTts, StubKokoro]) -> None:
    engine, stub = stubbed
    with pytest.raises(AppError) as err:
        engine.synthesize("Hi.", "zf_test", 1.0, "en-us")
    assert err.value.code == "VOICE_NOT_FOUND" and stub.calls == []


def test_kokoro_create_keeps_the_keyword_names_we_call() -> None:
    kokoro_onnx = pytest.importorskip("kokoro_onnx")  # a library upgrade must fail here, in CI
    params = inspect.signature(kokoro_onnx.Kokoro.create).parameters
    assert {"text", "voice", "speed", "lang"} <= params.keys()

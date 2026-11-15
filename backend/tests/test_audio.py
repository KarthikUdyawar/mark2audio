import wave
from pathlib import Path

import numpy as np
import pytest

from app.encoder import WavSink, encode_mp3, ffmpeg_args, probe_mp3
from app.errors import AppError


def make_wav(path: Path, seconds: float = 0.5, rate: int = 24000) -> None:
    with WavSink(path) as sink:
        sink.write(np.sin(np.linspace(0, 440, int(rate * seconds))).astype(np.float32), rate)


def test_ffmpeg_args_are_a_list_without_shell_interpolation(tmp_path: Path) -> None:
    args = ffmpeg_args(tmp_path / "a.wav", tmp_path / "o.part", 192, "x; rm -rf /")
    assert isinstance(args, list) and "192k" in args and "title=x; rm -rf /" in args
    assert args[:2] == ["ffmpeg", "-y"] and args[-1].endswith("o.part")


def test_wav_sink_inserts_silence_and_rejects_rate_change(tmp_path: Path) -> None:
    path = tmp_path / "a.wav"
    with WavSink(path) as sink:
        sink.write(np.ones(240, dtype=np.float32), 24000)
        sink.silence(10)
        with pytest.raises(AppError):
            sink.write(np.ones(10, dtype=np.float32), 16000)
    with wave.open(str(path)) as w:
        assert w.getnframes() == 240 + 240 and w.getnchannels() == 1


def test_encode_and_probe_real_mp3(tmp_path: Path) -> None:
    make_wav(tmp_path / "a.wav")
    out = tmp_path / "a.mp3.part"
    encode_mp3(tmp_path / "a.wav", out, 128, "Title")
    assert probe_mp3(out) > 0.3


def test_probe_rejects_empty_and_garbage(tmp_path: Path) -> None:
    empty = tmp_path / "e.mp3"
    empty.write_bytes(b"")
    garbage = tmp_path / "g.mp3"
    garbage.write_bytes(b"not audio" * 100)
    for bad in (empty, garbage):
        with pytest.raises(AppError) as err:
            probe_mp3(bad)
        assert err.value.code == "OUTPUT_INVALID"


def test_encode_failure_is_safe_error(tmp_path: Path) -> None:
    with pytest.raises(AppError) as err:
        encode_mp3(tmp_path / "missing.wav", tmp_path / "o.part", 192, "T")
    assert err.value.code == "ENCODE_FAILED" and str(tmp_path) not in err.value.message

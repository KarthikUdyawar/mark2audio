"""WAV assembly and FFmpeg MP3 encoding/validation. Never uses a shell."""

import json
import subprocess
import wave
from pathlib import Path
from typing import Self

import numpy as np
import numpy.typing as npt

from app.errors import AppError

PROBE_TIMEOUT_S = 60
DIAGNOSTIC_BYTES = 500


class WavSink:
    """Incrementally writes mono 16-bit PCM so long books never sit fully in RAM."""

    def __init__(self, path: Path) -> None:
        self._path = path
        self._wav: wave.Wave_write | None = None
        self._rate = 0

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *exc: object) -> None:
        if self._wav:
            self._wav.close()

    def write(self, samples: npt.NDArray[np.float32], rate: int) -> None:
        if self._wav is None:
            self._wav = wave.open(str(self._path), "wb")  # noqa: SIM115 (closed in __exit__)
            self._wav.setparams((1, 2, rate, 0, "NONE", "NONE"))
            self._rate = rate
        elif rate != self._rate:
            raise AppError("AUDIO_FORMAT", "TTS sample rate changed mid-job.", 500)
        pcm = (np.clip(samples, -1, 1) * 32767).astype("<i2")
        self._wav.writeframes(pcm.tobytes())

    def silence(self, milliseconds: int) -> None:
        if self._wav is not None:
            self._wav.writeframes(b"\x00\x00" * (self._rate * milliseconds // 1000))


def ffmpeg_args(wav: Path, out: Path, bitrate_kbps: int, title: str) -> list[str]:
    return [
        "ffmpeg", "-y", "-nostdin", "-loglevel", "error", "-i", str(wav),
        "-codec:a", "libmp3lame", "-b:a", f"{bitrate_kbps}k",
        "-metadata", f"title={title}", "-f", "mp3", str(out),
    ]  # fmt: skip


def encode_mp3(wav: Path, out: Path, bitrate_kbps: int, title: str, timeout_s: int = 1800) -> None:
    try:
        run = subprocess.run(
            ffmpeg_args(wav, out, bitrate_kbps, title),
            capture_output=True, timeout=timeout_s, check=False,
        )  # fmt: skip
    except (OSError, subprocess.TimeoutExpired):
        raise AppError("ENCODE_FAILED", "Audio encoding failed.", 500) from None
    if run.returncode != 0:
        # Diagnostics go to server logs via the exception chain, not to the API client.
        raise AppError("ENCODE_FAILED", "Audio encoding failed.", 500) from RuntimeError(
            run.stderr[-DIAGNOSTIC_BYTES:].decode(errors="replace")
        )


def probe_mp3(path: Path) -> float:
    """Return duration in seconds; raise OUTPUT_INVALID unless a non-empty, positive-length MP3."""
    invalid = AppError("OUTPUT_INVALID", "Generated audio failed validation.", 500)
    if not path.is_file() or path.stat().st_size == 0:
        raise invalid
    args = ["ffprobe", "-v", "error", "-show_entries", "format=duration:stream=codec_name",
            "-of", "json", str(path)]  # fmt: skip
    try:
        run = subprocess.run(args, capture_output=True, timeout=PROBE_TIMEOUT_S, check=True)
        info = json.loads(run.stdout)
        codecs = {s.get("codec_name") for s in info.get("streams", [])}
        duration = float(info["format"]["duration"])
    except (OSError, subprocess.SubprocessError, ValueError, KeyError):
        raise invalid from None
    if codecs != {"mp3"} or duration <= 0:
        raise invalid
    return duration

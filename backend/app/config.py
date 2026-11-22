"""Runtime settings from environment variables (see .env.example)."""

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    data_dir: Path = Path("data")
    model_dir: Path = Path("models/kokoro")
    max_upload_bytes: int = 10 * 1024 * 1024
    chunk_max_chars: int = 400
    silence_ms: int = 350
    poll_seconds: float = 1.0
    ffmpeg_timeout_s: int = 1800

    @classmethod
    def from_env(cls) -> "Settings":
        env = os.environ
        return cls(
            data_dir=Path(env.get("M2A_DATA_DIR", "data")),
            model_dir=Path(env.get("M2A_MODEL_DIR", "models/kokoro")),
            max_upload_bytes=int(env.get("M2A_MAX_UPLOAD_BYTES", 10 * 1024 * 1024)),
            chunk_max_chars=int(env.get("M2A_CHUNK_MAX_CHARS", 400)),
            silence_ms=int(env.get("M2A_SILENCE_MS", 350)),
            poll_seconds=float(env.get("M2A_POLL_SECONDS", 1.0)),
        )

    @property
    def uploads_dir(self) -> Path:
        return self.data_dir / "uploads"

    @property
    def audio_dir(self) -> Path:
        return self.data_dir / "audio"

    @property
    def temp_dir(self) -> Path:
        return self.data_dir / "temp"

    @property
    def db_path(self) -> Path:
        return self.data_dir / "mark2audio.db"

    @property
    def heartbeat_path(self) -> Path:
        """Touched by the worker; read by the compose health check (D-020)."""
        return self.data_dir / "worker.heartbeat"

    def ensure_dirs(self) -> None:
        for path in (self.uploads_dir, self.audio_dir, self.temp_dir):
            path.mkdir(parents=True, exist_ok=True)

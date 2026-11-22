import errno
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

from app import worker
from app.config import Settings
from app.encoder import encode_mp3, probe_mp3
from app.errors import AppError
from app.storage import book_dir
from app.store import JobParams, Store
from app.tts import Audio, FakeTts
from app.worker import run_pending
from tests.conftest import add_book

PARAMS = JobParams("fake_a", "en-us", 1.0, 128, False)


def test_job_completes_with_valid_mp3_and_clean_temp(
    settings: Settings, store: Store, engine: FakeTts
) -> None:
    book_id = add_book(settings, store)
    job = store.create_job(book_id, PARAMS)
    assert run_pending(store, engine, settings) is True
    done = store.get_job(job.id)
    assert (done.status, done.progress_percent) == ("completed", 100)
    assert done.total_chunks == done.completed_chunks >= 2
    assert probe_mp3(book_dir(settings.audio_dir, book_id) / "audiobook.mp3") > 0
    assert not (settings.temp_dir / job.id).exists()
    assert run_pending(store, engine, settings) is False


class BoomTts(FakeTts):
    def synthesize(self, text: str, voice_id: str, speed: float, language: str) -> Audio:
        raise RuntimeError(f"secret document text: {text}")


def test_tts_failure_marks_failed_without_leaking_text(settings: Settings, store: Store) -> None:
    job = store.create_job(add_book(settings, store), PARAMS)
    run_pending(store, BoomTts(), settings)
    failed = store.get_job(job.id)
    assert failed.status == "failed" and failed.error_code == "INTERNAL"
    assert "secret" not in (failed.error_message or "")
    assert not (settings.temp_dir / job.id).exists()


def test_empty_book_text_fails_with_clear_code(
    settings: Settings, store: Store, engine: FakeTts
) -> None:
    job = store.create_job(add_book(settings, store, "# \n"), PARAMS)
    run_pending(store, engine, settings)
    assert store.get_job(job.id).error_code == "NO_TEXT"


class CancelTts(FakeTts):
    def __init__(self, store: Store, job_id: str) -> None:
        self.store, self.job_id = store, job_id

    def synthesize(self, text: str, voice_id: str, speed: float, language: str) -> Audio:
        self.store.transition(self.job_id, "cancelled")  # user cancels mid-run
        return Audio(np.zeros(100, dtype=np.float32), 24000)


def test_cancel_stops_at_chunk_boundary_and_publishes_nothing(
    settings: Settings, store: Store
) -> None:
    book_id = add_book(settings, store)
    job = store.create_job(book_id, PARAMS)
    run_pending(store, CancelTts(store, job.id), settings)
    assert store.get_job(job.id).status == "cancelled"
    assert not (book_dir(settings.audio_dir, book_id) / "audiobook.mp3").exists()
    assert not (settings.temp_dir / job.id).exists()


def test_stale_job_recovered_on_start(settings: Settings, store: Store) -> None:
    job = store.create_job(add_book(settings, store), PARAMS)
    store.transition(job.id, "processing")
    store.fail_stale()
    assert store.get_job(job.id).error_code == "WORKER_RESTARTED"


def test_unknown_voice_rejected_by_engine(engine: FakeTts) -> None:
    with pytest.raises(AppError) as err:
        engine.synthesize("x", "nope", 1.0, "en-us")
    assert err.value.code == "VOICE_NOT_FOUND"


def test_cancel_during_encode_publishes_nothing(
    settings: Settings, store: Store, engine: FakeTts, monkeypatch: pytest.MonkeyPatch
) -> None:
    book_id = add_book(settings, store)
    job = store.create_job(book_id, PARAMS)
    real_encode = encode_mp3

    def encode_then_cancel(
        wav: Path, out: Path, bitrate_kbps: int, title: str, timeout_s: int = 1800
    ) -> None:
        real_encode(wav, out, bitrate_kbps, title, timeout_s)
        store.transition(job.id, "cancelled")  # user cancels while FFmpeg runs

    monkeypatch.setattr(worker, "encode_mp3", encode_then_cancel)
    run_pending(store, engine, settings)
    out_dir = book_dir(settings.audio_dir, book_id)
    assert store.get_job(job.id).status == "cancelled"
    assert not (out_dir / "audiobook.mp3").exists()
    assert not (out_dir / "audiobook.mp3.part").exists()


class CancelThenCrashTts(FakeTts):
    def __init__(self, store: Store, job_id: str) -> None:
        self.store, self.job_id = store, job_id

    def synthesize(self, text: str, voice_id: str, speed: float, language: str) -> Audio:
        self.store.transition(self.job_id, "cancelled")
        raise RuntimeError("boom")


def test_failure_after_cancel_keeps_cancelled_status(settings: Settings, store: Store) -> None:
    job = store.create_job(add_book(settings, store), PARAMS)
    run_pending(store, CancelThenCrashTts(store, job.id), settings)
    assert store.get_job(job.id).status == "cancelled"


class _StopLoopError(Exception):
    pass


def test_main_recovers_stale_job_runs_queued_then_idles(
    settings: Settings, store: Store, monkeypatch: pytest.MonkeyPatch
) -> None:
    stale = store.create_job(add_book(settings, store), PARAMS)
    store.transition(stale.id, "processing")  # a worker died mid-job
    queued = store.create_job(add_book(settings, store), PARAMS)
    monkeypatch.setenv("M2A_DATA_DIR", str(settings.data_dir))
    monkeypatch.setenv("M2A_FAKE_TTS", "1")

    def stop_when_idle(_seconds: float) -> None:
        raise _StopLoopError

    # Replace the name inside app.worker only: patching time.sleep globally would also
    # break subprocess polling.
    monkeypatch.setattr(worker, "time", SimpleNamespace(sleep=stop_when_idle))
    with pytest.raises(_StopLoopError):
        worker.main()
    assert store.get_job(stale.id).error_code == "WORKER_RESTARTED"
    assert store.get_job(queued.id).status == "completed"


class DiskFullTts(FakeTts):
    def synthesize(self, text: str, voice_id: str, speed: float, language: str) -> Audio:
        raise OSError(errno.ENOSPC, "No space left on device")


def test_disk_full_fails_job_with_safe_code(settings: Settings, store: Store) -> None:
    job = store.create_job(add_book(settings, store), PARAMS)
    run_pending(store, DiskFullTts(), settings)
    done = store.get_job(job.id)
    assert (done.status, done.error_code) == ("failed", "DISK_FULL")

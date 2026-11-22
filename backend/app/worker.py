"""Single-job worker: claim → parse → chunk → synthesize → encode → validate → publish."""

import logging
import os
import shutil
import time
from pathlib import Path

from app.chunker import chunk_chapters
from app.config import Settings
from app.encoder import WavSink, encode_mp3, probe_mp3
from app.errors import AppError, as_disk_full
from app.parser import parse_markdown
from app.storage import book_dir
from app.store import Job, Store
from app.tts import TtsEngine, load_engine

log = logging.getLogger("mark2audio.worker")


class _CancelledError(Exception):
    pass


def beat(settings: Settings) -> None:
    """Touch the heartbeat file so the health check sees the worker alive (D-020)."""
    settings.heartbeat_path.touch()


def run_pending(store: Store, engine: TtsEngine, settings: Settings) -> bool:
    """Run one queued job if any. Returns whether a job was claimed."""
    job = store.claim_next()
    if job is None:
        return False
    temp = settings.temp_dir / job.id
    try:
        _convert(store, engine, settings, job, temp)
        _settle(store, job.id, "completed")
    except _CancelledError:
        pass
    except Exception as err:
        known = err if isinstance(err, AppError) else as_disk_full(err)
        if known is None:
            log.exception("job %s crashed", job.id)  # stack trace stays server-side
            _settle(store, job.id, "failed", "INTERNAL", "Conversion failed. See server logs.")
        else:
            log.warning("job %s failed: %s", job.id, known.code, exc_info=err.__cause__ is not None)
            _settle(store, job.id, "failed", known.code, known.message)
    finally:
        shutil.rmtree(temp, ignore_errors=True)
        (book_dir(settings.audio_dir, job.book_id) / "audiobook.mp3.part").unlink(missing_ok=True)
    return True


def _settle(
    store: Store, job_id: str, to: str, code: str | None = None, msg: str | None = None
) -> None:
    try:
        store.transition(job_id, to, code, msg)
    except AppError as err:
        if err.code != "INVALID_TRANSITION":  # already cancelled by the user
            raise


def _convert(store: Store, engine: TtsEngine, settings: Settings, job: Job, temp: Path) -> None:
    book = store.get_book(job.book_id)
    source = book_dir(settings.uploads_dir, job.book_id) / "source.md"
    chapters = parse_markdown(
        source.read_text(encoding="utf-8"), include_code=job.include_code_blocks
    )
    if not chapters:
        raise AppError("NO_TEXT", "Document has no speakable text.")
    chunks = chunk_chapters(chapters, settings.chunk_max_chars)
    temp.mkdir(parents=True)
    wav = temp / "book.wav"
    with WavSink(wav) as sink:
        for done, chunk in enumerate(chunks, start=1):
            if store.get_job(job.id).status == "cancelled":
                raise _CancelledError
            audio = engine.synthesize(chunk.text, job.voice_id, job.speed, job.language)
            sink.write(audio.samples, audio.rate)
            sink.silence(settings.silence_ms)
            store.set_progress(job.id, done, len(chunks), chunk.chapter_title)
            beat(settings)
    out_dir = book_dir(settings.audio_dir, job.book_id)
    out_dir.mkdir(parents=True, exist_ok=True)
    part = out_dir / "audiobook.mp3.part"
    beat(settings)
    encode_mp3(wav, part, job.bitrate_kbps, book.title, settings.ffmpeg_timeout_s)
    probe_mp3(part)
    if store.get_job(job.id).status == "cancelled":
        raise _CancelledError
    os.replace(part, out_dir / "audiobook.mp3")  # atomic publish


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    settings = Settings.from_env()
    settings.ensure_dirs()
    store = Store(settings.db_path)
    store.fail_stale()
    engine = load_engine(settings)  # model loaded once per process
    log.info("worker ready")
    while True:
        beat(settings)
        if not run_pending(store, engine, settings):
            time.sleep(settings.poll_seconds)


if __name__ == "__main__":
    main()

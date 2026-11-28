"""REST API (/api/v1) + static UI. Heavy work is queued for the worker, never run here."""

import logging
import re
import shutil
import uuid
from pathlib import Path
from typing import Annotated, Literal

from fastapi import APIRouter, FastAPI, File, Request, UploadFile
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from app.config import Settings
from app.errors import AppError, as_disk_full
from app.parser import INTRO_TITLE, parse_markdown
from app.schemas import (
    BookDetailOut,
    BookOut,
    ChapterOut,
    ErrorResponse,
    HealthOut,
    JobErrorOut,
    JobOut,
    VoiceOut,
)
from app.storage import book_dir, remove_tree
from app.store import Book, Job, JobParams, Store
from app.tts import SPEED_RANGE, TtsEngine

STATIC = Path(__file__).parent / "static"
log = logging.getLogger("mark2audio.api")
ERROR_STATUSES = (400, 404, 409, 413, 422, 500, 503, 507)


class ConvertRequest(BaseModel):
    voice_id: str | None = None
    language: str | None = None
    speed: float = Field(1.0, ge=SPEED_RANGE[0], le=SPEED_RANGE[1])
    bitrate_kbps: Literal[128, 192, 256] = 192
    include_code_blocks: bool = False


def _display_name(raw: str | None) -> str:
    name = Path((raw or "").replace("\\", "/")).name
    return re.sub(r"[^\w .-]", "_", name)[:100] or "upload.md"


def _slug(title: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "_", title).strip("_")[:80] or "audiobook"


def _job_out(job: Job) -> JobOut:
    error = JobErrorOut(code=job.error_code, message=job.error_message) if job.error_code else None
    return JobOut.model_validate(
        {
            "id": job.id, "book_id": job.book_id, "status": job.status,
            "progress_percent": job.progress_percent, "completed_chunks": job.completed_chunks,
            "total_chunks": job.total_chunks, "current_chapter": job.current_chapter,
            "error": error,
        }
    )  # fmt: skip


def _book_out(book: Book) -> BookOut:
    return BookOut.model_validate(
        {
            "id": book.id, "title": book.title, "original_filename": book.original_filename,
            "status": book.status, "chapter_count": book.chapter_count,
            "created_at": book.created_at, "duration_seconds": book.duration_seconds,
        }
    )  # fmt: skip


def create_app(settings: Settings, engine: TtsEngine) -> FastAPI:
    settings.ensure_dirs()
    store = Store(settings.db_path)
    api = APIRouter(
        prefix="/api/v1",
        responses={
            code: {"model": ErrorResponse, "description": "Error"} for code in ERROR_STATUSES
        },
    )

    def read_source(book_id: str) -> str:
        try:
            return (book_dir(settings.uploads_dir, book_id) / "source.md").read_text(
                encoding="utf-8"
            )
        except FileNotFoundError:
            raise AppError("SOURCE_MISSING", "Book source file is missing.", 500) from None

    @api.get("/health")
    def health() -> HealthOut:
        ok = bool(shutil.which("ffmpeg") and shutil.which("ffprobe"))
        return HealthOut.model_validate(
            {"status": "ok" if ok else "degraded", "ffmpeg": ok, "voices": len(engine.voices())}
        )

    @api.post("/books/upload", status_code=201)
    def upload(file: Annotated[UploadFile, File()]) -> BookOut:
        display = _display_name(file.filename)
        if Path(display).suffix.lower() not in {".md", ".markdown"}:
            raise AppError("UNSUPPORTED_TYPE", "Only .md and .markdown files are supported.")
        raw = file.file.read(settings.max_upload_bytes + 1)
        if len(raw) > settings.max_upload_bytes:
            raise AppError("FILE_TOO_LARGE", "File exceeds the upload limit.", 413)
        if not raw.strip():
            raise AppError("EMPTY_FILE", "File is empty.")
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError:
            raise AppError("INVALID_ENCODING", "File must be UTF-8 text.") from None
        chapters = parse_markdown(text)
        if not chapters:
            raise AppError("NO_TEXT", "Document has no speakable text.")
        named = [c.title for c in chapters if c.title != INTRO_TITLE]
        title = named[0] if named else Path(display).stem
        book_id = str(uuid.uuid4())
        folder = book_dir(settings.uploads_dir, book_id)
        folder.mkdir(parents=True)
        try:
            (folder / "source.md").write_text(text, encoding="utf-8")
            store.create_book(book_id, title, display, len(chapters), [c.title for c in chapters])
        except BaseException as err:
            shutil.rmtree(folder, ignore_errors=True)  # no orphan upload on failure
            full = as_disk_full(err)
            if full is None:
                raise
            raise full from err
        return _book_out(store.get_book(book_id))

    @api.get("/books")
    def list_books() -> list[BookOut]:
        return [_book_out(b) for b in store.list_books()]

    @api.get("/books/{book_id}")
    def book_detail(book_id: str) -> BookDetailOut:
        book = store.get_book(book_id)
        rows = store.get_chapters(book_id)
        if not rows:  # book uploaded before S3: backfill once from the source
            store.backfill_chapters(
                book_id, [c.title for c in parse_markdown(read_source(book_id))]
            )
            rows = store.get_chapters(book_id)
            book = store.get_book(book_id)
        latest = store.latest_job(book_id)
        return BookDetailOut(
            **_book_out(book).model_dump(),
            chapters=[
                ChapterOut(
                    number=r.number,
                    title=r.title,
                    start_seconds=r.start_seconds,
                    duration_seconds=r.duration_seconds,
                )
                for r in rows
            ],
            latest_job=_job_out(latest) if latest else None,
        )

    @api.delete("/books/{book_id}", status_code=204)
    def delete_book(book_id: str) -> Response:
        store.get_book(book_id)
        store.delete_book(book_id)
        remove_tree(settings.uploads_dir, book_id)
        remove_tree(settings.audio_dir, book_id)
        return Response(status_code=204)

    @api.get("/voices")
    def voices() -> list[VoiceOut]:
        return [
            VoiceOut(id=v.id, name=v.name, language=v.language, available=True)
            for v in engine.voices()
        ]

    @api.post("/books/{book_id}/convert", status_code=202)
    def convert(book_id: str, req: ConvertRequest) -> JobOut:
        store.get_book(book_id)
        installed = {v.id: v for v in engine.voices()}
        if not installed:
            raise AppError("MODEL_UNAVAILABLE", "No TTS voices installed. See README setup.", 503)
        voice = installed.get(req.voice_id or next(iter(installed)))
        if voice is None:
            raise AppError("VOICE_NOT_FOUND", "Voice is not installed.")
        if req.language not in (None, voice.language):
            raise AppError("LANGUAGE_MISMATCH", f"Voice supports {voice.language}.")
        params = JobParams(
            voice.id, voice.language, req.speed, req.bitrate_kbps, req.include_code_blocks
        )
        return _job_out(store.create_job(book_id, params))

    @api.get("/jobs/{job_id}")
    def job_status(job_id: str) -> JobOut:
        return _job_out(store.get_job(job_id))

    @api.post("/jobs/{job_id}/cancel")
    def cancel(job_id: str) -> JobOut:
        store.transition(job_id, "cancelled")
        return _job_out(store.get_job(job_id))

    @api.get(
        "/books/{book_id}/audio",
        response_class=FileResponse,
        responses={
            200: {"content": {"audio/mpeg": {"schema": {"type": "string", "format": "binary"}}}}
        },
    )
    def audio(book_id: str) -> FileResponse:
        book = store.get_book(book_id)
        path = book_dir(settings.audio_dir, book_id) / "audiobook.mp3"
        if book.status != "completed" or not path.is_file():
            raise AppError("NOT_READY", "Audio is not ready.", 404)
        return FileResponse(path, media_type="audio/mpeg", filename=f"{_slug(book.title)}.mp3")

    app = FastAPI(title="Mark2Audio")

    @app.exception_handler(AppError)
    async def _app_error(_: Request, err: AppError) -> JSONResponse:
        return JSONResponse({"error": {"code": err.code, "message": err.message}}, err.status)

    @app.exception_handler(Exception)
    async def _unexpected(_: Request, err: Exception) -> JSONResponse:
        log.error("unhandled error", exc_info=err)  # stack trace stays server-side
        body = {"error": {"code": "INTERNAL", "message": "Unexpected server error."}}
        return JSONResponse(body, 500)

    @app.exception_handler(RequestValidationError)
    async def _invalid(_: Request, err: RequestValidationError) -> JSONResponse:
        first = err.errors()[0]
        where = ".".join(str(p) for p in first["loc"][1:])
        message = f"Invalid {where}: {first['msg']}" if where else first["msg"]
        return JSONResponse({"error": {"code": "VALIDATION_ERROR", "message": message}}, 422)

    app.include_router(api)
    app.mount("/", StaticFiles(directory=STATIC, html=True), name="ui")
    return app

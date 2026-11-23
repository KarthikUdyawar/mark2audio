"""Pydantic response models: the public API contract (D-024)."""

from typing import Literal

from pydantic import BaseModel

BookStatus = Literal["uploaded", "queued", "processing", "completed", "failed"]
JobStatus = Literal["queued", "processing", "completed", "failed", "cancelled"]


class ErrorBody(BaseModel):
    code: str
    message: str


class ErrorResponse(BaseModel):
    error: ErrorBody


class JobErrorOut(BaseModel):
    code: str
    message: str | None


class JobOut(BaseModel):
    id: str
    book_id: str
    status: JobStatus
    progress_percent: int
    completed_chunks: int
    total_chunks: int
    current_chapter: str | None
    error: JobErrorOut | None


class BookOut(BaseModel):
    id: str
    title: str
    original_filename: str
    status: BookStatus
    chapter_count: int
    created_at: str
    duration_seconds: float | None


class ChapterOut(BaseModel):
    number: int
    title: str
    start_seconds: float | None
    duration_seconds: float | None


class BookDetailOut(BookOut):
    chapters: list[ChapterOut]
    latest_job: JobOut | None


class VoiceOut(BaseModel):
    id: str
    name: str
    language: str
    available: bool


class HealthOut(BaseModel):
    status: Literal["ok", "degraded"]
    ffmpeg: bool
    voices: int

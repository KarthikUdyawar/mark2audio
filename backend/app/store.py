"""SQLite persistence: books, conversion jobs, validated state machine, atomic claiming."""

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from app.errors import AppError
from app.migrate import migrate

MIGRATIONS_DIR = Path(__file__).parent / "migrations"
ALLOWED = {
    "queued": {"processing", "cancelled"},
    "processing": {"completed", "failed", "cancelled"},
}
ACTIVE = ("queued", "processing")
PROGRESS_CAP_BEFORE_PUBLISH = 99


@dataclass(frozen=True)
class JobParams:
    voice_id: str
    language: str
    speed: float
    bitrate_kbps: int
    include_code_blocks: bool


@dataclass(frozen=True)
class Job:
    id: str
    book_id: str
    status: str
    voice_id: str
    language: str
    speed: float
    bitrate_kbps: int
    include_code_blocks: bool
    total_chunks: int
    completed_chunks: int
    progress_percent: int
    current_chapter: str | None
    error_code: str | None
    error_message: str | None
    created_at: str
    started_at: str | None
    completed_at: str | None


@dataclass(frozen=True)
class Book:
    id: str
    title: str
    original_filename: str
    chapter_count: int
    created_at: str
    status: str


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _job(row: sqlite3.Row) -> Job:
    return Job(**{**dict(row), "include_code_blocks": bool(row["include_code_blocks"])})


class Store:
    def __init__(self, path: Path) -> None:
        self._path = path
        migrate(path, MIGRATIONS_DIR)

    def _connect(self) -> sqlite3.Connection:
        db = sqlite3.connect(self._path, timeout=30, isolation_level=None)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA foreign_keys=ON")
        return db

    @contextmanager
    def _tx(self) -> Iterator[sqlite3.Connection]:
        """Short transaction on a fresh connection (API and worker are separate processes)."""
        db = self._connect()
        db.execute("BEGIN IMMEDIATE")
        try:
            yield db
            db.execute("COMMIT")
        except BaseException:
            db.execute("ROLLBACK")
            raise
        finally:
            db.close()

    # --- books ---
    def create_book(self, book_id: str, title: str, filename: str, chapter_count: int) -> None:
        with self._tx() as db:
            db.execute(
                "INSERT INTO books VALUES (?,?,?,?,?)",
                (book_id, title, filename, chapter_count, _now()),
            )

    _BOOK_SQL = """SELECT b.*, (SELECT status FROM jobs j WHERE j.book_id=b.id
                   ORDER BY j.created_at DESC, j.rowid DESC LIMIT 1) AS job_status FROM books b"""

    def list_books(self) -> list[Book]:
        with self._tx() as db:
            return [self._book(r) for r in db.execute(self._BOOK_SQL + " ORDER BY created_at DESC")]

    def get_book(self, book_id: str) -> Book:
        with self._tx() as db:
            row = db.execute(self._BOOK_SQL + " WHERE b.id=?", (book_id,)).fetchone()
        if row is None:
            raise AppError("BOOK_NOT_FOUND", "Book not found.", 404)
        return self._book(row)

    @staticmethod
    def _book(row: sqlite3.Row) -> Book:
        status = row["job_status"]
        if status not in {"queued", "processing", "completed", "failed"}:
            status = "uploaded"
        return Book(
            row["id"], row["title"], row["original_filename"], row["chapter_count"],
            row["created_at"], status,
        )  # fmt: skip

    def delete_book(self, book_id: str) -> None:
        with self._tx() as db:
            if db.execute(self._active_sql(), (book_id,)).fetchone():
                raise AppError("JOB_ACTIVE", "A conversion is running for this book.", 409)
            db.execute("DELETE FROM books WHERE id=?", (book_id,))

    # --- jobs ---
    @staticmethod
    def _active_sql() -> str:
        return "SELECT 1 FROM jobs WHERE book_id=? AND status IN ('queued','processing')"

    def create_job(self, book_id: str, p: JobParams) -> Job:
        job_id = str(uuid4())
        with self._tx() as db:
            if db.execute("SELECT 1 FROM books WHERE id=?", (book_id,)).fetchone() is None:
                raise AppError("BOOK_NOT_FOUND", "Book not found.", 404)  # deleted meanwhile
            if db.execute(self._active_sql(), (book_id,)).fetchone():
                raise AppError("JOB_ACTIVE", "A conversion is already active for this book.", 409)
            db.execute(
                "INSERT INTO jobs (id,book_id,status,voice_id,language,speed,bitrate_kbps,"
                "include_code_blocks,created_at) VALUES (?,?,?,?,?,?,?,?,?)",
                (job_id, book_id, "queued", p.voice_id, p.language, p.speed, p.bitrate_kbps,
                 int(p.include_code_blocks), _now()),
            )  # fmt: skip
        return self.get_job(job_id)

    def get_job(self, job_id: str) -> Job:
        with self._tx() as db:
            row = db.execute("SELECT * FROM jobs WHERE id=?", (job_id,)).fetchone()
        if row is None:
            raise AppError("JOB_NOT_FOUND", "Job not found.", 404)
        return _job(row)

    def latest_job(self, book_id: str) -> Job | None:
        with self._tx() as db:
            row = db.execute(
                "SELECT * FROM jobs WHERE book_id=? ORDER BY created_at DESC, rowid DESC LIMIT 1",
                (book_id,),
            ).fetchone()
        return _job(row) if row else None

    def claim_next(self) -> Job | None:
        """Atomically move the oldest queued job to processing; None if nothing queued."""
        with self._tx() as db:
            row = db.execute(
                "UPDATE jobs SET status='processing', started_at=? WHERE id=(SELECT id FROM jobs "
                "WHERE status='queued' ORDER BY created_at, rowid LIMIT 1) AND status='queued' "
                "RETURNING *",
                (_now(),),
            ).fetchone()
        return _job(row) if row else None

    def transition(
        self, job_id: str, to: str, error_code: str | None = None, error_message: str | None = None
    ) -> None:
        with self._tx() as db:
            row = db.execute("SELECT status FROM jobs WHERE id=?", (job_id,)).fetchone()
            if row is None:
                raise AppError("JOB_NOT_FOUND", "Job not found.", 404)
            if to not in ALLOWED.get(row["status"], set()):
                raise AppError("INVALID_TRANSITION", f"Cannot go {row['status']} → {to}.", 409)
            done = _now() if to in ("completed", "failed", "cancelled") else None
            db.execute(
                "UPDATE jobs SET status=?, error_code=?, error_message=?, completed_at=?, "
                "progress_percent=CASE WHEN ?='completed' THEN 100 ELSE progress_percent END "
                "WHERE id=?",
                (to, error_code, error_message, done, to, job_id),
            )

    def set_progress(self, job_id: str, completed: int, total: int, chapter: str) -> None:
        percent = min(completed * 100 // max(total, 1), PROGRESS_CAP_BEFORE_PUBLISH)
        with self._tx() as db:
            db.execute(
                "UPDATE jobs SET completed_chunks=?, total_chunks=?, current_chapter=?, "
                "progress_percent=MAX(progress_percent, ?) WHERE id=? AND status='processing'",
                (completed, total, chapter, percent, job_id),
            )

    def fail_stale(self) -> None:
        with self._tx() as db:
            db.execute(
                "UPDATE jobs SET status='failed', error_code='WORKER_RESTARTED', "
                "error_message='Worker restarted during conversion.', completed_at=? "
                "WHERE status='processing'",
                (_now(),),
            )

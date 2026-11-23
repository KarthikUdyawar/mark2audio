import threading
import uuid
from pathlib import Path

import pytest

from app.errors import AppError
from app.storage import book_dir
from app.store import ChapterRow, JobParams, Store

PARAMS = JobParams(
    voice_id="v", language="en-us", speed=1.0, bitrate_kbps=192, include_code_blocks=False
)


@pytest.fixture
def store(tmp_path: Path) -> Store:
    s = Store(tmp_path / "t.db")
    s.create_book("b1", "Title", "t.md", 2)
    return s


def test_claim_is_atomic_and_oldest_first(store: Store) -> None:
    first = store.create_job("b1", PARAMS)
    results: list[object] = []
    threads = [
        threading.Thread(target=lambda: results.append(store.claim_next())) for _ in range(5)
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    claimed = [r for r in results if r is not None]
    assert len(claimed) == 1 and claimed[0].id == first.id  # type: ignore[attr-defined]
    assert store.get_job(first.id).status == "processing"


@pytest.mark.parametrize(
    "a,b", [("completed", "processing"), ("queued", "completed"), ("failed", "queued")]
)
def test_illegal_transitions_rejected(store: Store, a: str, b: str) -> None:
    job = store.create_job("b1", PARAMS)
    path = {
        "completed": ["processing", "completed"],
        "queued": [],
        "failed": ["processing", "failed"],
    }[a]
    for step in path:
        store.transition(job.id, step)
    with pytest.raises(AppError) as err:
        store.transition(job.id, b)
    assert err.value.code == "INVALID_TRANSITION"


def test_progress_monotonic_capped_until_completed(store: Store) -> None:
    job = store.create_job("b1", PARAMS)
    store.transition(job.id, "processing")
    store.set_progress(job.id, 5, 10, "A")
    store.set_progress(job.id, 3, 10, "A")
    assert store.get_job(job.id).progress_percent == 50
    store.set_progress(job.id, 10, 10, "A")
    assert store.get_job(job.id).progress_percent == 99
    store.transition(job.id, "completed")
    assert store.get_job(job.id).progress_percent == 100


def test_stale_processing_jobs_fail_on_startup(store: Store) -> None:
    job = store.create_job("b1", PARAMS)
    store.transition(job.id, "processing")
    store.fail_stale()
    got = store.get_job(job.id)
    assert (got.status, got.error_code) == ("failed", "WORKER_RESTARTED")


def test_one_active_job_per_book_and_status_derivation(store: Store) -> None:
    job = store.create_job("b1", PARAMS)
    with pytest.raises(AppError) as err:
        store.create_job("b1", PARAMS)
    assert err.value.status == 409
    assert store.get_book("b1").status == "queued"
    store.transition(job.id, "cancelled")
    assert store.get_book("b1").status == "uploaded"


def test_delete_book_cascades_jobs(store: Store) -> None:
    job = store.create_job("b1", PARAMS)
    with pytest.raises(AppError):  # active job blocks delete
        store.delete_book("b1")
    store.transition(job.id, "cancelled")
    store.delete_book("b1")
    with pytest.raises(AppError):
        store.get_job(job.id)


def test_book_dir_rejects_traversal_and_symlink_escape(tmp_path: Path) -> None:
    root = tmp_path / "uploads"
    root.mkdir()
    with pytest.raises(AppError):
        book_dir(root, "../../etc")
    outside = tmp_path / "outside"
    outside.mkdir()
    bid = str(uuid.uuid4())
    (root / bid).symlink_to(outside)
    with pytest.raises(AppError):
        book_dir(root, bid)
    assert book_dir(root, str(uuid.uuid4())).parent == root.resolve()


def test_create_job_for_unknown_book_is_not_found(store: Store) -> None:
    params = JobParams("fake_a", "en-us", 1.0, 128, False)
    with pytest.raises(AppError) as err:
        store.create_job(str(uuid.uuid4()), params)
    assert err.value.code == "BOOK_NOT_FOUND" and err.value.status == 404


def test_create_book_with_chapters_writes_rows(store: Store) -> None:
    store.create_book("b2", "T", "t.md", 2, ["Same", "Same"])
    rows = store.get_chapters("b2")
    assert [(r.number, r.title) for r in rows] == [(1, "Same"), (2, "Same")]
    assert all(r.start_seconds is None and r.duration_seconds is None for r in rows)


def test_set_chapters_replaces_rows_and_count(store: Store) -> None:
    store.set_chapters("b1", ["X", "Y", "Z"])
    store.set_chapters("b1", ["Q"])
    assert [(r.number, r.title) for r in store.get_chapters("b1")] == [(1, "Q")]
    assert store.get_book("b1").chapter_count == 1


def test_set_chapters_unknown_book_is_not_found(store: Store) -> None:
    with pytest.raises(AppError) as err:
        store.set_chapters("nope", ["A"])
    assert err.value.code == "BOOK_NOT_FOUND"


def test_get_chapters_without_rows_is_empty(store: Store) -> None:
    assert store.get_chapters("b1") == []


def _book_duration(store: Store, book_id: str) -> float | None:
    db = store._connect()
    try:
        return db.execute(  # type: ignore[no-any-return]
            "SELECT duration_seconds FROM books WHERE id=?", (book_id,)
        ).fetchone()[0]
    finally:
        db.close()


def test_complete_job_writes_timing_and_completes_atomically(store: Store) -> None:
    job = store.create_job("b1", PARAMS)
    store.transition(job.id, "processing")
    rows = [ChapterRow(1, "A", 0.0, 1.5), ChapterRow(2, "A", 1.5, 2.0)]
    store.complete_job(job.id, rows, 3.6)
    done = store.get_job(job.id)
    assert (done.status, done.progress_percent) == ("completed", 100)
    assert store.get_chapters("b1") == rows
    assert store.get_book("b1").chapter_count == 2
    assert _book_duration(store, "b1") == 3.6


def test_complete_job_on_cancelled_job_writes_nothing(store: Store) -> None:
    store.set_chapters("b1", ["Old"])
    job = store.create_job("b1", PARAMS)
    store.transition(job.id, "processing")
    store.transition(job.id, "cancelled")
    with pytest.raises(AppError) as err:
        store.complete_job(job.id, [ChapterRow(1, "New", 0.0, 1.0)], 1.0)
    assert err.value.code == "INVALID_TRANSITION"
    assert [(r.title, r.duration_seconds) for r in store.get_chapters("b1")] == [("Old", None)]
    assert _book_duration(store, "b1") is None


def test_book_exposes_stored_duration(store: Store) -> None:
    assert store.get_book("b1").duration_seconds is None
    job = store.create_job("b1", PARAMS)
    store.transition(job.id, "processing")
    store.complete_job(job.id, [ChapterRow(1, "A", 0.0, 1.0)], 3.6)
    assert store.get_book("b1").duration_seconds == 3.6
    assert [b.duration_seconds for b in store.list_books()] == [3.6]

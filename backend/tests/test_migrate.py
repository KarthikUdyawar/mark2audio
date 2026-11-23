"""Migration runner: ordered SQL files, PRAGMA user_version, backup, newer-DB refusal."""

import sqlite3
import threading
from pathlib import Path

import pytest

from app.errors import AppError
from app.migrate import migrate
from app.store import Store


def _write(folder: Path, files: dict[str, str]) -> Path:
    folder.mkdir(exist_ok=True)
    for name, body in files.items():
        (folder / f"{name}.sql").write_text(body)
    return folder


def _version(path: Path) -> int:
    db = sqlite3.connect(path)
    try:
        return int(db.execute("PRAGMA user_version").fetchone()[0])
    finally:
        db.close()


def _tables(path: Path) -> set[str]:
    db = sqlite3.connect(path)
    try:
        return {r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    finally:
        db.close()


def test_applies_pending_in_order_on_fresh_db(tmp_path: Path) -> None:
    folder = _write(
        tmp_path / "m",
        {
            "002_rows": "INSERT INTO a VALUES (1);\n-- comment\nINSERT INTO a VALUES (2);",
            "001_table": "CREATE TABLE a (n INTEGER);",
        },
    )
    db_path = tmp_path / "app.db"
    migrate(db_path, folder)
    assert _version(db_path) == 2
    db = sqlite3.connect(db_path)
    try:
        assert [r[0] for r in db.execute("SELECT n FROM a ORDER BY rowid")] == [1, 2]
    finally:
        db.close()
    assert list(tmp_path.glob("*.pre-v*")) == []  # fresh database: nothing to protect


def test_second_run_is_a_noop(tmp_path: Path) -> None:
    folder = _write(tmp_path / "m", {"001_table": "CREATE TABLE a (n INTEGER);"})
    db_path = tmp_path / "app.db"
    migrate(db_path, folder)
    migrate(db_path, folder)  # would fail with "table a already exists" if re-applied
    assert _version(db_path) == 1


def test_existing_database_is_copied_before_migrating(tmp_path: Path) -> None:
    db_path = tmp_path / "app.db"
    db = sqlite3.connect(db_path)
    db.executescript("CREATE TABLE x (a); PRAGMA user_version=1;")
    db.close()
    folder = _write(
        tmp_path / "m",
        {
            "001_x": "CREATE TABLE IF NOT EXISTS x (a);",
            "002_col": "ALTER TABLE x ADD COLUMN b;",
        },
    )
    migrate(db_path, folder)
    backup = tmp_path / "app.db.pre-v2"
    assert backup.exists()
    assert _version(backup) == 1
    assert _version(db_path) == 2


def test_newer_database_is_refused(tmp_path: Path) -> None:
    db_path = tmp_path / "app.db"
    db = sqlite3.connect(db_path)
    db.execute("PRAGMA user_version=5")
    db.close()
    folder = _write(tmp_path / "m", {"001_table": "CREATE TABLE a (n INTEGER);"})
    with pytest.raises(AppError) as err:
        migrate(db_path, folder)
    assert err.value.code == "DB_TOO_NEW"
    assert _version(db_path) == 5
    assert "a" not in _tables(db_path)


def test_failed_migration_rolls_back_everything(tmp_path: Path) -> None:
    folder = _write(
        tmp_path / "m",
        {
            "001_a": "CREATE TABLE a (n INTEGER);",
            "002_bad": "CREATE TABLE b (n INTEGER); CREATE TABLE a (n INTEGER);",
        },
    )
    db_path = tmp_path / "app.db"
    with pytest.raises(sqlite3.OperationalError):
        migrate(db_path, folder)
    assert _version(db_path) == 0
    assert _tables(db_path) == set()


def test_concurrent_first_run_applies_once(tmp_path: Path) -> None:
    folder = _write(
        tmp_path / "m",
        {"001_seed": "CREATE TABLE a (n INTEGER); INSERT INTO a VALUES (1);"},
    )
    db_path = tmp_path / "app.db"
    errors: list[BaseException] = []

    def run() -> None:
        try:
            migrate(db_path, folder)
        except BaseException as exc:
            errors.append(exc)

    threads = [threading.Thread(target=run) for _ in range(6)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert errors == []
    assert _version(db_path) == 1
    db = sqlite3.connect(db_path)
    try:
        assert db.execute("SELECT COUNT(*) FROM a").fetchone()[0] == 1
    finally:
        db.close()


# Frozen v0.2.0 schema: the database shape that existing installs carry.
V020_SCHEMA = """
CREATE TABLE books (
  id TEXT PRIMARY KEY, title TEXT NOT NULL, original_filename TEXT NOT NULL,
  chapter_count INTEGER NOT NULL, created_at TEXT NOT NULL);
CREATE TABLE jobs (
  id TEXT PRIMARY KEY,
  book_id TEXT NOT NULL REFERENCES books(id) ON DELETE CASCADE,
  status TEXT NOT NULL, voice_id TEXT NOT NULL, language TEXT NOT NULL, speed REAL NOT NULL,
  bitrate_kbps INTEGER NOT NULL, include_code_blocks INTEGER NOT NULL,
  total_chunks INTEGER NOT NULL DEFAULT 0, completed_chunks INTEGER NOT NULL DEFAULT 0,
  progress_percent INTEGER NOT NULL DEFAULT 0, current_chapter TEXT,
  error_code TEXT, error_message TEXT,
  created_at TEXT NOT NULL, started_at TEXT, completed_at TEXT);
"""
STAMP = "2026-01-01T00:00:00+00:00"


def _seed_v020(path: Path) -> None:
    db = sqlite3.connect(path)
    db.executescript(V020_SCHEMA)
    db.execute("INSERT INTO books VALUES ('b1','T','t.md',1,?)", (STAMP,))
    db.execute(
        "INSERT INTO jobs (id,book_id,status,voice_id,language,speed,bitrate_kbps,"
        "include_code_blocks,created_at) VALUES ('j1','b1','completed','v','en-us',1.0,192,0,?)",
        (STAMP,),
    )
    db.commit()
    db.close()


def test_fresh_store_is_at_baseline(tmp_path: Path) -> None:
    path = tmp_path / "app.db"
    Store(path)
    assert _version(path) == 2
    assert {"books", "jobs"} <= _tables(path)


def test_v020_database_is_adopted_unchanged(tmp_path: Path) -> None:
    path = tmp_path / "app.db"
    _seed_v020(path)
    store = Store(path)
    assert store.get_book("b1").status == "completed"
    assert store.get_job("j1").status == "completed"
    assert _version(path) == 2
    backup = tmp_path / "app.db.pre-v2"
    assert backup.exists()
    assert _version(backup) == 0


def test_concurrent_stores_adopt_once(tmp_path: Path) -> None:
    path = tmp_path / "app.db"
    _seed_v020(path)
    errors: list[BaseException] = []

    def start() -> None:
        try:
            Store(path)
        except BaseException as exc:
            errors.append(exc)

    threads = [threading.Thread(target=start) for _ in range(6)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert errors == []
    assert _version(path) == 2
    backups = list(tmp_path.glob("app.db.pre-v*"))
    assert backups == [tmp_path / "app.db.pre-v2"]
    assert _version(backups[0]) == 0  # taken before the first migration, never after


def _columns(path: Path, table: str) -> list[str]:
    db = sqlite3.connect(path)
    try:
        return [r[1] for r in db.execute(f"PRAGMA table_info({table})")]
    finally:
        db.close()


def test_fresh_store_has_chapters_and_book_duration(tmp_path: Path) -> None:
    path = tmp_path / "app.db"
    Store(path)
    assert _columns(path, "chapters") == [
        "book_id", "number", "title", "start_seconds", "duration_seconds",
    ]  # fmt: skip
    assert "duration_seconds" in _columns(path, "books")


def test_v020_adoption_keeps_rows_and_leaves_new_data_empty(tmp_path: Path) -> None:
    path = tmp_path / "app.db"
    _seed_v020(path)
    Store(path)
    db = sqlite3.connect(path)
    try:
        assert db.execute("SELECT duration_seconds FROM books WHERE id='b1'").fetchone() == (None,)
        assert db.execute("SELECT COUNT(*) FROM chapters").fetchone() == (0,)
        assert db.execute("SELECT COUNT(*) FROM jobs").fetchone() == (1,)
    finally:
        db.close()


def test_chapter_rows_cascade_and_allow_duplicate_titles(tmp_path: Path) -> None:
    path = tmp_path / "app.db"
    store = Store(path)
    store.create_book("b1", "T", "t.md", 2)
    db = sqlite3.connect(path)
    db.execute("PRAGMA foreign_keys=ON")
    try:
        db.execute("INSERT INTO chapters (book_id, number, title) VALUES ('b1', 1, 'Same')")
        db.execute("INSERT INTO chapters (book_id, number, title) VALUES ('b1', 2, 'Same')")
        with pytest.raises(sqlite3.IntegrityError):
            db.execute("INSERT INTO chapters (book_id, number, title) VALUES ('b1', 2, 'X')")
        db.commit()
    finally:
        db.close()
    store.delete_book("b1")
    db = sqlite3.connect(path)
    try:
        assert db.execute("SELECT COUNT(*) FROM chapters").fetchone() == (0,)
    finally:
        db.close()

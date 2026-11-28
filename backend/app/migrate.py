"""Versioned SQL migrations, tracked by PRAGMA user_version (D-023)."""

import re
import shutil
import sqlite3
from pathlib import Path

from app.errors import AppError

_NAME = re.compile(r"^(\d+)_.+\.sql$")


def _steps(folder: Path) -> list[tuple[int, Path]]:
    found = ((int(m.group(1)), p) for p in folder.glob("*.sql") if (m := _NAME.match(p.name)))
    return sorted(found)


def _run_script(db: sqlite3.Connection, script: str) -> None:
    """Run statements one by one; executescript would COMMIT and break atomicity."""
    buf = ""
    for ch in script:
        buf += ch
        if ch == ";" and sqlite3.complete_statement(buf):
            db.execute(buf)
            buf = ""
    if buf.strip():
        db.execute(buf)


def _apply(db: sqlite3.Connection, db_path: Path, steps: list[tuple[int, Path]]) -> None:
    latest = steps[-1][0] if steps else 0
    current = int(db.execute("PRAGMA user_version").fetchone()[0])  # re-read under the lock
    if current > latest:
        raise AppError("DB_TOO_NEW", "Database is newer than this version of the app.", 500)
    pending = [(v, p) for v, p in steps if v > current]
    if not pending:
        return
    if db.execute("SELECT 1 FROM sqlite_master LIMIT 1").fetchone():
        shutil.copy2(db_path, db_path.with_name(f"{db_path.name}.pre-v{latest}"))
    for _, path in pending:
        _run_script(db, path.read_text(encoding="utf-8"))
    db.execute(f"PRAGMA user_version={latest}")


def migrate(db_path: Path, folder: Path) -> None:
    """Apply pending migrations in one transaction; safe if api and worker start together."""
    steps = _steps(folder)
    db = sqlite3.connect(db_path, timeout=30, isolation_level=None)
    try:
        db.execute("BEGIN IMMEDIATE")
        try:
            _apply(db, db_path, steps)
            db.execute("COMMIT")
        except BaseException:
            db.execute("ROLLBACK")
            raise
    finally:
        db.close()

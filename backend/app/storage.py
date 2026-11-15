"""Server-controlled storage paths. IDs must be UUIDs; results never escape the root."""

import shutil
import uuid
from pathlib import Path

from app.errors import AppError


def book_dir(root: Path, book_id: str) -> Path:
    """Return `root/<uuid>`, rejecting non-UUID ids, traversal and symlink escapes."""
    try:
        clean_id = str(uuid.UUID(book_id))
    except ValueError:
        raise AppError("INVALID_ID", "Invalid identifier.", 404) from None
    resolved_root = root.resolve()
    path = (resolved_root / clean_id).resolve()
    if not path.is_relative_to(resolved_root) or path.parent != resolved_root:
        raise AppError("INVALID_PATH", "Invalid storage path.", 404)
    return path


def remove_tree(root: Path, book_id: str) -> None:
    path = book_dir(root, book_id)
    if path.exists():
        shutil.rmtree(path)

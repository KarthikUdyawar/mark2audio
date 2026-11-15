import uuid
from pathlib import Path

import pytest

from app.config import Settings
from app.storage import book_dir
from app.store import Store
from app.tts import FakeTts


@pytest.fixture
def settings(tmp_path: Path) -> Settings:
    s = Settings(data_dir=tmp_path / "data", model_dir=tmp_path / "models", chunk_max_chars=40,
                 silence_ms=50)  # fmt: skip
    s.ensure_dirs()
    return s


@pytest.fixture
def store(settings: Settings) -> Store:
    return Store(settings.db_path)


@pytest.fixture
def engine() -> FakeTts:
    return FakeTts()


def add_book(
    settings: Settings, store: Store, text: str = "# One\nHello there. Second sentence.\n"
) -> str:
    book_id = str(uuid.uuid4())
    folder = book_dir(settings.uploads_dir, book_id)
    folder.mkdir(parents=True)
    (folder / "source.md").write_text(text, encoding="utf-8")
    store.create_book(book_id, "My Book", "my.md", 1)
    return book_id

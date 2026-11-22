from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.api import create_app
from app.config import Settings
from app.store import Store
from app.tts import FakeTts
from app.worker import run_pending

MD = b"# My Book\nHello there. Second sentence.\n\n# Part Two\nMore text.\n"
CONVERT = {"voice_id": "fake_a", "language": "en-us", "speed": 1.0, "bitrate_kbps": 128}


@pytest.fixture
def client(settings: Settings) -> TestClient:
    return TestClient(create_app(settings, FakeTts()))


def upload(client: TestClient, name: str = "book.md", data: bytes = MD) -> dict[str, object]:
    res = client.post("/api/v1/books/upload", files={"file": (name, data, "text/markdown")})
    assert res.status_code == 201, res.text
    return res.json()  # type: ignore[no-any-return]


def test_upload_lists_and_outlines(client: TestClient) -> None:
    book = upload(client)
    assert (book["title"], book["status"], book["chapter_count"]) == ("My Book", "uploaded", 2)
    assert [b["id"] for b in client.get("/api/v1/books").json()] == [book["id"]]
    detail = client.get(f"/api/v1/books/{book['id']}").json()
    assert [c["title"] for c in detail["chapters"]] == ["My Book", "Part Two"]


@pytest.mark.parametrize(
    "name,data,code",
    [
        ("a.txt", b"# hi\ntext", "UNSUPPORTED_TYPE"),
        ("a.md", b"", "EMPTY_FILE"),
        ("a.md", b"\xff\xfe\x00bad", "INVALID_ENCODING"),
        ("a.md", b"# \n```\nx\n```\n", "NO_TEXT"),
    ],
)
def test_upload_rejections(client: TestClient, name: str, data: bytes, code: str) -> None:
    res = client.post("/api/v1/books/upload", files={"file": (name, data)})
    assert res.status_code == 400 and res.json()["error"]["code"] == code


def test_oversized_upload_rejected(settings: Settings) -> None:
    small = Settings(**{**settings.__dict__, "max_upload_bytes": 10})
    res = TestClient(create_app(small, FakeTts())).post(
        "/api/v1/books/upload", files={"file": ("a.md", b"# x\n" * 10)}
    )
    assert res.status_code == 413 and res.json()["error"]["code"] == "FILE_TOO_LARGE"


def test_traversal_filename_is_display_only(
    client: TestClient, settings: Settings, tmp_path: Path
) -> None:
    book = upload(client, name="../../evil.md")
    assert (
        not (tmp_path / "evil.md").exists() and not (settings.data_dir.parent / "evil.md").exists()
    )
    assert client.get("/api/v1/books").json()[0]["original_filename"] == "evil.md"
    assert (settings.uploads_dir / str(book["id"]) / "source.md").is_file()


def test_voices_and_health(client: TestClient) -> None:
    assert client.get("/api/v1/voices").json() == [
        {"id": "fake_a", "name": "Fake A", "language": "en-us", "available": True}
    ]
    assert client.get("/api/v1/health").json()["status"] == "ok"


@pytest.mark.parametrize(
    "patch",
    [{"voice_id": "nope"}, {"speed": 2.0}, {"bitrate_kbps": 100}, {"language": "fr"}],
)
def test_convert_validation(client: TestClient, patch: dict[str, object]) -> None:
    book = upload(client)
    res = client.post(f"/api/v1/books/{book['id']}/convert", json={**CONVERT, **patch})
    assert res.status_code in (400, 422) and "code" in res.json()["error"]


def test_full_flow_convert_stream_download_delete(
    client: TestClient, settings: Settings, store: Store, engine: FakeTts
) -> None:
    book = upload(client)
    bid = book["id"]
    assert client.get(f"/api/v1/books/{bid}/audio").json()["error"]["code"] == "NOT_READY"
    job = client.post(f"/api/v1/books/{bid}/convert", json=CONVERT).json()
    assert job["status"] == "queued"
    assert client.post(f"/api/v1/books/{bid}/convert", json=CONVERT).status_code == 409
    run_pending(store, engine, settings)
    done = client.get(f"/api/v1/jobs/{job['id']}").json()
    assert (done["status"], done["progress_percent"], done["error"]) == ("completed", 100, None)
    audio = client.get(f"/api/v1/books/{bid}/audio")
    assert audio.status_code == 200 and audio.headers["content-type"] == "audio/mpeg"
    assert (
        'filename="My_Book.mp3"' in audio.headers["content-disposition"]
        and len(audio.content) > 1000
    )
    assert client.get(f"/api/v1/books/{bid}").json()["status"] == "completed"
    assert client.delete(f"/api/v1/books/{bid}").status_code == 204
    assert (
        not (settings.audio_dir / str(bid)).exists()
        and not (settings.uploads_dir / str(bid)).exists()
    )
    assert client.get(f"/api/v1/books/{bid}").status_code == 404


def test_cancel_queued_job_and_terminal_cancel_conflicts(client: TestClient) -> None:
    bid = upload(client)["id"]
    job = client.post(f"/api/v1/books/{bid}/convert", json=CONVERT).json()
    assert client.post(f"/api/v1/jobs/{job['id']}/cancel").json()["status"] == "cancelled"
    assert client.post(f"/api/v1/jobs/{job['id']}/cancel").status_code == 409


def test_bad_ids_are_404_never_500(client: TestClient) -> None:
    for path in ("/books/..%2F..%2Fetc", "/books/not-a-uuid/audio", "/jobs/zzz"):
        assert client.get("/api/v1" + path).status_code == 404


def test_detail_with_missing_source_is_stable_error(client: TestClient, settings: Settings) -> None:
    bid = str(upload(client)["id"])
    (settings.uploads_dir / bid / "source.md").unlink()
    res = client.get(f"/api/v1/books/{bid}")
    assert res.status_code == 500 and res.json()["error"]["code"] == "SOURCE_MISSING"


def test_failed_upload_leaves_no_orphan_folder(
    settings: Settings, monkeypatch: pytest.MonkeyPatch
) -> None:
    def boom(*_: object) -> None:
        raise RuntimeError("db down")

    monkeypatch.setattr(Store, "create_book", boom)
    client = TestClient(create_app(settings, FakeTts()), raise_server_exceptions=False)
    res = client.post("/api/v1/books/upload", files={"file": ("a.md", MD)})
    assert res.status_code == 500
    assert list(settings.uploads_dir.iterdir()) == []

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import create


def test_create_builds_app_from_environment(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("M2A_DATA_DIR", str(tmp_path / "data"))
    monkeypatch.setenv("M2A_FAKE_TTS", "1")
    client = TestClient(create())
    health = client.get("/api/v1/health").json()
    assert health["voices"] == 1
    assert [v["id"] for v in client.get("/api/v1/voices").json()] == ["fake_a"]
    assert (tmp_path / "data" / "uploads").is_dir()

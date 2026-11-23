"""OpenAPI contract: typed responses, one documented error shape, stable field names."""

from collections.abc import Iterator
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.api import create_app
from app.config import Settings
from app.tts import FakeTts

Json = dict[str, Any]
CONVERT = {"voice_id": "fake_a", "language": "en-us", "speed": 1.0, "bitrate_kbps": 128}
BOOK_KEYS = {
    "id",
    "title",
    "original_filename",
    "status",
    "chapter_count",
    "created_at",
    "duration_seconds",
}
JOB_KEYS = {
    "id",
    "book_id",
    "status",
    "progress_percent",
    "completed_chunks",
    "total_chunks",
    "current_chapter",
    "error",
}


@pytest.fixture
def client(settings: Settings) -> TestClient:
    return TestClient(create_app(settings, FakeTts()))


@pytest.fixture
def spec(client: TestClient) -> Json:
    return dict(client.get("/openapi.json").json())


def _operations(spec: Json) -> Iterator[tuple[str, Json]]:
    for path, item in spec["paths"].items():
        for method, op in item.items():
            yield f"{method.upper()} {path}", op


def _untyped(schema: Json) -> bool:
    """Return True if a schema says nothing about its shape (bare object, empty, any)."""
    if "$ref" in schema:
        return False
    if "anyOf" in schema:
        return any(_untyped(s) for s in schema["anyOf"] if s.get("type") != "null")
    kind = schema.get("type")
    if kind == "array":
        return _untyped(schema.get("items", {}))
    if kind == "object":
        return "properties" not in schema
    return kind is None


def test_every_json_response_is_typed(spec: Json) -> None:
    for name, op in _operations(spec):
        for code, response in op["responses"].items():
            body = response.get("content", {}).get("application/json")
            if body is not None:
                assert not _untyped(body.get("schema", {})), f"{name} {code}"


def test_every_success_response_declares_its_content(spec: Json) -> None:
    for name, op in _operations(spec):
        for code, response in op["responses"].items():
            if code == "204":
                assert not response.get("content"), name
            elif code.startswith("2"):
                assert response.get("content"), f"{name} {code}"


def test_audio_response_is_declared_as_binary_mpeg(spec: Json) -> None:
    ok = spec["paths"]["/api/v1/books/{book_id}/audio"]["get"]["responses"]["200"]
    assert ok["content"]["audio/mpeg"]["schema"] == {"type": "string", "format": "binary"}
    assert "application/json" not in ok["content"]


def test_errors_share_one_documented_shape(spec: Json) -> None:
    schemas = spec["components"]["schemas"]
    assert "HTTPValidationError" not in schemas  # the handler returns the app error shape
    assert set(schemas["ErrorResponse"]["properties"]) == {"error"}
    assert set(schemas["ErrorBody"]["properties"]) == {"code", "message"}
    for name, op in _operations(spec):
        assert "500" in op["responses"], name  # catch-all INTERNAL
        for code, response in op["responses"].items():
            if code[0] in "45":
                ref = response["content"]["application/json"]["schema"]["$ref"]
                assert ref == "#/components/schemas/ErrorResponse", f"{name} {code}"


def test_no_component_property_is_untyped(spec: Json) -> None:
    for model, schema in spec["components"]["schemas"].items():
        for prop, definition in schema.get("properties", {}).items():
            assert not _untyped(definition), f"{model}.{prop}"


def test_response_field_names_are_unchanged(client: TestClient) -> None:
    upload = client.post("/api/v1/books/upload", files={"file": ("a.md", b"# A\nText here.\n")})
    book = upload.json()
    assert set(book) == BOOK_KEYS
    job = client.post(f"/api/v1/books/{book['id']}/convert", json=CONVERT).json()
    assert set(job) == JOB_KEYS
    detail = client.get(f"/api/v1/books/{book['id']}").json()
    assert set(detail) == BOOK_KEYS | {"chapters", "latest_job"}
    assert set(detail["chapters"][0]) == {
        "number",
        "title",
        "start_seconds",
        "duration_seconds",
    }
    assert set(detail["latest_job"]) == JOB_KEYS
    assert set(client.get("/api/v1/books").json()[0]) == BOOK_KEYS
    assert set(client.get("/api/v1/voices").json()[0]) == {"id", "name", "language", "available"}
    assert set(client.get("/api/v1/health").json()) == {"status", "ffmpeg", "voices"}
    assert set(client.post(f"/api/v1/jobs/{job['id']}/cancel").json()) == JOB_KEYS

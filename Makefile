.PHONY: install hooks api worker test lint typecheck format up down logs model
install:   ; cd backend && uv sync -q --extra tts
hooks:     ; uv run --project backend pre-commit install --install-hooks
api:       ; cd backend && M2A_DATA_DIR=../data M2A_MODEL_DIR=../models/kokoro uv run uvicorn app.main:create --factory --reload --port 8000
worker:    ; cd backend && M2A_DATA_DIR=../data M2A_MODEL_DIR=../models/kokoro uv run python -m app.worker
test:      ; cd backend && uv run pytest
lint:      ; SKIP=no-commit-to-branch,mypy uv run --project backend pre-commit run --all-files && cd backend && uv run bandit -q -r app
typecheck: ; cd backend && uv run mypy app tests
format:    ; cd backend && uv run ruff format . && uv run ruff check --fix .
up:        ; docker compose up -d --build
down:      ; docker compose down
logs:      ; docker compose logs -f
# One-time, needs internet. Record sha256 + license before trusting (docs/TODO.md M0).
model:
	curl -L -o models/kokoro/kokoro-v1.0.onnx https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.onnx
	curl -L -o models/kokoro/voices-v1.0.bin https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin
	sha256sum models/kokoro/*

.PHONY: install api worker test lint typecheck format up down logs model
install:   ; cd backend && uv venv -q && uv pip install -q -e ".[dev,tts]"
api:       ; cd backend && M2A_DATA_DIR=../data M2A_MODEL_DIR=../models/kokoro uvicorn app.main:create --factory --reload --port 8000
worker:    ; cd backend && M2A_DATA_DIR=../data M2A_MODEL_DIR=../models/kokoro python -m app.worker
test:      ; cd backend && pytest
lint:      ; cd backend && ruff check . && ruff format --check . && bandit -q -r app
typecheck: ; cd backend && mypy app tests
format:    ; cd backend && ruff format . && ruff check --fix .
up:        ; docker compose up -d --build
down:      ; docker compose down
logs:      ; docker compose logs -f
# One-time, needs internet. Record sha256 + license before trusting (docs/TODO.md M0).
model:
	curl -L -o models/kokoro/kokoro-v1.0.onnx https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.onnx
	curl -L -o models/kokoro/voices-v1.0.bin https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin
	sha256sum models/kokoro/*

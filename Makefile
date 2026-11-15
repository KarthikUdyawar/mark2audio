.PHONY: install hooks api worker test lint typecheck format up down logs model ci trivy sonar
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
# Local CI via act. First run asks for an image size: choose Medium.
ci:        ; act push -j backend -P ubuntu-24.04=catthehacker/ubuntu:act-24.04
# One-time, needs internet. Record sha256 + license before trusting (docs/TODO.md M0).
model:
	curl -L -o models/kokoro/kokoro-v1.0.onnx https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.onnx
	curl -L -o models/kokoro/voices-v1.0.bin https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin
	sha256sum models/kokoro/*

# Optional tooling, off by default (no hook, no CI). Config: .env.tools (see .env.tools.example).
-include .env.tools
TRIVY_DIR ?= ../trivy-docker-scanner
SONAR_HOST_URL ?= http://localhost:9000
export SONAR_HOST_URL SONAR_TOKEN
trivy:
	docker compose build api
	$(MAKE) -C $(TRIVY_DIR) scan-critical IMAGE=mark2audio:local
sonar:
	@test -n "$$SONAR_TOKEN" || { echo 'SONAR_TOKEN missing: copy .env.tools.example to .env.tools'; exit 1; }
	cd backend && uv run pytest -q --cov-report=xml:coverage.xml
	@docker run --rm --network host -e SONAR_HOST_URL -e SONAR_TOKEN \
	  -v "$(CURDIR)/backend:$(CURDIR)/backend" -w "$(CURDIR)/backend" \
	  sonarsource/sonar-scanner-cli -Dsonar.projectBaseDir="$(CURDIR)/backend"

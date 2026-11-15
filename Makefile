.DEFAULT_GOAL := help

.PHONY: help setup install hooks api worker test lint typecheck format check \
        up down logs ci model trivy sonar tree status clean

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

PROJECT_NAME := Mark2Audio

BACKEND_DIR := backend
DATA_DIR := data
MODEL_DIR := models/kokoro

STRUCTURE := docs/STRUCTURE.md

TREE_IGNORE := .git|backups|__pycache__|.venv|node_modules|.mypy_cache|.ruff_cache|.pytest_cache|.coverage|data|models/kokoro/*

TRIVY_DIR ?= ../trivy-docker-scanner
SONAR_HOST_URL ?= http://localhost:9000

-include .env.tools

export SONAR_HOST_URL SONAR_TOKEN

# ---------------------------------------------------------------------------
# Help
# ---------------------------------------------------------------------------

help: ## list available targets
	@echo "$(PROJECT_NAME) - Development Commands"
	@echo ""
	@grep -hE '^[a-zA-Z0-9_-]+:.*## ' $(MAKEFILE_LIST) | \
		awk -F':.*## ' '{printf "  %-12s %s\n", $$1, $$2}'
	@echo ""

# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------

setup: ## install dependencies and configure pre-commit hooks
	cd $(BACKEND_DIR) && uv sync --extra tts
	uv tool install pre-commit
	pre-commit install --install-hooks

install: ## install backend dependencies
	cd $(BACKEND_DIR) && uv sync -q --extra tts

hooks: ## run all pre-commit hooks on all files
	SKIP=no-commit-to-branch uv run --project $(BACKEND_DIR) pre-commit run --all-files

# ---------------------------------------------------------------------------
# Development
# ---------------------------------------------------------------------------

api: ## start FastAPI development server
	cd $(BACKEND_DIR) && \
		M2A_DATA_DIR=../$(DATA_DIR) \
		M2A_MODEL_DIR=../$(MODEL_DIR) \
		uv run uvicorn app.main:create --factory --reload --port 8000

worker: ## start background worker
	cd $(BACKEND_DIR) && \
		M2A_DATA_DIR=../$(DATA_DIR) \
		M2A_MODEL_DIR=../$(MODEL_DIR) \
		uv run python -m app.worker

# ---------------------------------------------------------------------------
# Code Quality
# ---------------------------------------------------------------------------

lint: ## run Ruff and Bandit
	cd $(BACKEND_DIR) && uv run ruff check .
	cd $(BACKEND_DIR) && uv run ruff format --check .
	cd $(BACKEND_DIR) && uv run bandit -q -r app

format: ## automatically fix Ruff lint and formatting issues
	cd $(BACKEND_DIR) && uv run ruff check --fix .
	cd $(BACKEND_DIR) && uv run ruff format .

typecheck: ## run strict MyPy type checking
	cd $(BACKEND_DIR) && uv run mypy app tests

test: ## run pytest
	cd $(BACKEND_DIR) && uv run pytest

check: lint typecheck test ## complete local quality gate

# ---------------------------------------------------------------------------
# Docker
# ---------------------------------------------------------------------------

up: ## build and start Docker services
	docker compose up -d --build

down: ## stop Docker services
	docker compose down

logs: ## follow Docker Compose logs
	docker compose logs -f

# ---------------------------------------------------------------------------
# Local CI
# ---------------------------------------------------------------------------

ci: ## run GitHub Actions backend job locally using act
	act push -j backend -P ubuntu-24.04=catthehacker/ubuntu:act-24.04

# ---------------------------------------------------------------------------
# Kokoro Model
# ---------------------------------------------------------------------------

model: ## download Kokoro ONNX model and voice data (one-time)
	mkdir -p $(MODEL_DIR)
	curl -fL --retry 3 -o $(MODEL_DIR)/kokoro-v1.0.onnx \
		https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.onnx
	curl -fL --retry 3 -o $(MODEL_DIR)/voices-v1.0.bin \
		https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin
	sha256sum $(MODEL_DIR)/*

# ---------------------------------------------------------------------------
# Optional Security Scanning
# ---------------------------------------------------------------------------

trivy: ## build API image and scan critical vulnerabilities
	docker compose build api
	$(MAKE) -C $(TRIVY_DIR) scan-critical IMAGE=mark2audio:local

# ---------------------------------------------------------------------------
# SonarQube
# ---------------------------------------------------------------------------

sonar: ## run tests with coverage and SonarQube analysis
	@test -n "$$SONAR_TOKEN" || { \
		echo 'SONAR_TOKEN missing: copy .env.tools.example to .env.tools'; \
		exit 1; \
	}
	cd $(BACKEND_DIR) && uv run pytest -q --cov-report=xml:coverage.xml
	docker run --rm --network host \
		-e SONAR_HOST_URL \
		-e SONAR_TOKEN \
		-v "$(CURDIR)/$(BACKEND_DIR):$(CURDIR)/$(BACKEND_DIR)" \
		-w "$(CURDIR)/$(BACKEND_DIR)" \
		sonarsource/sonar-scanner-cli \
		-Dsonar.projectBaseDir="$(CURDIR)/$(BACKEND_DIR)"

# ---------------------------------------------------------------------------
# Repository Documentation
# ---------------------------------------------------------------------------

tree: ## generate repository structure documentation
	@command -v tree >/dev/null || { \
		echo 'Install tree: sudo apt install tree'; \
		exit 1; \
	}
	@mkdir -p docs
	@{ \
		printf '# $(PROJECT_NAME): Repository Structure\n\n'; \
		printf 'Generated by `make tree`. Do not edit manually.\n\n```text\n'; \
		tree -a --gitignore --dirsfirst --noreport -I '$(TREE_IGNORE)'; \
		printf '```\n'; \
	} > $(STRUCTURE)
	@echo "Generated $(STRUCTURE)"

# ---------------------------------------------------------------------------
# Git Status
# ---------------------------------------------------------------------------

status: ## show branch, working tree, stashes and recent commits
	@git status -sb
	@echo ""
	@echo "--- Stashes ---"
	@git stash list
	@echo ""
	@echo "--- Recent commits ---"
	@git log --oneline -10

# ---------------------------------------------------------------------------
# Cleanup
# ---------------------------------------------------------------------------

clean: ## remove Python and testing caches (preserves virtualenv)
	find $(BACKEND_DIR) -name __pycache__ -type d -prune -exec rm -rf {} +
	rm -rf $(BACKEND_DIR)/.mypy_cache
	rm -rf $(BACKEND_DIR)/.ruff_cache
	rm -rf $(BACKEND_DIR)/.pytest_cache
	rm -rf $(BACKEND_DIR)/.coverage
	rm -rf $(BACKEND_DIR)/coverage.xml

# Mark2Audio — Decisions

Append-only log. Never edit an accepted entry; add a new one that supersedes it.
Format: `D-NNN`, date, status, context, decision, consequence.
Related: [ARCHITECTURE.md](ARCHITECTURE.md) · [ROADMAP.md](ROADMAP.md) ·
[CLAUDE.md](../CLAUDE.md#21-project-mark2audio).

D-001 to D-005 were recorded retroactively from the MVP baseline (commit `cd46e5b`).

## D-001 — Modular monolith, SQLite, no external services

- Date: 2026-11-15 · Status: accepted
- Context: single-user, local-first, offline tool.
- Decision: two processes (api, worker) from one image; SQLite for metadata and job state; no
  Redis, RabbitMQ, PostgreSQL, MinIO or cloud APIs.
- Consequence: no outbound network at conversion time. Revisit only with measured need.

## D-002 — Local TTS behind an interface (Kokoro ONNX)

- Date: 2026-11-15 · Status: accepted, unverified with real model
- Context: need open, local speech synthesis.
- Decision: `TtsEngine` protocol in `tts.py`; Kokoro ONNX adapter in `tts_kokoro.py`; `FakeTts`
  (sine tones) for tests and demos.
- Consequence: adapter assumptions and model checksum/license still to verify (see ROADMAP).

## D-003 — Vanilla-JS UI served by the API

- Date: 2026-11-15 · Status: accepted (deviates from the original React/Vite/Tailwind plan)
- Context: smallest thing that completes the workflow.
- Decision: single `static/index.html`, no build step, no frontend container.
- Consequence: UI rules in [DESIGN.md](DESIGN.md#rules) that assume TypeScript apply only after a
  rewrite. A React rewrite needs a new decision.

## D-004 — Stdlib `sqlite3`, no ORM or migration tool

- Date: 2026-11-15 · Status: accepted (deviates from SQLAlchemy 2.0 + Alembic plan)
- Decision: hand-written SQL in `store.py`; schema created with `CREATE TABLE IF NOT EXISTS`;
  short `BEGIN IMMEDIATE` transactions on fresh connections.
- Consequence: any schema change needs a migration decision before it ships.

## D-005 — Derived book status, no chapter table

- Date: 2026-11-15 · Status: accepted (deviates from the original data model)
- Decision: book status comes from the latest job; chapters are not persisted.
- Consequence: per-chapter audio or durations need a schema change (new decision).

## D-006 — Document set and sprint workflow

- Date: 2026-11-15 · Status: accepted
- Decision: `ROADMAP.md` (plan), `ARCHITECTURE.md` (backend as-built + rules), `DESIGN.md` (UI),
  `DECISION.md` (this log), `docs/sprints/Sn/{PRD,TODO}.md` per sprint. Docs describe what exists;
  each fact lives in one place and is linked elsewhere.
- Consequence: workflow detail lives in CLAUDE.md section 21.

## D-007 — Branching and releases

- Date: 2026-11-15 · Status: accepted
- Decision: `main`, `develop`, one `feature/*` branch per sprint, one commit per task, release
  merged to `main` and tagged `v0.S.0`. Free GitHub plan: no branch protection, rule enforced by
  convention.

## D-008 — Private repository

- Date: 2026-11-15 · Status: accepted
- Decision: repo is private and not open-sourced. No LICENSE, CONTRIBUTING or SECURITY files.
- Consequence: revisit before any publication; model and voice licenses still unchecked.

## D-009 — Working skills

- Date: 2026-11-15 · Status: accepted
- Decision: `tdd`, `ponytail`, `clean-code`, `handoff`; `caveman` (ultra) for chat replies only.
  `sprint` and `code-review` skills may be built with `skill-creator`.

## D-010 — Locked dependencies, one set of gate commands

- Date: 2026-11-15 · Status: accepted
- Decision: `backend/uv.lock` committed; Python minor pinned to 3.12 (`backend/.python-version`;
  Docker pins 3.12.7). Makefile targets run tools through `uv run`. Pre-commit (local hooks) and
  CI both call `make lint typecheck test`; hygiene hooks and a `no-commit-to-branch` guard on
  `main`/`develop` are added. CI installs the `tts` extra so the Kokoro adapter is type-checked.
- Consequence: change a gate in the Makefile only. Real-model smoke test never runs in CI.

## D-011 — Compose pins container paths

- Date: 2026-11-15 · Status: accepted
- Context: `.env` copied from `.env.example` holds native paths and overrides the image `ENV`.
- Decision: `environment` in `docker-compose.yml` sets `M2A_DATA_DIR=/data`,
  `M2A_MODEL_DIR=/models`.

## D-012 — Pre-commit config is the gate source; `act` for local CI

- Date: 2026-11-15 · Status: accepted · Supersedes the wiring in D-010 (pins unchanged)
- Decision: `.pre-commit-config.yaml` defines the lint checks (hygiene, gitleaks, codespell,
  pyproject-fmt, ruff, uv-lock, prettier, mypy). `make lint` runs all hooks except mypy and
  `no-commit-to-branch`, fixes files, and still runs bandit until D-014. `make typecheck` and
  `make test` are unchanged. CI and `make ci` (`act`) call the same make targets. Hooks: commit
  (checks), commit-msg (`feat|fix|docs|test|chore|ci|refactor|build|style|perf|revert: …` or
  `Merge …`), push (pytest). Commits to `main` and `develop` are blocked.
- Consequence: change checks in the hook config, not in CI. Merge commits need a conforming
  message. The commit that introduced the config used `--no-verify` (chicken-and-egg).

## D-013 — Trivy and SonarQube are opt-in

- Date: 2026-11-15 · Status: accepted
- Decision: they stay in their own repos (`trivy-docker-scanner`, `local-sonarqube`). This repo
  only has `make trivy` and `make sonar`: no hook, no CI job. Config lives in gitignored
  `.env.tools`, never `.env` (compose forwards `.env` into containers). Compose pins
  `image: mark2audio:local` so scanners get one stable name.
- Consequence: scans run only when asked. Sonar settings: `backend/sonar-project.properties`;
  the token exists only in `.env.tools`.

## D-014 — Ruff rule set replaces bandit

- Date: 2026-11-15 · Status: accepted · Supersedes the bandit part of D-012
- Context: ruff `S` rules (flake8-bandit) cover the checks bandit ran, in the same pass.
- Decision: `select = B D E F I N PL RUF S SIM UP`; `D1` (missing docstrings) is ignored because
  docstrings are required only where they clarify a contract. Per-file ignores, each with a
  reason comment, live in `backend/pyproject.toml`. bandit is removed from the dev group and
  `make lint`; `# nosec` comments are removed.
- Consequence: the "bandit or equivalent" rule in [ARCHITECTURE.md](ARCHITECTURE.md) is met by
  ruff `S`. Suppressions use `# noqa` or per-file ignores, never `# nosec`.

## D-015 — CI runs on develop, main, release and pull requests

- Date: 2026-11-15 · Status: accepted
- Context: a push to every `feature/**` branch started a GitHub Actions run. Sprint branches are
  pushed often and merged locally ([CLAUDE.md](../CLAUDE.md#21-project-mark2audio)).
- Decision: `ci.yml` triggers on pushes to `main`, `develop` and `release/**`, and on pull
  requests to `main` and `develop`. The pre-merge gate is `make ci` (`act`) plus `make check`.
- Consequence: a feature branch gets no remote CI until it is merged into `develop` or a PR is
  opened. Run `make ci` before every merge.

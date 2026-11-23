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

## D-016 — Sprint merge flow by pull request

- Date: 2026-11-21 · Status: accepted · Supersedes the merge wording in D-007 and D-015
- Context: S0 was released through GitHub pull requests (#1 into `develop`, #2 into `main`), not
  local merges. After the release, `main` and `develop` had identical trees, so a back-merge
  would only add a merge commit that `main` lacks, on every release.
- Decision: a sprint merges `feature/*` → `develop` by pull request, then `release/v0.N.0` →
  `main` by pull request. Both use a merge commit, never squash or rebase. Tag `v0.N.0` on the
  merge commit on `main`. Back-merge `main` → `develop` only when `main` has content `develop`
  lacks (for example a hotfix). PR title is `type: summary` with the same types as commits;
  labels: `chore`, `documentation`, `ci`, `sprint:Sn`, `no-behavior-change`; release PRs get
  `release` and `v0.N.0`.
- Consequence: CI runs on every PR ([D-015](#d-015--ci-runs-on-develop-main-release-and-pull-requests)),
  so `make ci` before opening the PR remains the pre-merge gate. Merge commits made on GitHub
  skip the local commit-msg hook, so the PR title carries the format. `v0.0.0` stays on the
  `develop` merge commit `b0aa8fe`, because a pushed tag does not move.

## D-017 — Model provenance, Kokoro verified locally

- Date: 2026-11-21 · Status: accepted · Supersedes the "unverified with real model" status of D-002
- Context: S1 ran the Kokoro adapter against the real model (smoke test, adapter audit, speed and
  memory measured, see [ARCHITECTURE.md](ARCHITECTURE.md)). `make model` URLs were written from
  memory.
- Decision: model files come from the GitHub release `model-files-v1.0` of
  `thewh1teagle/kokoro-onnx`: `kokoro-v1.0.onnx` and `voices-v1.0.bin`. Their URLs and sha256 are
  pinned in the `Makefile` (the only place hashes are stored), and `make model` fails on a
  mismatch. Release `model-files-v1.1` also exists, ships a different `kokoro-v1.0.onnx` (other
  bytes and size), and is not verified. GitHub published no digest for the v1.0 onnx; its pin is
  the hash of the file the smoke test passed on, with a size equal to the upstream asset.
- Licenses, as stated in the upstream README on 2026-11-21: `kokoro-onnx` MIT, Kokoro model
  Apache 2.0. Per-voice terms and the Kokoro-82M model card were not checked.
- Consequence: the repository is private ([D-008](#d-008--private-repository)); check voice
  terms before any distribution. Moving to v1.1 or another model needs a new decision and a new
  smoke run.

## D-018 — Docker image installs from `uv.lock`

- Date: 2026-11-21 · Status: accepted · Completes [D-010](#d-010--locked-dependencies-one-set-of-gate-commands)
  for the image
- Context: the image was built with `pip install ".[tts]"`, which resolves fresh versions. S1
  found it shipped fastapi 0.165.0, numpy 2.5.5, pydantic 2.14.4 and python-multipart 0.0.34
  against 0.163.0, 2.5.4, 2.14.3 and 0.0.33 in `backend/uv.lock`. The tested set is the lock, not
  what the image ran.
- Decision: the Dockerfile copies the `uv` binary from the pinned `ghcr.io/astral-sh/uv:0.13.6`
  image (the version CI uses) and runs `uv sync --locked --no-dev --extra tts
--no-install-project` into `/opt/venv`; the app source is copied afterwards. The build fails if
  `uv.lock` is stale.
- Consequence: image dependencies equal the lock. The `uv` binary stays in the image. Change the
  `uv` version in the Dockerfile and `ci.yml` together. Dependency updates go through `uv lock`.

## D-019 — GitHub Actions pinned by commit SHA

- Date: 2026-11-21 · Status: accepted
- Context: `ci.yml` used floating tags (`checkout@v4`, `setup-uv@v6`, `cache@v4`), so upstream
  could change the code CI runs without any change here. Pre-commit hooks were already pinned.
- Decision: every `uses:` in `.github/workflows` is pinned to a full commit SHA with the version
  in a trailing comment. The SHA must be a commit: take the `^{}` line of
  `git ls-remote <repo> 'refs/tags/<tag>' 'refs/tags/<tag>^{}'` when it exists, else the plain
  line (a lightweight tag). Pinned in S1: `checkout` v4.4.0, `setup-uv` v6.8.0, `cache` v4.3.0.
- Consequence: updates are manual, no Dependabot. The `uv` version in `ci.yml` and the Dockerfile
  still changes together ([D-018](#d-018--docker-image-installs-from-uvlock)).

## D-020 — Worker health check by heartbeat file

- Date: 2026-11-22 · Status: accepted
- Context: technical rule Docker and operations 3 asks for a worker health check; the worker has
  none. A heartbeat touched only while idle goes stale during a long conversion.
- Decision: the worker touches `data/worker.heartbeat` after the model loads, on every idle poll,
  after every chunk and before encoding. Compose marks the worker healthy while the file is
  younger than 300 s (`start_period` 120 s for model load). Path and threshold are fixed, not
  env-driven. No schema change.
- Consequence: a single FFmpeg encode can exceed 300 s (timeout 1800 s) and show `unhealthy`.
  Harmless: compose does not restart on it. A DB heartbeat table was rejected (schema change,
  see [D-004](#d-004--stdlib-sqlite3-no-orm-or-migration-tool)).

## D-021 — API responses stay plain dicts

- Date: 2026-11-22 · Status: accepted
- Context: API rule 2 asks Pydantic schemas for request and response data. Requests are
  validated by Pydantic (`ConvertRequest`); responses are built by `_job_json` and `_book_json`
  and covered by API tests.
- Decision: keep plain dict responses. Recorded as a deviation, not rewritten.
- Consequence: no response schema in OpenAPI. Revisit if the UI is rewritten in TypeScript
  ([D-003](#d-003--vanilla-js-ui-served-by-the-api)), where typed responses matter.

## D-022 — SQLite and local disk stay the defaults; infrastructure lab is optional

- Date: 2026-11-22 · Status: accepted
- Context: three independent design reviews of the idea "PostgreSQL, Garage (S3) and React/TS"
  agreed that none solves a product problem for one user on one machine, and that object storage
  adds failure modes because FFmpeg needs local files anyway. The maintainer also wants to learn
  these technologies.
- Decision: SQLite and local disk are the defaults until a real requirement appears (multi-user,
  multi-machine, concurrent workers). PostgreSQL and S3-compatible storage may be added only as
  optional compose profiles in lab sprints, each with its own PRD and decision. The default
  install and the offline worker proof (`network_mode: none`) stay unchanged. No repository or
  storage interface is built before a second implementation is.
- Consequence: this changes technical rules Architecture and scope 3 and 4 in
  [ARCHITECTURE.md](ARCHITECTURE.md#technical-rules) for the optional profiles only. The lab
  track is in [ROADMAP.md](ROADMAP.md#lab-track-optional).

## D-023 — Versioned SQL migrations

- Date: 2026-11-22 · Status: accepted · Supersedes the "no migration tool" part of
  [D-004](#d-004--stdlib-sqlite3-no-orm-or-migration-tool) (stdlib `sqlite3` stays)
- Decision: ordered `.sql` files in `backend/app/migrations/`, tracked by `PRAGMA user_version`.
  A pending migration runs inside `BEGIN IMMEDIATE` and re-reads the version there, because the
  api and the worker both start the store. Before applying any migration to an existing database,
  the file is copied to `mark2audio.db.pre-vN`. A database newer than the code refuses to start.
  No Alembic, no ORM.
- Consequence: every schema change is a new numbered file with a test. The baseline migration
  keeps `CREATE TABLE IF NOT EXISTS`, so existing v0.2.0 databases are adopted unchanged.

## D-024 — Pydantic response models

- Date: 2026-11-22 · Status: accepted · Supersedes [D-021](#d-021--api-responses-stay-plain-dicts)
- Context: plain dict responses leave no response schema in OpenAPI, which blocks a generated
  TypeScript client.
- Decision: every public endpoint declares a `response_model`, and the error shape is documented
  in OpenAPI. Field names and values of existing responses do not change.
- Consequence: API rule 2 is met. Done in S3.

## D-025 — React/TypeScript approved for the lab track

- Date: 2026-11-22 · Status: accepted, scheduled as Lab 1 after D-024 lands
- Decision: the UI may be rewritten in React and TypeScript. Vite builds a static bundle served by
  the API process, with no frontend container. API types are generated from the OpenAPI schema and
  the generated file is checked in CI. The vanilla UI ([D-003](#d-003--vanilla-js-ui-served-by-the-api))
  stays until the rewrite reaches parity.
- Consequence: UI rules 1 to 3 in [DESIGN.md](DESIGN.md#rules) apply from that sprint.

## D-026 — Default tests stay offline and service-free

- Date: 2026-11-22 · Status: accepted
- Decision: `make test` needs no network, no Docker and no external service. Tests that need
  PostgreSQL or an object store are opt-in (pytest marker, compose service) and never part of the
  default gate or of CI's default job.
- Consequence: a SQLite fallback is not accepted as a stand-in for PostgreSQL tests.

## D-027 — Chapters table and stored durations

- Date: 2026-11-24 · Status: accepted · Supersedes the "no chapter table" part of
  [D-005](#d-005--derived-book-status-no-chapter-table) (derived book status stays)
- Context: FR-08 needs durations, and chapter export (S4) needs per-chapter data. Chapters are
  parsed on every use and never stored.
- Decision: migration `002` adds table `chapters` (`book_id` cascade, `number`, `title` TEXT NOT
  NULL DEFAULT '', `start_seconds` REAL NULL, `duration_seconds` REAL NULL; primary key
  `book_id, number`) and column `books.duration_seconds` REAL NULL.
  - Rows are written at upload, parsed with `include_code=False`. Books uploaded before S3 are
    backfilled once from `source.md`; a book that already has rows is left unchanged.
  - Start and duration stay NULL until a conversion completes. Backfill does not probe old audio.
  - On completion the worker replaces all chapter rows of the book from its own chapter list
    (the job's `include_code_blocks` applies) and sets `books.chapter_count` and
    `books.duration_seconds`, in the same transaction as the `completed` transition. A
    reconversion overwrites them.
  - A failed or cancelled job writes nothing, so the previous audio keeps its previous durations.
  - Chapter durations come from samples per chunk. The book duration comes from `probe_mp3`, so
    the chapter sum can differ slightly (MP3 padding). Silence after a chunk belongs to the
    chapter that precedes it.
- Consequence: per-chapter audio (S4) can build on stored boundaries. Duplicate chapter titles
  stay separate rows, keyed by `number`.

## D-028 — Migration runner and completion details

- Date: 2026-11-24 · Status: accepted · Refines [D-023](#d-023--versioned-sql-migrations) and
  [D-027](#d-027--chapters-table-and-stored-durations)
- Decision:
  - One `BEGIN IMMEDIATE` covers all pending migrations; any failure rolls back all and leaves
    `user_version` unchanged. Statements run one by one (`executescript` would COMMIT).
  - One backup per run, taken under the lock, only if the database already has tables, named
    `<db>.pre-v<final version>`. A v0.2.0 database gets `.pre-v2`.
  - A database newer than the highest migration file raises `DB_TOO_NEW` (500).
  - Chapter rows are written with the book at upload (`include_code=False`). Old books are
    backfilled lazily on `GET /books/{id}` when they have no rows.
  - `Store.complete_job` finishes a job, replaces chapter rows and sets `chapter_count` and
    `duration_seconds` in one transaction; a cancelled job writes nothing.
  - Router-level `responses` document one error shape; the default 422 schema is replaced.
- Consequence: schema changes are new numbered files with tests. Chapter sum and probed MP3
  length may differ slightly (padding).

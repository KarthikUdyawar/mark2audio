# S3 — Data foundation

Release `v0.3.0` · Branch `feature/s3-data-foundation` · Tasks: [TODO.md](TODO.md)
Plan: [ROADMAP.md](../../ROADMAP.md#sprints) · Workflow: [CLAUDE.md](../../../CLAUDE.md#21-project-mark2audio)

## Goal

Give the data model room to grow: versioned migrations, a `chapters` table, stored audio durations,
and typed API responses. The only visible change is the duration in the UI (FR-08). Chapter export
(S4) and the typed UI (Lab 1) build on this.

## In scope

- S3-R1 Migrations ([D-023](../../DECISION.md)): runner, `PRAGMA user_version`, baseline `001`
  equal to the current schema, pre-migration copy of the database file, refusal to start on a
  database newer than the code, safe when api and worker start together.
- S3-R2 Migration `002`: table `chapters` (`book_id` cascade, `number`, `title`, `start_seconds`,
  `duration_seconds`; primary key `book_id, number`) and column `books.duration_seconds`.
  Supersedes [D-005](../../DECISION.md#d-005--derived-book-status-no-chapter-table) (D-027, T1).
- S3-R3 Chapter rows are written at upload. Books uploaded before S3 are backfilled once from
  `source.md` (idempotent, no change to a book whose rows exist).
- S3-R4 On completion the worker stores each chapter's start and duration, and the book duration
  from `probe_mp3`. A reconversion overwrites them.
- S3-R5 Pydantic response models on all public endpoints ([D-024](../../DECISION.md)), error shape
  in OpenAPI. Existing field names and values do not change.
- S3-R6 API returns `duration_seconds` on books and per-chapter durations in book detail.
- S3-R7 UI shows book duration in the library and chapter durations in the outline. Vanilla JS.
- S3-R8 Upgrade path verified by hand: a real v0.2.0 `data/` directory opened by the new image.
- S3-R9 Docs match reality: ARCHITECTURE (data model, migrations), DESIGN, README, ROADMAP
  (FR-08 Built), `STRUCTURE.md`.

## Out of scope

Chapter MP3s and ZIP (S4) · React/TypeScript and generated clients (Lab 1) · retention and
backup tooling (S7) · PostgreSQL and S3 profiles (lab) · duration for books never converted ·
any change to job states.

## Decisions

- D-022 to D-026 are recorded before the sprint.
- D-027 Chapters table and durations, supersedes D-005 (T1).

## Acceptance

- Each behavior above has a test that fails without it, including: upgrade of a v0.2.0-shaped
  database with data; two processes racing the first migration; a newer database refused.
- The `/openapi.json` schema has no untyped object for any `/api/v1` response.
- `make lint typecheck test` and `make ci` pass; coverage stays at or above the 80% gate.
- Compose run on a copy of a real v0.2.0 `data/`: books, jobs and audio still work, the pre-migration
  copy exists, backfilled chapters show in the UI, a new conversion shows durations.
- Every doc link resolves; no fact in two docs.
- `git tag` shows `v0.3.0` on `main` after the release PR.

## Risks

- Chapter durations come from samples per chunk, grouped by consecutive chapter; duplicate
  chapter titles must not merge. Tested with a fixture that repeats a title.
- Silence between chunks and chapters belongs to the chapter that precedes it; documented.
- A migration bug can damage the only copy of the data; the pre-migration copy is the rollback.
- Free plan: no branch protection ([D-007](../../DECISION.md#d-007--branching-and-releases)).

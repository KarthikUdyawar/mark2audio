# S3 — Tasks

One commit per task. Goal and acceptance: [PRD.md](PRD.md).

- [x] T0 Sprint S3 PRD and TODO, ROADMAP link
- [x] T1 D-027 chapters table and durations (supersedes D-005)
- [x] T2 Migration runner: `user_version`, pre-migration copy, newer-DB refusal, race (test first)
- [x] T3 Baseline `001` equals current schema; v0.2.0-shaped database adopted (test first)
- [x] T4 Migration `002`: `chapters` table, `books.duration_seconds` (test first)
- [x] T5 Store: write chapters at upload, read them, backfill old books (test first)
- [x] T6 Worker: chapter start and duration, book duration on completion (test first)
- [x] T7 Pydantic response models for all endpoints; OpenAPI has no untyped response (test first)
- [x] T8 API: `duration_seconds` on books, chapter durations in detail (test first)
- [ ] T9 UI: durations in library and outline
- [ ] T10 Upgrade a copy of a real v0.2.0 `data/` through Compose; record in ARCHITECTURE
- [ ] T11 ARCHITECTURE, DESIGN, README, ROADMAP (FR-08 Built, S3 Done), `make tree`
- [ ] T12 Review sprint diff (CLAUDE.md section 18), fix findings
- [ ] T13 PR to `develop`, `release/v0.3.0` PR to `main`, tag `v0.3.0`, handoff

Cut line if the sprint runs long: T9 first, then the backfill part of T5.

## Next actions

- [ ] T9 is coded but unticked: tick it in the T10 commit after the UI is seen in a browser
      (library `Title (completed, m:ss)`, outline `Title · m:ss`, null timing shows title only).
- [ ] T10 Copy a real v0.2.0 `data/`, run Compose, check `.pre-v2` backup, old books backfill, new
      conversion shows durations. Record in ARCHITECTURE with date.
- [ ] T11 Docs: ARCHITECTURE (data model, migrations, `complete_job`), DESIGN (durations, gaps),
      README (backup `.pre-v2`), ROADMAP (FR-08 Built, S3 Done), `make tree`.
- [ ] T12 Sprint diff review. T13 PR, release, tag `v0.3.0`.

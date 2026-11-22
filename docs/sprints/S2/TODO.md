# S2 — Tasks

One commit per task. Goal and acceptance: [PRD.md](PRD.md).

- [x] T0 Sprint S2 PRD and TODO, tick S1 T17, ROADMAP sprint row
- [x] T1 D-020 heartbeat file, D-021 dict responses (`7526d92`)
- [x] T2 H1: missing `source.md` gives `SOURCE_MISSING` (test first)
- [x] T3 H2: failed upload leaves no orphan folder (test first)
- [x] T4 H4: catch-all handler returns the `INTERNAL` error shape (test first)
- [x] T5 H7: `create_job` for an unknown book gives `BOOK_NOT_FOUND` (test first)
- [x] T6 H8: `ENOSPC` becomes `DISK_FULL` in upload and worker (test first)
- [x] T7 Heartbeat: `Settings.heartbeat_path`, worker touches it in four places (test first)
- [x] T8 Compose worker health check; verify healthy, busy and unhealthy by hand
- [x] T9 README: health status, orphan-files limitation (H3)
- [x] T10 ARCHITECTURE, ROADMAP (S2 row, candidates), `make tree`
- [x] T11 Review sprint diff (CLAUDE.md section 18), fix findings
- [ ] T12 PR to `develop`, `release/v0.2.0` PR to `main`, tag `v0.2.0`, S1 and S2 handoff

Cut line if the sprint runs long: T6 first, then T3.

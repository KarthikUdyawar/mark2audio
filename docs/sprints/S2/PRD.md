# S2 — Ops and hardening

Release `v0.2.0` · Branch `feature/s2-ops-hardening` · Tasks: [TODO.md](TODO.md)
Plan: [ROADMAP.md](../../ROADMAP.md#sprints) · Workflow: [CLAUDE.md](../../../CLAUDE.md#21-project-mark2audio)

## Goal

Close the "Docker and operations" health-check rule and remove the API failure paths found in the
S2 review of `api.py`, `store.py`, `worker.py`. No new product features, no schema change.

## In scope

- S2-R1 Worker health check: the worker touches `data/worker.heartbeat` after the model loads,
  on every idle poll, after every chunk and before encoding. Compose marks the worker healthy
  while the file is younger than 300 s, with a 120 s start period. Path and threshold are fixed,
  not env-driven. Unhealthy only changes the shown status: compose does not restart on it.
- S2-R2 H1: `GET /books/{id}` with a missing `source.md` returns a stable `SOURCE_MISSING` error,
  not a raw 500.
- S2-R3 H2: a failed upload (database or disk error) leaves no orphan folder under `uploads/`.
- S2-R4 H4: any unhandled exception in the API returns `{"error": {"code": "INTERNAL", ...}}`
  with a generic message; the stack trace stays in the server log.
- S2-R5 H7: `create_job` for a book deleted after the existence check returns `BOOK_NOT_FOUND`
  (404), not a foreign-key error.
- S2-R6 H8: disk full (`ENOSPC`) in upload or in the worker becomes `DISK_FULL` with a safe
  message, not `INTERNAL`.
- S2-R7 H3: documented as a known limitation: if file removal fails after a book delete, orphan
  files stay on disk, invisible to the UI. README only, no code.
- S2-R8 Decisions: D-020 heartbeat file, D-021 API responses stay plain dicts (deviation from
  API rule 2, recorded not rewritten).
- S2-R9 Docs match reality: ARCHITECTURE, README, ROADMAP, `STRUCTURE.md`.

## Checked, no change

- H5: `KokoroTts.voices()` caches once the model files exist, so `/health` does not reload the
  voices file.
- H3 as code: the delete order (database row first, files second) is already the safe one.

## Out of scope

Chapter MP3/ZIP export (FR-10, needs a schema decision against D-005) · retention (technical rule
File and path safety 10) · duration display · the 26 non-English voices · `phonemizer` warning
trace · model release v1.1 · image alt text · configurable heading level · huge-document and
malformed-Markdown review · Pydantic response models. Candidates for S3:
[ROADMAP.md](../../ROADMAP.md#unscheduled-candidates).

## Decisions

- D-020 Worker health check by heartbeat file (T1).
- D-021 API responses stay plain dicts (T1).

## Acceptance

- Each fixed failure path (H1, H2, H4, H7, H8) has a regression test that fails without the fix.
- The worker heartbeat is touched in the four places above, covered by a unit test.
- `docker compose ps` shows the worker `healthy` while idle and during a conversion, and
  `unhealthy` after the heartbeat file is aged past 300 s. The run is recorded in ARCHITECTURE.
- Coverage stays at or above the 80% gate.
- `make lint typecheck test` and `make ci` pass; every doc link resolves; no fact in two docs.
- `git tag` shows `v0.2.0` on `main` after the release PR.

## Risks

- A single FFmpeg encode can run up to 1800 s, longer than the 300 s threshold, so a very long
  encode can show the worker `unhealthy`. Harmless (no restart); noted in ARCHITECTURE.
- The compose health check cannot be unit-tested; it is verified by hand.
- Free plan: no branch protection ([D-007](../../DECISION.md#d-007--branching-and-releases)).

# S1 — Verify the baseline

Release `v0.1.0` · Branch `feature/s1-verify-baseline` · Tasks: [TODO.md](TODO.md)
Plan: [ROADMAP.md](../../ROADMAP.md#sprints) · Workflow: [CLAUDE.md](../../../CLAUDE.md#21-project-mark2audio)

## Goal

Prove the MVP baseline works for real: real Kokoro model, real FFmpeg, Docker Compose, and no
outbound network during conversion. No new product features. Findings that contradict the docs
fix the docs or the code.

## In scope

- S1-R1 Close S0: accept D-016 (sprints merge by pull request with a merge commit; back-merge only
  when `main` has content `develop` lacks). Fix CLAUDE.md step 6, tick S0 T21, update the ROADMAP
  sprint table.
- S1-R2 Smoke test: it must run when model files exist. Resolve the default model directory from
  the repo root, require both model files, and cover synthesis, `encode_mp3` and `probe_mp3`.
  Add `make smoke`.
- S1-R3 Adapter audit: check `KokoroTts` against the locked `kokoro-onnx` version and the real
  model: voice list and language prefixes, sample rate, language handling, no runtime downloads.
  Every defect gets a failing stub-Kokoro unit test first.
- S1-R4 Chunk size: measure whether `M2A_CHUNK_MAX_CHARS` (400) is safe for the real model's input
  limit; change the default or the chunker if not.
- S1-R5 Model provenance: pinned source URLs and sha256 in the Makefile, verified on download.
  Source, revision and license recorded in D-017, which supersedes the "unverified" part of D-002.
- S1-R6 Docker: build and run Compose, convert a book through the stack, then convert with the
  worker's network disabled (`docker-compose.offline.yml`). Check bind-mount permissions.
  Decide whether the image should honor `uv.lock` (D-018, only if the Docker run shows it matters).
- S1-R7 Cheap hardening: test for `app/main.py`, cover meaningful uncovered worker paths, pin
  GitHub Actions by commit SHA.
- S1-R8 Docs match reality: "unverified" wording removed or replaced by what was verified;
  measured real-time factor and peak memory recorded once, in ARCHITECTURE.

## Out of scope

Chapter MP3/ZIP export (FR-10, schema change, S2) · worker health check · upload and Markdown
robustness review (malformed, huge, disk-full) · duration display · image alt text · configurable
heading level · more languages and voices · UI rewrite. Candidates for S2:
[ROADMAP.md](../../ROADMAP.md#unscheduled-candidates).

## Decisions

- D-016 Sprint merge flow (T1).
- D-017 Model provenance, supersedes the "unverified" status in D-002 (T6).
- D-018 Dockerfile honors `uv.lock`: only if T9 shows image dependencies drift or break. Skipped
  otherwise, noted in the T10 commit message.

## Acceptance

- `make smoke` runs (not skipped) with model files present and passes.
- Each adapter defect found has a regression test that fails without the fix.
- `make model` fails on a checksum mismatch; hashes live only in the Makefile.
- `make up` builds, the UI converts a book, and the MP3 plays.
- The offline run converts a book with the worker on `network_mode: none`, and an outbound
  connection attempt from inside that container fails.
- Real-time factor and peak memory are recorded in ARCHITECTURE.
- Coverage stays at or above the 80% gate; `app/main.py` is covered.
- No docs still call the adapter, image or offline operation "unverified" or "never run" unless
  that is still true.
- `make lint typecheck test` and `make ci` pass; every doc link resolves; no fact in two docs.
- `git tag` shows `v0.1.0` on `main` after the release PR.

## Risks

- The smoke test and Docker verification cannot run in CI (no model files); they stay local.
- The 325 MB model and Docker build need disk and RAM; the dev box had about 1 GiB free during
  planning. Measure with other work closed.
- Pinned hashes are only as good as their source. Confirm them against the upstream release page
  before pinning.
- Free plan: no branch protection ([D-007](../../DECISION.md#d-007--branching-and-releases)).

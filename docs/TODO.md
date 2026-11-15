# Mark2Audio — Implementation TODO

**Planning style:** Small, reviewable increments  
**Priority:** P0 = MVP blocker, P1 = next iteration, P2 = later

## Milestone 0 — Repository and developer experience

- [ ] Create repository with `backend/`, `frontend/`, `docs/`, and `data/` layout.
- [ ] Add `README.md` with project purpose and local-first guarantee.
- [ ] Add `.gitignore` for virtual environments, node modules, SQLite files, uploads, audio, temp files, and model weights.
- [ ] Add `.env.example` with storage roots, upload limit, model path, worker polling interval, and default audio settings.
- [ ] Add Makefile targets: `install`, `dev`, `test`, `lint`, `typecheck`, `format`, `up`, `down`, `logs`.
- [ ] Configure Ruff, strict mypy, pytest, coverage, and Bandit.
- [ ] Add pre-commit hooks.
- [ ] Add CI for backend tests, lint, typecheck, and frontend checks.
- [ ] Record model artifact source, revision, license, and checksum before committing to a model choice.

**Acceptance:** A fresh clone can install development dependencies and run empty backend/frontend checks.

## Milestone 1 — Backend foundation

- [ ] Create FastAPI application and `/health` endpoint.
- [ ] Add settings management and environment validation.
- [ ] Configure SQLAlchemy 2.0 and SQLite.
- [ ] Enable SQLite foreign keys.
- [ ] Add Alembic migrations.
- [ ] Create Book, Chapter, and ConversionJob models.
- [ ] Add repository layer and session dependency.
- [ ] Add consistent API error schema.
- [ ] Add structured logging with request and resource IDs.
- [ ] Add tests for database setup and health endpoint.

**Acceptance:** API starts locally, database tables migrate, and health check passes.

## Milestone 2 — Markdown upload and parsing (P0)

- [ ] Implement upload size and extension validation.
- [ ] Decode UTF-8 safely and reject empty documents.
- [ ] Generate server-side book UUID and safe storage path.
- [ ] Store uploaded source under `data/uploads/{book_id}/`.
- [ ] Implement Markdown AST/block parsing.
- [ ] Support headings, paragraphs, lists, blockquotes, links, code, and image alt text.
- [ ] Implement narration policies for links, images, and code.
- [ ] Detect chapters from configurable heading level.
- [ ] Handle preamble and documents without headings.
- [ ] Add parser fixtures and edge-case tests.
- [ ] Implement list/detail/delete book endpoints.

**Acceptance:** User uploads a Markdown file and receives a book record with a stable chapter outline.

## Milestone 3 — Text normalization and chunking (P0)

- [ ] Implement conservative whitespace normalization.
- [ ] Preserve paragraph and list boundaries.
- [ ] Implement configurable chunk size.
- [ ] Prefer paragraph and sentence boundaries.
- [ ] Ensure deterministic chunk order.
- [ ] Map chunks to chapter IDs and progress positions.
- [ ] Add tests for long paragraphs, punctuation, Unicode, and empty sections.

**Acceptance:** A book is transformed into ordered, bounded narration chunks without losing meaningful content.

## Milestone 4 — Local TTS integration (P0)

- [ ] Verify Kokoro ONNX model artifact, revision, license, and voice asset requirements.
- [ ] Select and pin a compatible ONNX Runtime version.
- [ ] Implement a TTS engine protocol.
- [ ] Implement Kokoro ONNX adapter.
- [ ] Load model once per worker process.
- [ ] Implement voice catalogue endpoint.
- [ ] Validate language, voice, and speech speed.
- [ ] Add fake TTS engine for deterministic tests.
- [ ] Add optional real-model smoke test.
- [ ] Benchmark CPU memory, speed, and output quality on target workstation.
- [ ] Evaluate CUDA execution provider separately; keep CPU as baseline.

**Acceptance:** A sample chunk produces valid local audio with a selected installed voice and no network request.

## Milestone 5 — Audio encoding and output validation (P0)

- [ ] Check FFmpeg and ffprobe availability at startup.
- [ ] Generate per-chunk WAV/PCM in job temp directory.
- [ ] Normalize sample rate, channels, and sample format.
- [ ] Add configurable silence between chunks/paragraphs.
- [ ] Concatenate chapter chunks in correct order.
- [ ] Encode MP3 at 128/192/256 kbps.
- [ ] Add safe title metadata.
- [ ] Validate output duration, codec, and non-zero size with ffprobe.
- [ ] Publish final MP3 using atomic rename.
- [ ] Add tests for FFmpeg argument construction and validation failures.

**Acceptance:** A completed conversion produces an MP3 that passes ffprobe and plays in a browser.

## Milestone 6 — Worker and job lifecycle (P0)

- [ ] Implement SQLite-backed job creation.
- [ ] Implement atomic queued-job claiming.
- [ ] Implement single-job worker loop.
- [ ] Add explicit state transition validation.
- [ ] Persist chunk-level progress and current chapter.
- [ ] Handle worker restart and stale processing jobs.
- [ ] Handle exceptions and safe error messages.
- [ ] Clean temporary files on success and failure.
- [ ] Implement cancellation checks between chunks (P1 if MVP schedule is tight).
- [ ] Add worker tests using fake TTS.
- [ ] Add job status and conversion endpoints.

**Acceptance:** API can enqueue a conversion, worker processes it, and UI/API can observe accurate terminal status.

## Milestone 7 — Frontend MVP (P0)

- [ ] Scaffold React + TypeScript + Vite.
- [ ] Enable TypeScript strict mode.
- [ ] Add Tailwind CSS and accessible base components.
- [ ] Implement library/dashboard page.
- [ ] Implement Markdown drag-and-drop and file picker.
- [ ] Show upload progress and validation errors.
- [ ] Implement book detail and chapter outline.
- [ ] Implement voice, speed, bitrate, and code-block options.
- [ ] Implement conversion action and job polling.
- [ ] Implement progress display and error state.
- [ ] Implement HTML audio player.
- [ ] Implement MP3 download.
- [ ] Add responsive layout and keyboard-accessible controls.

**Acceptance:** User can complete the primary workflow entirely through the browser UI.

## Milestone 8 — Docker and offline validation (P0)

- [ ] Create backend/API Dockerfile.
- [ ] Create worker Dockerfile or shared backend image with separate command.
- [ ] Create frontend Dockerfile.
- [ ] Add Docker Compose with frontend, API, and worker.
- [ ] Persist data and model directories.
- [ ] Run containers as non-root where feasible.
- [ ] Bind host ports to localhost.
- [ ] Add health checks and startup dependency handling.
- [ ] Document model acquisition as a one-time setup operation.
- [ ] Test conversion with outbound network disabled.
- [ ] Document backup and restore of `data/`.

**Acceptance:** `docker compose up` starts the application and a conversion succeeds offline after model setup.

## Milestone 9 — Hardening and release

- [ ] Run full tests and reach at least 80% application coverage.
- [ ] Run Ruff, strict mypy, and Bandit.
- [ ] Review upload/path traversal and deletion safety.
- [ ] Verify no remote Markdown resources are fetched.
- [ ] Verify logs do not contain source text.
- [ ] Test malformed Markdown and very long documents.
- [ ] Test disk-full and FFmpeg failure behavior.
- [ ] Test API and worker restart during conversion.
- [ ] Add troubleshooting guide and known limitations.
- [ ] Add screenshots/GIF only after UI stabilizes.
- [ ] Tag `v0.1.0`.

**Acceptance:** MVP definition of done in `PRD.md` is satisfied.

## Post-MVP backlog

### P1

- [ ] Export chapter MP3 files.
- [ ] Export chapter ZIP with manifest.
- [ ] Add cancellation UI and safe cancellation.
- [ ] Add conversion history and retry-as-new-job.
- [ ] Add storage usage display and cleanup controls.
- [ ] Add additional verified language/voice packs.

### P2

- [ ] Add configurable pronunciation dictionary.
- [ ] Add audiobook metadata editor.
- [ ] Add chapter-level playback navigation.
- [ ] Add optional cover art from user-provided local image.
- [ ] Add resume/recovery from last successful chunk.
- [ ] Evaluate additional local TTS engines behind the same interface.

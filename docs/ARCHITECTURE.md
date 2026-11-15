# Mark2Audio — Technical Rules

These rules are mandatory for implementation and code review unless a decision record explicitly changes them.

## 1. Architecture and scope

1. Build a modular monolith; do not split the MVP into microservices.
2. Runtime services are limited to frontend, API, and worker.
3. Use SQLite for metadata and job state.
4. Do not add Redis, RabbitMQ, PostgreSQL, MinIO, or cloud APIs to the MVP.
5. All TTS inference and audio processing must run locally.
6. Runtime conversion must not require outbound network access.
7. Keep model files and user data outside immutable container images.

## 2. Python and dependency management

1. Use Python 3.12 or newer, pinned to a tested version in CI and Docker.
2. Use `uv` for dependency and environment management.
3. Declare runtime and development dependencies explicitly in `pyproject.toml`.
4. Pin or constrain dependencies; commit the lockfile.
5. Use type annotations for public functions, methods, and module-level interfaces.
6. Avoid `Any`; if unavoidable at an external boundary, isolate it and validate immediately.
7. Use `pathlib.Path` for filesystem paths.
8. Use timezone-aware UTC timestamps.
9. Do not perform blocking TTS or FFmpeg work inside FastAPI request handlers.

## 3. Code quality

Required checks:

- `ruff check`
- `ruff format --check`
- `mypy` in strict mode where practical
- `pytest`
- `pytest --cov` with at least 80% coverage for application code
- `bandit` or equivalent static security scan

Guidelines:

1. Keep functions focused and small.
2. Prefer dependency injection for database sessions, settings, and TTS engine.
3. Use domain-specific exceptions; translate them into stable API errors.
4. Do not silently swallow exceptions.
5. Do not log document contents, generated speech text, or sensitive filesystem details.
6. Add docstrings to public modules/classes/functions where they clarify contracts.
7. Avoid broad `# type: ignore`; explain and narrow any suppression.

## 4. API rules

1. Version all endpoints under `/api/v1`.
2. Validate request and response data with Pydantic schemas.
3. Set explicit upload-size limits.
4. Accept only allowed Markdown extensions and supported text encoding.
5. Use UUIDs for public resource identifiers.
6. Never accept a client-provided filesystem path.
7. Never return absolute server paths.
8. Return consistent error structures with stable error codes.
9. Use correct content types for MP3 and ZIP responses.
10. Keep long-running work in the worker, not the API process.

## 5. File and path safety

1. Generate storage names server-side.
2. Treat original filenames as display metadata only.
3. Resolve all paths under configured storage roots and verify path containment.
4. Prevent path traversal and symlink escape when reading or deleting files.
5. Write generated output to a temporary path, validate it, then atomically rename.
6. Delete only files owned by the requested book/job.
7. Do not execute uploaded content.
8. Do not fetch remote URLs found in Markdown.
9. Clean temporary directories on success, failure, cancellation, and stale-job recovery.
10. Apply configurable retention for uploaded source and generated output.

## 6. Markdown processing rules

1. Parse Markdown as data; never render or execute raw HTML in a privileged context.
2. Preserve source reading order.
3. Preserve paragraph and list boundaries.
4. Speak headings as meaningful section titles.
5. Skip fenced and inline code by default.
6. Convert links to link text by default; raw URL narration is opt-in.
7. Do not download remote images.
8. Use image alt text only when configured.
9. Handle empty documents and empty chapters explicitly.
10. Maintain fixtures for supported Markdown constructs and malformed input.

## 7. TTS and audio rules

1. Define a TTS engine protocol/interface independent of Kokoro.
2. Load the model once per worker process, not once per chunk.
3. Validate voice ID, language, and speed before starting a job.
4. Bound chunk length and worker concurrency.
5. Prefer paragraph/sentence boundaries when chunking.
6. Keep chunk ordering deterministic.
7. Normalize sample rate, channels, and sample format before concatenation.
8. Invoke FFmpeg with an argument list; never interpolate user input into a shell command.
9. Set subprocess timeouts and capture bounded diagnostic output.
10. Validate final MP3 using `ffprobe` before marking a job completed.
11. Never mark a job completed before final output is safely published.
12. Keep temporary WAV files out of the final library unless explicitly requested.

## 8. Worker and job rules

1. Job state transitions must be explicit and validated.
2. Claim queued jobs atomically.
3. Default to one active job.
4. Persist progress after completed chunks or meaningful milestones.
5. Progress must not move backwards.
6. Reserve 100% for validated final output.
7. Store safe error codes/messages in the database; keep stack traces in logs.
8. A worker restart must not leave jobs permanently stuck in `processing`.
9. Retrying creates a new job for MVP; do not mutate terminal jobs back to queued.
10. Cancellation must be checked between chunks and clean temporary data.

## 9. Frontend rules

1. Use TypeScript strict mode.
2. Keep API calls in a service/client layer.
3. Model API responses with explicit types.
4. Show upload and conversion states separately.
5. Poll only while a job is active and stop at terminal state.
6. Disable duplicate conversion actions for an active job.
7. Display actionable validation and failure messages.
8. Use semantic HTML and accessible labels.
9. Do not expose internal paths or stack traces.
10. Do not treat browser-side state as authoritative for job completion.

## 10. Docker and operations

1. Use non-root container users where feasible.
2. Pin base image versions; avoid floating production tags.
3. Add health checks for API and worker readiness.
4. Persist `data/` and `models/` across container recreation.
5. Bind local application ports to `127.0.0.1` by default.
6. Do not expose the service to a LAN unless the user explicitly configures it.
7. Do not mount the Docker socket into application containers.
8. Keep secrets out of images and source control.
9. Document CPU and memory requirements.
10. Provide a model download/setup step separate from normal offline startup.

## 11. Git workflow

1. Use GitFlow-style branches: `feature/*` → `develop` → `main`.
2. Protect `main` and `develop`; do not push feature work directly to either.
3. Use pull requests for feature integration.
4. Keep commits focused and conventional (e.g. `feat:`, `fix:`, `test:`, `docs:`).
5. Do not use `git add -A` blindly; inspect `git status` and stage intentional paths.
6. Require quality checks and review before merge.
7. Keep generated model files, audio, databases, and user uploads out of Git.

## 12. Testing rules

Required test categories:

- Markdown parser fixtures.
- Text normalization and chunk-boundary tests.
- Voice/settings validation.
- Job state transition and atomic-claim tests.
- File path traversal and upload validation tests.
- FFmpeg command construction tests.
- Audio output validation tests.
- API integration tests using temporary SQLite and storage directories.
- Worker tests with a fake TTS engine; do not require real model inference in the normal unit-test suite.
- One optional local smoke test using the actual model and FFmpeg.

Tests must not depend on network access. Use deterministic fixtures and fake TTS output for normal CI.

## 13. Definition of done

A change is done only when:

- Acceptance criteria are met.
- Tests cover normal, invalid, and failure paths.
- Ruff, mypy, pytest, and security checks pass.
- No secrets, user data, model weights, or generated audio are committed.
- API and user-facing behavior are documented.
- Relevant docs and `.env.example` are updated.

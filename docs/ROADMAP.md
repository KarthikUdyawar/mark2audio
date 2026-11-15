# Mark2Audio — Product Requirements Document

**Status:** MVP specification  
**Project type:** Local-first, offline-capable Markdown-to-audiobook application  
**Version:** 1.0

## 1. Product summary

Mark2Audio converts user-uploaded Markdown (`.md`) documents into downloadable MP3 audiobooks using a locally hosted text-to-speech (TTS) engine. Documents, models, intermediate audio, and final output remain on the user's machine.

The MVP is a single-user local application. It does not require accounts, cloud storage, paid APIs, or a distributed microservice architecture.

## 2. Goals

- Convert a Markdown file into a playable and downloadable MP3.
- Run TTS locally with an open model/runtime.
- Work without internet access after dependencies and model files have been downloaded.
- Preserve document reading order and useful chapter boundaries.
- Provide clear conversion status and actionable error messages.
- Keep the application practical to run with Docker Compose on a developer workstation.

## 3. Non-goals for MVP

- Cloud hosting, multi-user accounts, authentication, or synchronization.
- EPUB, PDF, DOCX, HTML, or web-page ingestion.
- Speech cloning or user-uploaded voice models.
- Collaborative editing.
- Mobile applications.
- Advanced audiobook mastering, background music, or sound effects.
- Distributed queues, Kubernetes, Redis, RabbitMQ, or PostgreSQL.
- Guaranteed support for every Markdown extension.

## 4. Target user and primary workflow

**Target user:** A person who has Markdown notes, technical documents, tutorials, or book manuscripts and wants to listen to them locally.

**Primary workflow:**

1. Open the local web application.
2. Select or drag in one `.md` file.
3. Review the detected title and chapter outline.
4. Choose a locally installed voice and speech speed.
5. Start conversion.
6. Monitor progress and any warnings.
7. Preview the generated audio.
8. Download the complete MP3 and, optionally, chapter MP3s.

## 5. Functional requirements

### FR-01 — Markdown upload (P0)

- Accept `.md` and `.markdown` files.
- Enforce a configurable upload-size limit (default: 10 MiB).
- Validate extension, size, and UTF-8 text decoding.
- Generate a server-side UUID; never trust the supplied filename as a storage path.
- Show a useful validation error for unsupported, empty, or unreadable files.

**Acceptance criteria**

- A valid Markdown file is stored and appears in the library.
- An oversized, empty, invalid-encoding, or unsupported file is rejected.
- A filename containing path traversal characters cannot escape the upload directory.

### FR-02 — Markdown parsing and normalization (P0)

- Parse headings, paragraphs, ordered/unordered lists, blockquotes, and emphasis.
- Preserve reading order.
- Convert links to readable link text by default; do not speak raw URLs unless configured.
- Remove Markdown syntax while preserving meaningful text.
- Exclude fenced and inline code by default; expose an option to include code.
- Treat images as optional alt-text narration; do not fetch remote images.
- Normalize whitespace and avoid joining adjacent paragraphs unintentionally.

**Acceptance criteria**

- A fixture containing headings, lists, links, blockquotes, and code produces clean readable text.
- No network request is made while parsing a document.
- Empty or effectively textless documents are rejected with a clear message.

### FR-03 — Chapter detection (P0)

- Detect chapters from Markdown headings.
- Use `#` as top-level chapter boundaries; support a configurable heading level.
- Content before the first heading becomes an introductory section when non-empty.
- Documents without headings are treated as one chapter.
- Preserve heading text as chapter titles.

**Acceptance criteria**

- Chapter order matches source order.
- A document with no headings still converts as one audio track.
- Heading-only sections are handled without creating empty audio files.

### FR-04 — Voice catalogue (P0)

- List voices available in the installed local TTS model.
- Expose voice ID, display name, language, and availability.
- Never imply a voice is installed if its model assets are missing.
- Provide a default voice from the configured model.

**Acceptance criteria**

- The UI only offers voices that the backend confirms are available.
- A missing voice produces a clear validation error rather than a failed conversion halfway through.

### FR-05 — Local text-to-speech (P0)

- Use a local TTS engine (initial implementation: Kokoro ONNX).
- Support configurable speech speed with safe bounds (initial range: 0.8–1.2).
- Split text into bounded chunks while preserving paragraph order.
- Keep chunk sizes configurable and respect model/runtime limits.
- Generate intermediate audio in a per-job temporary directory.
- Run one conversion job at a time by default to control memory use.

**Acceptance criteria**

- A short sample document produces non-empty audio.
- Long documents are chunked rather than submitted as one unbounded request.
- The worker reports progress as chunks complete.
- A failed chunk marks the job failed and preserves a useful error record.

### FR-06 — MP3 output (P0)

- Use FFmpeg to encode WAV/PCM output into MP3.
- Default bitrate: 192 kbps; allow 128, 192, and 256 kbps.
- Produce a complete audiobook MP3.
- Add basic title metadata where supported.
- Do not delete intermediate files until final output validation succeeds.

**Acceptance criteria**

- The output exists, is non-empty, and can be probed by FFmpeg/ffprobe.
- The final duration is positive.
- The browser can play the MP3 and the user can download it.

### FR-07 — Job lifecycle and progress (P0)

- Job states: `queued`, `processing`, `completed`, `failed`, `cancelled`.
- Track total chunks, completed chunks, current chapter, progress percentage, timestamps, and error details.
- Expose job status through a polling endpoint.
- Progress must be monotonic from 0 to 100 for a successful job.
- Do not report `completed` until output validation and database updates finish.

**Acceptance criteria**

- UI progress updates while a conversion is running.
- A successful job ends at 100%.
- A failed job exposes a safe, human-readable error.
- Restart behavior is documented; MVP may mark interrupted jobs as failed on startup.

### FR-08 — Audiobook library (P0)

- List imported books and their conversion status.
- Show title, original filename, creation time, duration when available, and output status.
- Allow a user to open a book detail page.
- Allow deletion of a book and its associated files after confirmation.

**Acceptance criteria**

- Deleting a book removes only files belonging to that book.
- The library remains consistent after application restart.

### FR-09 — Audio playback and download (P0)

- Provide browser audio playback for completed audiobooks.
- Provide a direct download endpoint for the final MP3.
- Return appropriate content type and safe download filename.
- Do not expose arbitrary filesystem paths.

**Acceptance criteria**

- Completed audio can be streamed and downloaded.
- Incomplete or missing output returns a clear not-ready/not-found response.

### FR-10 — Chapter exports (P1)

- Optionally produce one MP3 per chapter.
- Produce a ZIP containing chapter MP3s and a simple manifest.
- Keep chapter order explicit in filenames and manifest.

### FR-11 — Conversion cancellation (P1)

- Allow cancellation of queued or processing jobs.
- Stop work at a safe chunk boundary.
- Clean temporary files without deleting completed library content.

## 6. Non-functional requirements

- **Local-first:** No document or audio data is sent to third-party services.
- **Offline operation:** Runtime conversion must not need internet access once models and dependencies are present.
- **Privacy:** Bind the web service to localhost by default.
- **Resource use:** Single worker and bounded chunks by default; configurable limits.
- **Reliability:** Use atomic file moves for final output and persist job state.
- **Maintainability:** Modular monolith with clear service boundaries and typed interfaces.
- **Accessibility:** Keyboard-operable controls, labels, visible status, and adequate contrast.
- **Observability:** Structured logs with job/book IDs; never log full document contents.
- **Portability:** Docker Compose and a documented native development path.

## 7. MVP user interface

1. **Library page:** upload dropzone, recent books, status cards.
2. **Book detail page:** title, chapter outline, conversion controls, job progress, player, download.
3. **Voice settings:** available voices, language, speech speed, bitrate.
4. **Settings page:** storage usage, upload limit, model status, worker status.

## 8. Success metrics

- A valid Markdown file can be uploaded and converted end-to-end.
- A short sample document converts without manual intervention.
- A longer document is chunked and reports progress.
- Generated MP3 passes an FFmpeg probe and plays in a browser.
- Conversion works with outbound network access disabled after setup.
- Tests cover parsing, chunking, job transitions, file safety, and audio command construction.

## 9. Risks and mitigations

| Risk                             | Mitigation                                                |
| -------------------------------- | --------------------------------------------------------- |
| TTS model/runtime compatibility  | Pin model revision and runtime versions; add a smoke test |
| Large documents exhaust memory   | Chunk text, single worker, bounded concurrency            |
| Audio chunks sound discontinuous | Add configurable silence and test concatenation           |
| Markdown edge cases              | Define supported syntax and maintain parser fixtures      |
| FFmpeg missing or incompatible   | Startup health check and explicit setup instructions      |
| Model licensing uncertainty      | Verify model and voice licenses before redistribution     |
| Interrupted conversion           | Persist state and mark stale jobs failed on startup       |

## 10. MVP definition of done

- All P0 requirements implemented.
- Unit and integration tests pass.
- Ruff, strict mypy, and security checks pass.
- At least 80% test coverage for application code.
- Docker Compose starts frontend, API, and worker.
- Model files are mounted/persisted separately from the application image.
- README documents setup, model acquisition, offline use, troubleshooting, and data locations.

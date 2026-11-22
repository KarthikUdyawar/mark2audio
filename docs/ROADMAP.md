# Mark2Audio — Roadmap

Local-first, offline-capable Markdown-to-audiobook app: upload `.md`, get a downloadable MP3 made
by a local TTS engine. Single user. No accounts, cloud storage, paid APIs or microservices.

Related: [ARCHITECTURE.md](ARCHITECTURE.md) (backend, rules) · [DESIGN.md](DESIGN.md) (UI) ·
[DECISION.md](DECISION.md) · [CLAUDE.md](../CLAUDE.md#21-project-mark2audio) (workflow) ·
sprint docs in `sprints/`.

## Goals

- Convert a Markdown file into a playable, downloadable MP3.
- Run TTS locally with an open model; work offline once dependencies and models are present.
- Preserve reading order and chapter boundaries.
- Clear status and actionable errors.
- Practical on a developer workstation with Docker Compose.

## Non-goals

Cloud hosting, accounts, sync · EPUB/PDF/DOCX/HTML ingestion · voice cloning · collaborative
editing · mobile apps · audiobook mastering or sound effects · Kubernetes or external queues ·
support for every Markdown extension.

## Target user and workflow

Someone with Markdown notes, docs or manuscripts who wants to listen locally. Open the app → upload
`.md` → review title and chapters → pick voice and speed → convert → watch progress → play →
download.

## Requirements status

Baseline MVP requirements (full acceptance criteria: `git show cd46e5b:docs/PRD.md`). Status as
of 2026-11-22. How each is built: [ARCHITECTURE.md](ARCHITECTURE.md).

| ID    | Requirement                                                     | Pri | Status                                |
| ----- | --------------------------------------------------------------- | --- | ------------------------------------- |
| FR-01 | Markdown upload, size/extension/UTF-8 validation, UUID storage  | P0  | Built                                 |
| FR-02 | Parsing and normalization (links as text, code skipped, images) | P0  | Partial: no image alt-text option     |
| FR-03 | Chapter detection from headings, intro, no-heading docs         | P0  | Built, heading level not configurable |
| FR-04 | Voice catalogue from the installed model                        | P0  | Built, verified with real model       |
| FR-05 | Local TTS, chunking, speed 0.8–1.2, progress                    | P0  | Built, verified with real model       |
| FR-06 | FFmpeg MP3 at 128/192/256 kbps, title metadata, probe           | P0  | Built                                 |
| FR-07 | Job lifecycle, monotonic progress, safe errors                  | P0  | Built                                 |
| FR-08 | Library, detail, delete                                         | P0  | Partial: no duration shown            |
| FR-09 | Playback and download                                           | P0  | Built                                 |
| FR-10 | Chapter MP3s and ZIP with manifest                              | P1  | Not built                             |
| FR-11 | Cancellation                                                    | P1  | Built (API, worker, UI)               |

## Sprints

One `feature/sN-<slug>` branch per sprint, one commit per task, release tagged `v0.N.0`.
Per-sprint `PRD.md` and `TODO.md` live in `sprints/SN/`.

| Sprint                  | Theme                                            | Release  | Status      |
| ----------------------- | ------------------------------------------------ | -------- | ----------- |
| [S0](sprints/S0/PRD.md) | Setup: docs, workflow, CI, pre-commit, lockfile  | `v0.0.0` | Done        |
| [S1](sprints/S1/PRD.md) | Verify the baseline: real model, Docker, offline | `v0.1.0` | Done        |
| [S2](sprints/S2/PRD.md) | Ops hardening: worker health check, API errors   | `v0.2.0` | In progress |

## Unscheduled candidates

Input for S2 planning, in rough priority order. S1 verified the baseline (real model, Docker,
offline), covered `app/main.py` and the worker, and pinned Actions by SHA.

### **Hardening**

- Review upload, path traversal and deletion safety; verify no remote Markdown resources are
  fetched; verify logs contain no source text.
- Malformed Markdown, very long documents, disk-full, FFmpeg failure, restart during conversion.
- Troubleshooting guide and known limitations.
- Worker health check (technical rule: Docker and operations, item 3; none exists yet).
- Trace the `phonemizer words count mismatch` warnings in the worker log.
- Evaluate model release `model-files-v1.1` (different `kokoro-v1.0.onnx`, untested, see D-017).
- Enable the 26 hidden non-English voices after verifying their espeak language codes.

### **P1**

- Chapter MP3 export and ZIP with manifest (FR-10).
- Settings page, duration display, worker heartbeat, storage usage and cleanup.
- Conversion history, retry as new job.
- More verified languages and voice packs.

### **P2**

- Pronunciation dictionary, metadata editor, chapter navigation, optional cover art.
- Resume from last successful chunk.
- Other local TTS engines behind the same interface.
- React/TypeScript UI (needs a decision, see [DECISION.md](DECISION.md)).

## Risks

| Risk                              | Mitigation                               |
| --------------------------------- | ---------------------------------------- |
| TTS model/runtime incompatibility | Pin versions, smoke test, verify adapter |
| Large documents exhaust memory    | Bounded chunks, single worker            |
| Chunks sound discontinuous        | Configurable silence (`M2A_SILENCE_MS`)  |
| Markdown edge cases               | Parser fixtures                          |
| FFmpeg missing                    | Health check, setup docs                 |
| Model/voice licensing unknown     | Verify before any distribution           |
| Interrupted conversion            | Stale jobs marked failed on worker start |

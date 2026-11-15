# Mark2Audio

Markdown in, MP3 out. Local TTS (Kokoro ONNX) + FFmpeg. Nothing leaves your machine.
Specs: [`docs/`](docs/).

## Run

```bash
make model          # once, needs internet: downloads Kokoro model + voices into models/kokoro/
make up             # docker compose: api (+UI) and worker, bound to 127.0.0.1:8000
```

Open <http://127.0.0.1:8000>, drop a `.md`, pick voice/speed, Convert, play or download.
After `make model`, conversion needs no network.

Native dev: `make install`, then `make api` and `make worker` in two terminals.
No model yet? `M2A_FAKE_TTS=1` makes sine-tone audio to try the pipeline.

## Data

`data/uploads/{id}/source.md`, `data/audio/{id}/audiobook.mp3`, `data/temp/{job}` (removed after each job),
`data/mark2audio.db`. Back up by copying `data/`. Models live in `models/kokoro/` (mounted, not in the image).

## Checks

`make test lint typecheck` (pytest with 80% coverage gate, ruff, strict mypy, bandit).
A real-model smoke test runs automatically when model files exist.

## Behaviour notes

- Code blocks skipped by default; links read as link text; images ignored; chapters split on `#`.
- One job at a time. Worker restart marks interrupted jobs `failed` (`WORKER_RESTARTED`); retry = new job.
- Errors: `{"error": {"code", "message"}}`. API under `/api/v1`.

## Troubleshooting

- *No voices in UI / `MODEL_UNAVAILABLE`*: run `make model`, check `models/kokoro/` has both files.
- *Health `degraded`*: ffmpeg/ffprobe missing from PATH.
- *Permission denied on `data/`*: container runs as uid 1000; `chown -R 1000 data`.

## Known gaps vs docs/ (deliberate, MVP-lazy)

Plain-JS UI served by the API instead of a React/Vite/Tailwind container · stdlib `sqlite3` instead of
SQLAlchemy/Alembic · no chapter MP3/ZIP export (P1) · no settings page, duration display, image alt-text
option, worker heartbeat · Kokoro adapter and Docker build not run in this build · model license/checksum
not yet recorded · CI, pre-commit and git branching not set up.

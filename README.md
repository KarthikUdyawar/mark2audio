# Mark2Audio

Markdown in, MP3 out. Local TTS (Kokoro ONNX) + FFmpeg. Nothing leaves your machine.
Docs: [ROADMAP](docs/ROADMAP.md) · [ARCHITECTURE](docs/ARCHITECTURE.md) · [DESIGN](docs/DESIGN.md) · [DECISION](docs/DECISION.md) · [CLAUDE.md](CLAUDE.md).

## Run

```bash
make model          # once, needs internet: downloads Kokoro model + voices into models/kokoro/, verifies sha256
make up             # docker compose: api (+UI) and worker, bound to 127.0.0.1:8000
```

Open <http://127.0.0.1:8000>, drop a `.md`, pick voice/speed, Convert, play or download.
After `make model`, conversion needs no network ([proof](docs/ARCHITECTURE.md#runtime)).

Native dev: `make install hooks`, then `make api` and `make worker` in two terminals.
No model yet? `M2A_FAKE_TTS=1` makes sine-tone audio to try the pipeline.

## Data

Layout: [ARCHITECTURE.md](docs/ARCHITECTURE.md#storage). Back up by copying `data/`. Models stay in `models/kokoro/` (mounted, not in the image).

Upgrades migrate the database on start and first copy it to `data/mark2audio.db.pre-v<N>`. To roll
back: `make down`, restore that file as `data/mark2audio.db`, run the previous release (a newer
database stops an older app with `DB_TOO_NEW`).

## Checks

`make test lint typecheck` (pytest with 80% coverage gate, ruff with security rules, strict mypy).
`make smoke` runs the real-model test (it also runs in `make test` when the model files and FFmpeg exist).

Local CI: `make ci` (needs [`act`](https://github.com/nektos/act)). Opt-in scans, off by default:
`make trivy`, `make sonar` ([ARCHITECTURE.md](docs/ARCHITECTURE.md#optional-tooling-off-by-default)).

## Behaviour notes

- Code blocks skipped by default; links read as link text; images ignored; chapters split on `#`.
- Jobs, errors, API: [ARCHITECTURE.md](docs/ARCHITECTURE.md#job-lifecycle).

## Troubleshooting

- _No voices in UI / `MODEL_UNAVAILABLE`_: run `make model`, check `models/kokoro/` has both files.
- _Health `degraded`_: ffmpeg/ffprobe missing from PATH.
- _Permission denied on `data/`_: container runs as uid 1000; `chown -R 1000 data`.
- _`phonemizer words count mismatch` warnings in the worker log_: seen on every real conversion; the audio is fine and the log contains no document text.
- _Worker `unhealthy` in `docker compose ps`_: its heartbeat file is stale, so the worker is
  stopped or stuck; see `docker compose logs worker`. One very long FFmpeg encode can also show
  it. Compose does not restart on it ([D-020](docs/DECISION.md#d-020--worker-health-check-by-heartbeat-file)).
- _`DISK_FULL` error_: free disk space under `data/` and convert again.
- _Known limitation_: if deleting a book fails to remove its files, orphans can stay in
  `data/uploads/<id>` or `data/audio/<id>`. The UI does not show them; remove the folder by hand.

## Status

Built vs planned: [ROADMAP.md](docs/ROADMAP.md#requirements-status). Why it differs from the first plan: [DECISION.md](docs/DECISION.md).

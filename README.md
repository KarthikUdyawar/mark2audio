# Mark2Audio

Markdown in, MP3 out. Local TTS (Kokoro ONNX) + FFmpeg. Nothing leaves your machine.
Docs: [ROADMAP](docs/ROADMAP.md) · [ARCHITECTURE](docs/ARCHITECTURE.md) · [DESIGN](docs/DESIGN.md) · [DECISION](docs/DECISION.md) · [CLAUDE.md](CLAUDE.md).

## Run

```bash
make model          # once, needs internet: downloads Kokoro model + voices into models/kokoro/
make up             # docker compose: api (+UI) and worker, bound to 127.0.0.1:8000
```

Open <http://127.0.0.1:8000>, drop a `.md`, pick voice/speed, Convert, play or download.
After `make model`, conversion needs no network.

Native dev: `make install hooks`, then `make api` and `make worker` in two terminals.
No model yet? `M2A_FAKE_TTS=1` makes sine-tone audio to try the pipeline.

## Data

Layout: [ARCHITECTURE.md](docs/ARCHITECTURE.md#storage). Back up by copying `data/`. Models stay in `models/kokoro/` (mounted, not in the image).

## Checks

`make test lint typecheck` (pytest with 80% coverage gate, ruff, strict mypy, bandit).
A real-model smoke test runs automatically when model files exist.

Local CI: `make ci` (needs [`act`](https://github.com/nektos/act)). Opt-in scans, off by default:
`make trivy`, `make sonar` ([ARCHITECTURE.md](docs/ARCHITECTURE.md#optional-tooling-off-by-default)).

## Behaviour notes

- Code blocks skipped by default; links read as link text; images ignored; chapters split on `#`.
- Jobs, errors, API: [ARCHITECTURE.md](docs/ARCHITECTURE.md#job-lifecycle).

## Troubleshooting

- _No voices in UI / `MODEL_UNAVAILABLE`_: run `make model`, check `models/kokoro/` has both files.
- _Health `degraded`_: ffmpeg/ffprobe missing from PATH.
- _Permission denied on `data/`_: container runs as uid 1000; `chown -R 1000 data`.

## Status

Built vs planned: [ROADMAP.md](docs/ROADMAP.md#requirements-status). Why it differs from the first plan: [DECISION.md](docs/DECISION.md).

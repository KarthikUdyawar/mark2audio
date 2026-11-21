# S1 — Tasks

One commit per task. Goal and acceptance: [PRD.md](PRD.md).

- [ ] T0 Sprint S1 PRD and TODO
- [ ] T1 D-016 merge flow; fix CLAUDE.md step 6; tick S0 T21; ROADMAP S0 done, S1 planned
- [ ] T2 Smoke test: repo-root model path, both files, synth, encode and probe; `make smoke`
- [ ] T3 Adapter audit against `kokoro-onnx` 0.6.1: failing stub-Kokoro test per defect, then fix
- [ ] T4 Chunk size vs real model input limit: measure, adjust default or chunker (test first)
- [ ] T5 Measure real-time factor and peak memory; listen to chunk joins and silence; record
- [ ] T6 Confirm model URLs, revision, license and sha256 upstream; D-017
- [ ] T7 `make model`: pinned URLs, sha256 variables, `sha256sum -c`
- [ ] T8 Replace "unverified" text in ARCHITECTURE, ROADMAP FR-04/05 and the `tts_kokoro.py` docstring
- [ ] T9 `make up`: build, run, convert through the stack; fix what breaks
- [ ] T10 Dockerfile and `uv.lock`: decide; D-018 only if needed
- [ ] T11 `docker-compose.offline.yml`; prove offline conversion and a failing outbound connect
- [ ] T12 README troubleshooting and bind-mount permissions checked against real behavior
- [ ] T13 Test for `app/main.py` (test first)
- [ ] T14 Worker coverage gaps from `--cov-report=term-missing`
- [ ] T15 Pin GitHub Actions by commit SHA (confirm peeled commit with `^{}`)
- [ ] T16 Review sprint diff (CLAUDE.md section 18), fix findings
- [ ] T17 PR to `develop`, `release/v0.1.0` PR to `main`, tag `v0.1.0`, handoff

Cut line if the sprint runs long: T15 first, then T10.

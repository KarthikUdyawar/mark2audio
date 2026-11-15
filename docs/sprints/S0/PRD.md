# S0 — Setup

Release `v0.0.0` · Branch `feature/s0-setup` · Tasks: [TODO.md](TODO.md)
Plan: [ROADMAP.md](../../ROADMAP.md#sprints) · Workflow: [CLAUDE.md](../../../CLAUDE.md#21-project-mark2audio)

## Goal

Make the repository safe and repeatable to work in before any new feature: documents, git flow,
quality gates automated. No product behavior changes.

## In scope

- S0-R1 Git history: baseline commit on `main`, `develop`, sprint branch.
- S0-R2 Documents: ROADMAP, ARCHITECTURE, DESIGN, DECISION, CLAUDE.md, README, sprint docs; no
  duplicated facts, links between them.
- S0-R3 Reproducible dependencies: committed `backend/uv.lock`, Python 3.12 pinned.
- S0-R4 Local gates: pre-commit (`make hooks`) runs hygiene, secrets, spelling, formatting, ruff,
  mypy, commit-message format; tests on push.
- S0-R5 CI: GitHub Actions runs `make lint typecheck test` (80% coverage gate).
- S0-R6 Config hygiene: `.env.example` matches [ARCHITECTURE.md](../../ARCHITECTURE.md#configuration);
  compose pins container paths.
- S0-R7 Release: merge to `develop`, `release/v0.0.0` to `main`, tag `v0.0.0`.
- S0-R8 Tooling, off by default: local CI with `act`, Trivy, SonarQube
  ([D-013](../../DECISION.md)). Ruff rule set replaces bandit.

## Out of scope

Verifying Kokoro/Docker/offline, model checksum and license, new features, UI rewrite, frontend CI
(no Node toolchain). Candidates for S1: [ROADMAP.md](../../ROADMAP.md#unscheduled-candidates).

## Acceptance

- Fresh clone: `make install hooks && make test lint typecheck` passes.
- `pre-commit run --all-files` passes.
- `make ci` (act) passes locally on the sprint branch; CI is green on `develop` after the
  merge ([D-015](../../DECISION.md)).
- Every doc link resolves; no fact stated in two docs.
- `git tag` shows `v0.0.0` on `main`.

## Risks

- CI cannot run the real-model smoke test (no model files): it stays skipped.
- Free plan: no branch protection; the `no-commit-to-branch` hook and discipline only
  ([DECISION.md](../../DECISION.md#d-007--branching-and-releases)).

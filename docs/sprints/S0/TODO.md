# S0 — Tasks

One commit per task. Goal and acceptance: [PRD.md](PRD.md).

- [x] T1 Baseline commit, `main` / `develop` / `feature/s0-setup` (`cd46e5b`)
- [x] T2 Rename PRD → ROADMAP, TECH_RULES → ARCHITECTURE (`21db89c`)
- [x] T3 CLAUDE.md: principles, project section, path rule, link example (`c894e70`, `f9f55f5`, `6d87012`, `92e1bca`)
- [x] T4 ARCHITECTURE and DESIGN as built (`06fad98`, `33267bb`)
- [x] T5 DESIGN: UI flow and form (`4c9599a`)
- [x] T6 DECISION.md D-001 to D-009 (`2e0e0f5`)
- [x] T7 ROADMAP with sprint plan, remove old TODO.md (`de5cc22`)
- [x] T8 README links, remove duplicates (`0e4a89b`)
- [x] T9 Sprint S0 PRD and TODO (`94acd47`)
- [x] T10 `uv.lock` committed; Makefile uses `uv run` (`15a76a1`)
- [x] T11 `.pre-commit-config.yaml` (`1ff03ce`, `c21b848`)
- [x] T12 `.github/workflows/ci.yml` (`fcd256e`)
- [x] T13 `.env.example` and Makefile checked; compose paths pinned, D-010, D-011 (`4089775`)
- [x] T14 Dev tools in `[dependency-groups]`, `httpx2` replaces `httpx` (`656dcae`)
- [x] T15 Pre-commit v2: hygiene, gitleaks, codespell, prettier, commit-msg, pytest on push (`9d52ccc`)
- [x] T16 Format pass from the new hooks (`bedc888`)
- [x] T17 Ruff rule set (D, PL, S, N, …), fix findings, drop bandit, tool tables in pyproject (`b81c523`, `5021c93`, `52d54ff`, `76fdf69`, `a685983`)
- [x] T18 CI hardening, `make ci` with `act` (`44b812b`)
- [x] T19 Opt-in `make trivy` and `make sonar` (`96f75fb`, `5987421`)
- [x] T22 `make lint` runs all pre-commit hooks, as the docs state
- [x] T23 Map `docs/STRUCTURE.md` in the CLAUDE.md documentation map
- [ ] T20 Review sprint diff (CLAUDE.md section 18), fix findings
- [ ] T21 Merge to `develop`, `release/v0.0.0` → `main`, tag `v0.0.0`, back-merge, handoff

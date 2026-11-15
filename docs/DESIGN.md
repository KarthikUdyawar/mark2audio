# Mark2Audio — UI Design

UI as built. Backend and API: [ARCHITECTURE.md](ARCHITECTURE.md#api). Planned UI work:
[ROADMAP.md](ROADMAP.md).

## As built

- One file, `backend/app/static/index.html`: vanilla JS, no build step, served by the API process
  (`http://127.0.0.1:8000`).
- Every server call goes through one `fetch("/api/v1" + path)` helper.
- Library view: `#books` list. Book detail view: `#title`.
- Detail actions: Convert (`#go`), Cancel (`#cancel`, hidden by default), Delete book (`#del`).

## Rules

Rules 1–3 target a TypeScript UI and apply when the UI is rewritten; the rest apply now.

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

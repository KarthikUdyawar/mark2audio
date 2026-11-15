# Mark2Audio — UI Design

UI as built. Backend and API: [ARCHITECTURE.md](ARCHITECTURE.md#api). Planned UI work:
[ROADMAP.md](ROADMAP.md).

## As built

One file, `backend/app/static/index.html`: vanilla JS, no build step, served by the API process
(`http://127.0.0.1:8000`). Every server call goes through one `fetch("/api/v1" + path)` helper.

### Views

- **Upload**: drop zone (`#drop`) and file input (`.md`, `.markdown`). Messages in `#upmsg`.
- **Library**: `#books`, one button per book, labelled `Title (status)`.
- **Detail** (`#detail`, hidden until a book is opened): title, chapter outline (`#chapters`,
  titles only), convert form, job message (`#jobmsg`), progress bar (`#bar`), result (`#result`).

### Convert form

Voice (only voices the API reports as `available`), speed (0.8–1.2, step 0.05, default 1),
bitrate (128, 192, 256; default 192), "Read code blocks aloud" checkbox. Sent as `voice_id`,
`speed`, `bitrate_kbps`, `include_code_blocks`. The UI does not send `language`.

### Flow

1. Upload (picker or drop) → `POST /books/upload` → reload library → open the new book.
2. Open book → `GET /books/{id}` and `GET /voices`; show the latest job; resume polling if it is
   not terminal.
3. Convert → Convert button disabled, `POST /books/{id}/convert`, then poll `GET /jobs/{id}` every
   1500 ms until `completed`, `failed` or `cancelled`; then reload the library.
4. Cancel button is visible only while a job is active.
5. Failed job: `Failed: <message>` in `#jobmsg` (class `err`).
6. Completed: `<audio controls>` and a download link on `/books/{id}/audio` (cache-busting `?t=`).
7. Delete → browser `confirm` → `DELETE /books/{id}` → detail hidden.

API contract: [ARCHITECTURE.md](ARCHITECTURE.md#api).

### Accessibility

Labelled inputs, `role="status"` messages, `aria-live` on the detail section, native `button`,
`progress` and `audio` elements. Not audited.

### Gaps

No settings page, duration display or chapter downloads. No TypeScript, no UI tests, script is
inline. Planned work: [ROADMAP.md](ROADMAP.md).

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

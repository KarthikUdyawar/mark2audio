CREATE TABLE IF NOT EXISTS books (
  id TEXT PRIMARY KEY, title TEXT NOT NULL, original_filename TEXT NOT NULL,
  chapter_count INTEGER NOT NULL, created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS jobs (
  id TEXT PRIMARY KEY,
  book_id TEXT NOT NULL REFERENCES books(id) ON DELETE CASCADE,
  status TEXT NOT NULL, voice_id TEXT NOT NULL, language TEXT NOT NULL, speed REAL NOT NULL,
  bitrate_kbps INTEGER NOT NULL, include_code_blocks INTEGER NOT NULL,
  total_chunks INTEGER NOT NULL DEFAULT 0, completed_chunks INTEGER NOT NULL DEFAULT 0,
  progress_percent INTEGER NOT NULL DEFAULT 0, current_chapter TEXT,
  error_code TEXT, error_message TEXT,
  created_at TEXT NOT NULL, started_at TEXT, completed_at TEXT);

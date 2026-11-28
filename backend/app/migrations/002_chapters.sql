ALTER TABLE books ADD COLUMN duration_seconds REAL;
CREATE TABLE chapters (
  book_id TEXT NOT NULL REFERENCES books(id) ON DELETE CASCADE,
  number INTEGER NOT NULL,
  title TEXT NOT NULL DEFAULT '',
  start_seconds REAL,
  duration_seconds REAL,
  PRIMARY KEY (book_id, number));

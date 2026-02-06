CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS attachments (
  id BIGSERIAL PRIMARY KEY,
  uuid UUID NOT NULL UNIQUE,
  exam_uuid TEXT NOT NULL,

  original_filename TEXT NOT NULL,
  mime_type TEXT NOT NULL,
  size_bytes INTEGER NOT NULL,
  sha256_hash TEXT NOT NULL,

  storage_path TEXT NOT NULL, -- caminho relativo
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  
  CONSTRAINT fk_attachments_exam
    FOREIGN KEY (exam_uuid) REFERENCES public.exams(uuid)
    ON UPDATE CASCADE
    ON DELETE CASCADE
  
);

CREATE INDEX IF NOT EXISTS idx_attachments_exam_uuid ON attachments (exam_uuid);
CREATE INDEX IF NOT EXISTS idx_attachments_sha256_hash ON attachments (sha256);

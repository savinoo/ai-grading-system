CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS attachments (
  id BIGSERIAL PRIMARY KEY,
  uuid UUID NOT NULL UNIQUE DEFAULT gen_random_uuid(),
  exam_uuid UUID NOT NULL,

  original_filename TEXT NOT NULL,
  mime_type TEXT NOT NULL,
  size_bytes INTEGER NOT NULL,
  sha256_hash TEXT NOT NULL,
  
  vector_status VARCHAR(50) NOT NULL DEFAULT 'DRAFT',

  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  
  CONSTRAINT fk_attachments_exam
    FOREIGN KEY (exam_uuid) REFERENCES public.exams(uuid)
    ON UPDATE CASCADE
    ON DELETE CASCADE,
    
  CONSTRAINT chk_attachments_vector_status 
    CHECK (vector_status IN ('DRAFT', 'SUCCESS', 'FAILED'))
  
);

CREATE INDEX IF NOT EXISTS idx_attachments_exam_uuid ON attachments (exam_uuid);
CREATE INDEX IF NOT EXISTS idx_attachments_sha256_hash ON attachments (sha256_hash);
CREATE INDEX IF NOT EXISTS idx_attachments_vector_status ON attachments (vector_status);

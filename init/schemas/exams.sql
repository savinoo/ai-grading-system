CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS public.exams (
  id BIGSERIAL PRIMARY KEY,
  uuid UUID NOT NULL DEFAULT gen_random_uuid(),

  title VARCHAR(255) NOT NULL,
  description TEXT NULL,

  created_by UUID NULL, -- opcional: users.uuid (quem criou)
  status VARCHAR(50) NOT NULL DEFAULT 'DRAFT', -- DRAFT, ACTIVE, GRADING, GRADED, FINALIZED, PUBLISHED, ARCHIVED
  class_uuid UUID null,

  starts_at TIMESTAMPTZ NULL,
  ends_at   TIMESTAMPTZ NULL,

  active BOOLEAN NOT NULL DEFAULT TRUE,

  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  
  CONSTRAINT uq_exams_uuid UNIQUE (uuid),
  CONSTRAINT chk_exams_status CHECK (status IN ('DRAFT','ACTIVE','GRADING','GRADED','FINALIZED','PUBLISHED','ARCHIVED')),
  CONSTRAINT chk_exams_window CHECK (
    starts_at IS NULL OR ends_at IS NULL OR starts_at < ends_at
  ),

  CONSTRAINT fk_exams_created_by
    FOREIGN KEY (created_by) REFERENCES public.users(uuid)
    ON UPDATE CASCADE
    ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_exams_active ON public.exams(active);
CREATE INDEX IF NOT EXISTS idx_exams_status ON public.exams(status);
CREATE INDEX IF NOT EXISTS idx_exams_created_by ON public.exams(created_by);
CREATE INDEX IF NOT EXISTS idx_exams_class_uuid ON public.exams(class_uuid);


CREATE OR REPLACE FUNCTION public.set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;


DROP TRIGGER IF EXISTS trg_exams_updated_at ON public.exams;
CREATE TRIGGER trg_exams_updated_at
BEFORE UPDATE ON public.exams
FOR EACH ROW
EXECUTE FUNCTION public.set_updated_at();

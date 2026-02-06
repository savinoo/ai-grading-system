CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS public.exam_questions (
  id BIGSERIAL PRIMARY KEY,
  uuid UUID NOT NULL DEFAULT gen_random_uuid(),

  exam_uuid UUID NOT NULL,

  question_order INTEGER NOT NULL, -- ordem na prova

  statement TEXT NOT NULL, -- enunciado
  points NUMERIC(8,2) NOT NULL DEFAULT 1.00,

  active BOOLEAN NOT NULL DEFAULT TRUE,

  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

  CONSTRAINT uq_exam_questions_uuid UNIQUE (uuid),
  CONSTRAINT chk_exam_questions_points CHECK (points >= 0),
  CONSTRAINT chk_exam_questions_order CHECK (question_order >= 1),

  CONSTRAINT fk_exam_questions_exam
    FOREIGN KEY (exam_uuid) REFERENCES public.exams(uuid)
    ON UPDATE CASCADE
    ON DELETE CASCADE
);

-- garante que não exista duas perguntas com o mesmo número na mesma prova
CREATE UNIQUE INDEX IF NOT EXISTS uq_exam_questions_exam_order
ON public.exam_questions (exam_uuid, question_order);

CREATE INDEX IF NOT EXISTS idx_exam_questions_exam_uuid
ON public.exam_questions (exam_uuid);

CREATE INDEX IF NOT EXISTS idx_exam_questions_active
ON public.exam_questions (active);

CREATE OR REPLACE FUNCTION public.set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_exam_questions_updated_at ON public.exam_questions;
CREATE TRIGGER trg_exam_questions_updated_at
BEFORE UPDATE ON public.exam_questions
FOR EACH ROW
EXECUTE FUNCTION public.set_updated_at();

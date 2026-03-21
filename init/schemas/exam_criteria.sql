CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS public.exam_criteria (
  id BIGSERIAL PRIMARY KEY,
  uuid UUID NOT NULL DEFAULT gen_random_uuid(),

  exam_uuid UUID NOT NULL,
  criteria_uuid UUID NOT NULL,

  weight NUMERIC(8,4) NOT NULL DEFAULT 1.0,
  max_points NUMERIC(8,2) NULL,
  active BOOLEAN NOT NULL DEFAULT TRUE,

  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

  CONSTRAINT uq_exam_criteria_uuid UNIQUE (uuid),
  CONSTRAINT uq_exam_criteria_exam_criteria UNIQUE (exam_uuid, criteria_uuid),
  CONSTRAINT chk_exam_criteria_weight CHECK (weight > 0),

  CONSTRAINT fk_exam_criteria_exam
    FOREIGN KEY (exam_uuid) REFERENCES public.exams(uuid)
    ON UPDATE CASCADE ON DELETE CASCADE,

  CONSTRAINT fk_exam_criteria_criteria
    FOREIGN KEY (criteria_uuid) REFERENCES public.grading_criteria(uuid)
    ON UPDATE CASCADE ON DELETE RESTRICT
);

CREATE INDEX IF NOT EXISTS idx_exam_criteria_exam_uuid
ON public.exam_criteria (exam_uuid);

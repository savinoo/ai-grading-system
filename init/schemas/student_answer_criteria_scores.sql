CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS public.student_answer_criteria_scores (
  id BIGSERIAL PRIMARY KEY,
  uuid UUID NOT NULL DEFAULT gen_random_uuid(),

  student_answer_uuid UUID NOT NULL,
  criteria_uuid UUID NOT NULL,

  raw_score NUMERIC(8,2) NOT NULL DEFAULT 0,  -- quanto ganhou (bruto)
  weighted_score NUMERIC(8,2) NULL,           -- opcional: armazenar já ponderado
  feedback TEXT NULL,                         -- feedback específico do critério

  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

  CONSTRAINT fk_sacs_answer
    FOREIGN KEY (student_answer_uuid) REFERENCES public.student_answers(uuid)
    ON UPDATE CASCADE ON DELETE CASCADE,

  CONSTRAINT fk_sacs_criteria
    FOREIGN KEY (criteria_uuid) REFERENCES public.grading_criteria(uuid)
    ON UPDATE CASCADE ON DELETE RESTRICT,

  CONSTRAINT chk_sacs_raw_score CHECK (raw_score >= 0)
);

-- evita duplicar o mesmo critério para a mesma resposta
CREATE UNIQUE INDEX IF NOT EXISTS uq_sacs_answer_criteria
ON public.student_answer_criteria_scores (student_answer_uuid, criteria_uuid);

CREATE INDEX IF NOT EXISTS idx_sacs_answer
ON public.student_answer_criteria_scores (student_answer_uuid);

CREATE INDEX IF NOT EXISTS idx_sacs_criteria
ON public.student_answer_criteria_scores (criteria_uuid);

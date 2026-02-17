CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS public.student_answers (
  id BIGSERIAL PRIMARY KEY,
  uuid UUID NOT NULL DEFAULT gen_random_uuid(),

  exam_uuid UUID NOT NULL,
  question_uuid UUID NOT NULL,

  student_uuid UUID NOT NULL, -- users.uuid

  answer TEXT NULL,

  status VARCHAR(20) NOT NULL DEFAULT 'SUBMITTED', -- SUBMITTED, GRADED, FINALIZED, INVALID
  score NUMERIC(8,2) NULL,
  feedback TEXT NULL,
  graded_at TIMESTAMPTZ NULL,
  graded_by UUID NULL, -- users.uuid (avaliador)

  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

  CONSTRAINT uq_student_answers_uuid UNIQUE (uuid),
  CONSTRAINT chk_student_answers_status CHECK (status IN ('SUBMITTED','GRADED','FINALIZED','INVALID')),
  CONSTRAINT chk_student_answers_score CHECK (score IS NULL OR score >= 0),

  CONSTRAINT fk_student_answers_exam
    FOREIGN KEY (exam_uuid) REFERENCES public.exams(uuid)
    ON UPDATE CASCADE
    ON DELETE CASCADE,

  CONSTRAINT fk_student_answers_question
    FOREIGN KEY (question_uuid) REFERENCES public.exam_questions(uuid)
    ON UPDATE CASCADE
    ON DELETE CASCADE,

  CONSTRAINT fk_student_answers_student
    FOREIGN KEY (student_uuid) REFERENCES public.students(uuid)
    ON UPDATE CASCADE
    ON DELETE CASCADE,

  CONSTRAINT fk_student_answers_graded_by
    FOREIGN KEY (graded_by) REFERENCES public.users(uuid)
    ON UPDATE CASCADE
    ON DELETE SET NULL
);

-- evita o aluno responder 2x a mesma questão da mesma prova (ajuste se quiser múltiplas tentativas)
CREATE UNIQUE INDEX IF NOT EXISTS uq_student_answers_student_exam_question
ON public.student_answers (student_uuid, exam_uuid, question_uuid);

CREATE INDEX IF NOT EXISTS idx_student_answers_student
ON public.student_answers (student_uuid);

CREATE INDEX IF NOT EXISTS idx_student_answers_exam
ON public.student_answers (exam_uuid);

CREATE INDEX IF NOT EXISTS idx_student_answers_question
ON public.student_answers (question_uuid);

CREATE INDEX IF NOT EXISTS idx_student_answers_status
ON public.student_answers (status);

CREATE OR REPLACE FUNCTION public.set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_student_answers_updated_at ON public.student_answers;
CREATE TRIGGER trg_student_answers_updated_at
BEFORE UPDATE ON public.student_answers
FOR EACH ROW
EXECUTE FUNCTION public.set_updated_at();


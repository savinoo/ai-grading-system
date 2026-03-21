CREATE TABLE IF NOT EXISTS public.exam_question_criteria_override (
  id BIGSERIAL PRIMARY KEY,
  uuid UUID NOT NULL DEFAULT gen_random_uuid(),

  question_uuid UUID NOT NULL,
  criteria_uuid UUID NOT NULL,

  -- Se NULL, significa: "usa o peso do template da prova"
  weight_override NUMERIC(8,4) NULL,
  -- Se NULL, significa: "usa o pontuação do template da prova"
  max_points_override NUMERIC(8,4) NULL,

  -- Se FALSE, o critério fica removido/desativado para a questão
  active BOOLEAN NOT NULL DEFAULT TRUE,

  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

  CONSTRAINT uq_eqco_uuid UNIQUE (uuid),
  CONSTRAINT uq_eqco_question_criteria UNIQUE (question_uuid, criteria_uuid),
  CONSTRAINT chk_eqco_weight CHECK (weight_override IS NULL OR weight_override > 0),

  CONSTRAINT fk_eqco_question
    FOREIGN KEY (question_uuid) REFERENCES public.exam_questions(uuid)
    ON UPDATE CASCADE ON DELETE CASCADE,

  CONSTRAINT fk_eqco_criteria
    FOREIGN KEY (criteria_uuid) REFERENCES public.grading_criteria(uuid)
    ON UPDATE CASCADE ON DELETE RESTRICT
);

CREATE INDEX IF NOT EXISTS idx_eqco_question_uuid
ON public.exam_question_criteria_override (question_uuid);

CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS public.grading_criteria (
  id BIGSERIAL PRIMARY KEY,
  uuid UUID NOT NULL DEFAULT gen_random_uuid(),

  code VARCHAR(50) NOT NULL UNIQUE, -- ex: CLAREZA, COERENCIA, GRAMATICA
  name VARCHAR(255) NOT NULL,
  description TEXT NULL,

  active BOOLEAN NOT NULL DEFAULT TRUE,

  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_grading_criteria_uuid
ON public.grading_criteria (uuid);

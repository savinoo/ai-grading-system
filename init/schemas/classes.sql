CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS public.classes (
    id BIGSERIAL PRIMARY KEY,
    uuid UUID NOT NULL DEFAULT gen_random_uuid(),

    name VARCHAR(255) NOT NULL, -- ex: "3º Ano A"
    description TEXT NULL,
    
    teacher_uuid UUID null, 

    year INTEGER NULL, -- ex: 2025
    semester INTEGER NULL, -- ex: 1

    created_by UUID NULL, -- professor (users.uuid)

    active BOOLEAN NOT NULL DEFAULT TRUE,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT uq_classes_uuid UNIQUE (uuid),

    constraint fk_classes_teacher_uuid foreign key (teacher_uuid) REFERENCES public.users(uuid) ON UPDATE cascade ON DELETE SET NULL
    
    CONSTRAINT fk_classes_created_by
      FOREIGN KEY (created_by) REFERENCES public.users(uuid)
      ON UPDATE CASCADE
      ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_classes_active ON public.classes(active);
CREATE INDEX IF NOT EXISTS idx_classes_year ON public.classes(year);
CREATE INDEX IF NOT EXISTS idx_classes_created_by ON public.classes(created_by);

DROP TRIGGER IF EXISTS trg_classes_updated_at ON public.classes;
CREATE TRIGGER trg_classes_updated_at
BEFORE UPDATE ON public.classes
FOR EACH ROW
EXECUTE FUNCTION public.set_updated_at();

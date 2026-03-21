CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS public.class_students (
    id BIGSERIAL PRIMARY KEY,

    class_uuid UUID NOT NULL,
    student_uuid UUID NOT NULL,

    enrolled_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    active BOOLEAN NOT NULL DEFAULT TRUE,

    CONSTRAINT uq_class_students UNIQUE (class_uuid, student_uuid),

    CONSTRAINT fk_class_students_class
      FOREIGN KEY (class_uuid) REFERENCES public.classes(uuid)
      ON UPDATE CASCADE
      ON DELETE CASCADE,

    CONSTRAINT fk_class_students_student
      FOREIGN KEY (student_uuid) REFERENCES public.students(uuid)
      ON UPDATE CASCADE
      ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_class_students_class ON public.class_students(class_uuid);
CREATE INDEX IF NOT EXISTS idx_class_students_student ON public.class_students(student_uuid);
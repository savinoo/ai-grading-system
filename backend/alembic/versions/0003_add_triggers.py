"""add updated_at triggers

Revision ID: 68e87c53e449
Revises: 7aa473382699
Create Date: 2026-02-06 17:59:38.917454

"""
from alembic import op

revision = "0003_add_triggers"
down_revision = "0002_initial_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # users
    op.execute("""
    DROP TRIGGER IF EXISTS trg_users_updated_at ON public.users;
    CREATE TRIGGER trg_users_updated_at
    BEFORE UPDATE ON public.users
    FOR EACH ROW
    EXECUTE FUNCTION public.set_updated_at();
    """)

    # classes
    op.execute("""
    DROP TRIGGER IF EXISTS trg_classes_updated_at ON public.classes;
    CREATE TRIGGER trg_classes_updated_at
    BEFORE UPDATE ON public.classes
    FOR EACH ROW
    EXECUTE FUNCTION public.set_updated_at();
    """)

    # exam_questions
    op.execute("""
    DROP TRIGGER IF EXISTS trg_exam_questions_updated_at ON public.exam_questions;
    CREATE TRIGGER trg_exam_questions_updated_at
    BEFORE UPDATE ON public.exam_questions
    FOR EACH ROW
    EXECUTE FUNCTION public.set_updated_at();
    """)

    # student_answers
    op.execute("""
    DROP TRIGGER IF EXISTS trg_student_answers_updated_at ON public.student_answers;
    CREATE TRIGGER trg_student_answers_updated_at
    BEFORE UPDATE ON public.student_answers
    FOR EACH ROW
    EXECUTE FUNCTION public.set_updated_at();
    """)

    # ... repete para as demais tabelas que tiverem updated_at


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS trg_student_answers_updated_at ON public.student_answers;")
    op.execute("DROP TRIGGER IF EXISTS trg_exam_questions_updated_at ON public.exam_questions;")
    op.execute("DROP TRIGGER IF EXISTS trg_classes_updated_at ON public.classes;")
    op.execute("DROP TRIGGER IF EXISTS trg_users_updated_at ON public.users;")

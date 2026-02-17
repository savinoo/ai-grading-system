"""update_status_constraints_for_exams_and_student_answers

Revision ID: f778ab1e7755
Revises: 0007_add_warning_graded_status
Create Date: 2026-02-17 13:34:46.238176

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f778ab1e7755'
down_revision: Union[str, Sequence[str], None] = '0007_add_warning_graded_status'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Atualizar constraint de status em exams
    # Remove constraint antigo
    op.drop_constraint('chk_exams_status', 'exams', schema='public', type_='check')
    
    # Adiciona novo constraint com novos status: ACTIVE, GRADING, FINALIZED
    op.create_check_constraint(
        'chk_exams_status',
        'exams',
        "status IN ('DRAFT','ACTIVE','GRADING','GRADED','FINALIZED','PUBLISHED','ARCHIVED')",
        schema='public'
    )
    
    # Atualizar constraint de status em student_answers
    # Remove constraint antigo
    op.drop_constraint('chk_student_answers_status', 'student_answers', schema='public', type_='check')
    
    # Adiciona novo constraint com novo status: FINALIZED
    op.create_check_constraint(
        'chk_student_answers_status',
        'student_answers',
        "status IN ('SUBMITTED','GRADED','FINALIZED','INVALID')",
        schema='public'
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Reverter constraint de status em exams
    op.drop_constraint('chk_exams_status', 'exams', schema='public', type_='check')
    
    # Volta ao constraint antigo
    op.create_check_constraint(
        'chk_exams_status',
        'exams',
        "status IN ('DRAFT','PUBLISHED','ARCHIVED','FINISHED','WARNING','GRADED')",
        schema='public'
    )
    
    # Reverter constraint de status em student_answers
    op.drop_constraint('chk_student_answers_status', 'student_answers', schema='public', type_='check')
    
    # Volta ao constraint antigo
    op.create_check_constraint(
        'chk_student_answers_status',
        'student_answers',
        "status IN ('SUBMITTED','GRADED','INVALID')",
        schema='public'
    )

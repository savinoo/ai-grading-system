"""add WARNING and GRADED status to exams

Revision ID: 0007_add_warning_graded_status
Revises: 0006_add_is_graded_columns
Create Date: 2026-02-09 20:00:00.000000

"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision = "0007_add_warning_graded_status"
down_revision = "0006_add_is_graded_columns"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Adiciona os status 'WARNING' e 'GRADED' ao check constraint de Exams.status.
    
    - WARNING: Indica que houve erro durante indexação ou correção
    - GRADED: Indica que a prova foi corrigida com sucesso
    """
    # Remove constraint antigo
    op.drop_constraint(
        'chk_exams_status',
        'exams',
        schema='public',
        type_='check'
    )
    
    # Adiciona constraint novo com os novos status
    op.create_check_constraint(
        'chk_exams_status',
        'exams',
        "status IN ('DRAFT','PUBLISHED','ARCHIVED','FINISHED','WARNING','GRADED')",
        schema='public'
    )


def downgrade() -> None:
    """
    Remove os status 'WARNING' e 'GRADED' do check constraint.
    """
    # Remove constraint com os novos status
    op.drop_constraint(
        'chk_exams_status',
        'exams',
        schema='public',
        type_='check'
    )
    
    # Restaura constraint original
    op.create_check_constraint(
        'chk_exams_status',
        'exams',
        "status IN ('DRAFT','PUBLISHED','ARCHIVED','FINISHED')",
        schema='public'
    )

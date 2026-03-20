"""add WARNING status back to exams

Revision ID: 0009_add_warning_status_back
Revises: f778ab1e7755
Create Date: 2026-02-17 20:15:00.000000

"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision = "0009_add_warning_status_back"
down_revision = "f778ab1e7755"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Adiciona o status 'WARNING' de volta ao check constraint de Exams.status.
    
    WARNING é usado quando:
    - Falha na indexação de PDFs no ChromaDB
    - Erros parciais durante a correção automática
    """
    # Remove constraint atual
    op.drop_constraint(
        'chk_exams_status',
        'exams',
        schema='public',
        type_='check'
    )
    
    # Adiciona constraint com WARNING incluído
    op.create_check_constraint(
        'chk_exams_status',
        'exams',
        "status IN ('DRAFT','ACTIVE','GRADING','GRADED','FINALIZED','PUBLISHED','ARCHIVED','WARNING')",
        schema='public'
    )


def downgrade() -> None:
    """
    Remove o status 'WARNING' do check constraint.
    """
    # Remove constraint com WARNING
    op.drop_constraint(
        'chk_exams_status',
        'exams',
        schema='public',
        type_='check'
    )
    
    # Restaura constraint sem WARNING
    op.create_check_constraint(
        'chk_exams_status',
        'exams',
        "status IN ('DRAFT','ACTIVE','GRADING','GRADED','FINALIZED','PUBLISHED','ARCHIVED')",
        schema='public'
    )

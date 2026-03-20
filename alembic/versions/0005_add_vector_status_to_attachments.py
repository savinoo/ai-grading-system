"""add vector status to attachments

Revision ID: 0005_add_vector_status
Revises: 0004_seed_grading_criteria
Create Date: 2026-02-07 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = "0005_add_vector_status"
down_revision = "0004_seed_grading_criteria"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Adiciona coluna vector_status à tabela attachments.
    
    Esta coluna rastreia o status do processamento do arquivo no banco vetorial:
    - DRAFT: Arquivo aguardando processamento (prova ainda não publicada)
    - SUCCESS: Embedding processado e armazenado com sucesso no ChromaDB
    - FAILED: Falha no processamento do embedding
    """
    # Adiciona a coluna vector_status
    op.add_column(
        'attachments',
        sa.Column(
            'vector_status',
            sa.String(50),
            nullable=False,
            server_default='DRAFT'
        ),
        schema='public'
    )
    
    # Adiciona constraint de validação
    op.create_check_constraint(
        'chk_attachments_vector_status',
        'attachments',
        "vector_status IN ('DRAFT', 'SUCCESS', 'FAILED')",
        schema='public'
    )
    
    # Adiciona índice para otimizar consultas por status
    op.create_index(
        'idx_attachments_vector_status',
        'attachments',
        ['vector_status'],
        schema='public'
    )


def downgrade() -> None:
    """Remove as alterações da migration."""
    # Remove índice
    op.drop_index(
        'idx_attachments_vector_status',
        table_name='attachments',
        schema='public'
    )
    
    # Remove constraint
    op.drop_constraint(
        'chk_attachments_vector_status',
        'attachments',
        schema='public',
        type_='check'
    )
    
    # Remove coluna
    op.drop_column(
        'attachments',
        'vector_status',
        schema='public'
    )

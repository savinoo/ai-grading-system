"""add is_graded column to exam_questions and student_answers

Revision ID: 0006_add_is_graded_columns
Revises: 0005_add_vector_status
Create Date: 2026-02-08 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = "0006_add_is_graded_columns"
down_revision = "0005_add_vector_status"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Adiciona coluna is_graded às tabelas exam_questions e student_answers.
    
    Esta coluna indica se a questão ou resposta já foi corrigida, impedindo
    modificações após a correção.
    """
    # Adiciona a coluna is_graded à tabela exam_questions
    op.add_column(
        'exam_questions',
        sa.Column(
            'is_graded',
            sa.Boolean(),
            nullable=False,
            server_default='FALSE'
        ),
        schema='public'
    )
    
    # Adiciona índice para otimizar consultas por is_graded em exam_questions
    op.create_index(
        'idx_exam_questions_is_graded',
        'exam_questions',
        ['is_graded'],
        schema='public'
    )
    
    # Adiciona a coluna is_graded à tabela student_answers
    op.add_column(
        'student_answers',
        sa.Column(
            'is_graded',
            sa.Boolean(),
            nullable=False,
            server_default='FALSE'
        ),
        schema='public'
    )
    
    # Adiciona índice para otimizar consultas por is_graded em student_answers
    op.create_index(
        'idx_student_answers_is_graded',
        'student_answers',
        ['is_graded'],
        schema='public'
    )


def downgrade() -> None:
    """Remove as alterações da migration."""
    # Remove índice de student_answers
    op.drop_index(
        'idx_student_answers_is_graded',
        table_name='student_answers',
        schema='public'
    )
    
    # Remove coluna de student_answers
    op.drop_column(
        'student_answers',
        'is_graded',
        schema='public'
    )
    
    # Remove índice de exam_questions
    op.drop_index(
        'idx_exam_questions_is_graded',
        table_name='exam_questions',
        schema='public'
    )
    
    # Remove coluna de exam_questions
    op.drop_column(
        'exam_questions',
        'is_graded',
        schema='public'
    )

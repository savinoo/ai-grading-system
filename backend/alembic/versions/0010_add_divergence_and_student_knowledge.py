"""add divergence fields and student knowledge tables

Revision ID: 0010_add_divergence_and_student_knowledge
Revises: 0009_add_warning_status_back
Create Date: 2026-03-16 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "0010_add_divergence_and_student_knowledge"
down_revision: Union[str, Sequence[str], None] = "0009_add_warning_status_back"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Adiciona campos de divergencia em student_answers e cria tabelas
    de perfil de aprendizagem (student_learning_profiles, student_learning_gaps).
    """
    # --- 1. Campos de divergencia em student_answers ---
    op.add_column(
        'student_answers',
        sa.Column(
            'divergence_detected',
            sa.Boolean(),
            server_default=sa.text('FALSE'),
            nullable=False,
        ),
        schema='public',
    )
    op.add_column(
        'student_answers',
        sa.Column(
            'divergence_value',
            sa.Numeric(precision=8, scale=4),
            nullable=True,
        ),
        schema='public',
    )
    op.create_index(
        'idx_student_answers_divergence',
        'student_answers',
        ['divergence_detected'],
        unique=False,
        schema='public',
    )

    # --- 2. Tabela student_learning_profiles ---
    op.create_table(
        'student_learning_profiles',
        sa.Column('id', sa.BigInteger(), nullable=False),
        sa.Column('uuid', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('student_uuid', sa.UUID(), nullable=False),
        sa.Column('total_submissions', sa.Integer(), server_default=sa.text('0'), nullable=False),
        sa.Column('avg_grade', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('grade_trend', sa.String(length=20), nullable=True),
        sa.Column('last_updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.CheckConstraint(
            "grade_trend IS NULL OR grade_trend IN ('improving', 'declining', 'stable')",
            name='chk_slp_grade_trend',
        ),
        sa.ForeignKeyConstraint(
            ['student_uuid'],
            ['public.students.uuid'],
            onupdate='CASCADE',
            ondelete='CASCADE',
        ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('uuid'),
        schema='public',
    )
    op.create_index(
        'idx_slp_student_uuid',
        'student_learning_profiles',
        ['student_uuid'],
        unique=False,
        schema='public',
    )

    # --- 3. Tabela student_learning_gaps ---
    op.create_table(
        'student_learning_gaps',
        sa.Column('id', sa.BigInteger(), nullable=False),
        sa.Column('uuid', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('profile_uuid', sa.UUID(), nullable=False),
        sa.Column('criterion_name', sa.String(length=200), nullable=False),
        sa.Column('topic', sa.String(length=200), nullable=True),
        sa.Column('severity', sa.String(length=20), server_default=sa.text("'medium'"), nullable=False),
        sa.Column('evidence_count', sa.Integer(), server_default=sa.text('1'), nullable=False),
        sa.Column('avg_score', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.CheckConstraint(
            "severity IN ('low', 'medium', 'high')",
            name='chk_slg_severity',
        ),
        sa.ForeignKeyConstraint(
            ['profile_uuid'],
            ['public.student_learning_profiles.uuid'],
            onupdate='CASCADE',
            ondelete='CASCADE',
        ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('uuid'),
        schema='public',
    )
    op.create_index(
        'idx_slg_profile_uuid',
        'student_learning_gaps',
        ['profile_uuid'],
        unique=False,
        schema='public',
    )


def downgrade() -> None:
    """Remove tabelas de conhecimento do aluno e campos de divergencia."""
    # --- 3. Drop student_learning_gaps ---
    op.drop_index('idx_slg_profile_uuid', table_name='student_learning_gaps', schema='public')
    op.drop_table('student_learning_gaps', schema='public')

    # --- 2. Drop student_learning_profiles ---
    op.drop_index('idx_slp_student_uuid', table_name='student_learning_profiles', schema='public')
    op.drop_table('student_learning_profiles', schema='public')

    # --- 1. Drop divergence columns from student_answers ---
    op.drop_index('idx_student_answers_divergence', table_name='student_answers', schema='public')
    op.drop_column('student_answers', 'divergence_value', schema='public')
    op.drop_column('student_answers', 'divergence_detected', schema='public')

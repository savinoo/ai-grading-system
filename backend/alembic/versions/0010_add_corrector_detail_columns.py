"""add corrector detail columns to student_answers and criteria_scores

Revision ID: 0010_add_corrector_detail_columns
Revises: 0009_add_warning_status_back
Create Date: 2026-03-28 12:00:00.000000

"""

from alembic import op
import sqlalchemy as sa

revision = "0010_corrector_details"
down_revision = "0009_add_warning_status_back"
branch_labels = None
depends_on = None


def upgrade():
    """
    Adiciona colunas para armazenar notas individuais dos corretores (C1, C2, árbitro)
    e metadados de divergência na tabela student_answers.
    Adiciona coluna agent_id na tabela student_answer_criteria_scores.
    """

    # ── student_answers: notas individuais e metadados de divergência ─────
    op.add_column(
        "student_answers",
        sa.Column("c1_score", sa.Numeric(8, 2), nullable=True),
        schema="public",
    )
    op.add_column(
        "student_answers",
        sa.Column("c2_score", sa.Numeric(8, 2), nullable=True),
        schema="public",
    )
    op.add_column(
        "student_answers",
        sa.Column("arbiter_score", sa.Numeric(8, 2), nullable=True),
        schema="public",
    )
    op.add_column(
        "student_answers",
        sa.Column(
            "divergence_detected",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("FALSE"),
        ),
        schema="public",
    )
    op.add_column(
        "student_answers",
        sa.Column("divergence_value", sa.Numeric(8, 2), nullable=True),
        schema="public",
    )
    op.add_column(
        "student_answers",
        sa.Column("consensus_method", sa.String(30), nullable=True),
        schema="public",
    )

    # ── student_answer_criteria_scores: agent_id ─────────────────────────
    op.add_column(
        "student_answer_criteria_scores",
        sa.Column(
            "agent_id",
            sa.String(30),
            nullable=True,
            comment="corretor_1, corretor_2, corretor_3_arbiter, ou consensus",
        ),
        schema="public",
    )

    # Drop old unique constraint and create new one including agent_id
    op.drop_index(
        "uq_sacs_answer_criteria",
        table_name="student_answer_criteria_scores",
        schema="public",
    )
    op.create_index(
        "uq_sacs_answer_criteria_agent",
        "student_answer_criteria_scores",
        ["student_answer_uuid", "criteria_uuid", "agent_id"],
        unique=True,
        schema="public",
    )

    # Index on agent_id
    op.create_index(
        "idx_sacs_agent",
        "student_answer_criteria_scores",
        ["agent_id"],
        schema="public",
    )


def downgrade():
    """Remove colunas adicionadas."""

    # ── Revert student_answer_criteria_scores ─────────────────────────────
    op.drop_index(
        "idx_sacs_agent",
        table_name="student_answer_criteria_scores",
        schema="public",
    )
    op.drop_index(
        "uq_sacs_answer_criteria_agent",
        table_name="student_answer_criteria_scores",
        schema="public",
    )
    op.create_index(
        "uq_sacs_answer_criteria",
        "student_answer_criteria_scores",
        ["student_answer_uuid", "criteria_uuid"],
        unique=True,
        schema="public",
    )
    op.drop_column(
        "student_answer_criteria_scores", "agent_id", schema="public"
    )

    # ── Revert student_answers ────────────────────────────────────────────
    op.drop_column("student_answers", "consensus_method", schema="public")
    op.drop_column("student_answers", "divergence_value", schema="public")
    op.drop_column("student_answers", "divergence_detected", schema="public")
    op.drop_column("student_answers", "arbiter_score", schema="public")
    op.drop_column("student_answers", "c2_score", schema="public")
    op.drop_column("student_answers", "c1_score", schema="public")

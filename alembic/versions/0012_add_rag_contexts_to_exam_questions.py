"""add rag_contexts_json to exam_questions

Revision ID: 0012_add_rag_contexts
Revises: 0011_corrector_details
Branch_labels: None
Depends_on: None
"""

from alembic import op
import sqlalchemy as sa

revision = "0012_add_rag_contexts"
down_revision = "0011_corrector_details"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "exam_questions",
        sa.Column(
            "rag_contexts_json",
            sa.Text,
            nullable=True,
            comment="Contexto RAG recuperado para esta questão (JSON serializado)",
        ),
        schema="public",
    )


def downgrade():
    op.drop_column("exam_questions", "rag_contexts_json", schema="public")

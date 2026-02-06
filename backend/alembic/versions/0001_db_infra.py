"""db infra: extensions and functions

Revision ID: 1588dc59fe3a
Revises: 
Create Date: 2026-02-06 17:39:21.534339

"""
from alembic import op

revision = "0001_db_infra"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto;")

    op.execute("""
    CREATE OR REPLACE FUNCTION public.set_updated_at()
    RETURNS TRIGGER AS $$
    BEGIN
      NEW.updated_at = NOW();
      RETURN NEW;
    END;
    $$ LANGUAGE plpgsql;
    """)


def downgrade() -> None:
    # normalmente você não remove extensão em downgrade (mas pode)
    op.execute("DROP FUNCTION IF EXISTS public.set_updated_at();")

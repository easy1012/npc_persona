from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB
from pgvector.sqlalchemy import Vector


revision = "0002_full_knowledge_pgvector"
down_revision = "0001_runtime_state"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.create_table(
        "full_knowledge_documents",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("source_id", sa.String(128), nullable=False, unique=True),
        sa.Column("source_type", sa.String(64), nullable=False),
        sa.Column("title", sa.String(300), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("document_metadata", JSONB(), nullable=True),
        sa.Column("embedding", Vector(768), nullable=True),
    )
    op.create_index("ix_full_knowledge_source_type", "full_knowledge_documents", ["source_type"])


def downgrade() -> None:
    op.drop_table("full_knowledge_documents")

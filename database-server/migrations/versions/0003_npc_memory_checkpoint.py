from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0003_npc_memory_checkpoint"
down_revision = "0002_full_knowledge_pgvector"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "npc_memory_summaries",
        sa.Column(
            "summarized_through_ordinal",
            sa.Integer(),
            nullable=False,
            server_default="-1",
        ),
    )
    op.add_column(
        "npc_memory_summaries",
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )


def downgrade() -> None:
    op.drop_column("npc_memory_summaries", "updated_at")
    op.drop_column("npc_memory_summaries", "summarized_through_ordinal")

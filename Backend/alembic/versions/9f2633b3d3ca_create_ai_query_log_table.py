from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '9f2633b3d3ca'
down_revision: Union[str, Sequence[str], None] = '3dd436d18478'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "ai_query_log",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("tool_name", sa.String(), nullable=False),
        sa.Column("params_json", sa.JSON(), nullable=True),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("message", sa.String(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_ai_query_log_user_id", "ai_query_log", ["user_id"])
    op.create_index("ix_ai_query_log_tool_name", "ai_query_log", ["tool_name"])


def downgrade() -> None:
    op.drop_index("ix_ai_query_log_tool_name", table_name="ai_query_log")
    op.drop_index("ix_ai_query_log_user_id", table_name="ai_query_log")
    op.drop_table("ai_query_log")

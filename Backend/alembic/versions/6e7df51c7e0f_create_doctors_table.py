"""create doctors table

Revision ID: 6e7df51c7e0f
Revises: 9632704049f8
Create Date: 2026-07-21 15:55:31.417367

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6e7df51c7e0f'
down_revision: Union[str, Sequence[str], None] = '9632704049f8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "doctors",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("full_name", sa.String(), nullable=False),
        sa.Column("specialization", sa.String(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_unique_constraint("uq_doctors_user_id", "doctors", ["user_id"])
    op.create_index("ix_doctors_user_id", "doctors", ["user_id"])
    op.create_index("ix_doctors_specialization", "doctors", ["specialization"])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("ix_doctors_specialization", table_name="doctors")
    op.drop_index("ix_doctors_user_id", table_name="doctors")
    op.drop_constraint("uq_doctors_user_id", "doctors", type_="unique")
    op.drop_table("doctors")

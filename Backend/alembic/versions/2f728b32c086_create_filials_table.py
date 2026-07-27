"""create filials table

Revision ID: 2f728b32c086
Revises: 761c01bf96cb
Create Date: 2026-07-21 15:42:50.934687

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '2f728b32c086'
down_revision: Union[str, Sequence[str], None] = '761c01bf96cb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "filials",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("city", sa.String(), nullable=False),
        sa.Column("address", sa.String(), nullable=False),
        sa.Column("phone", sa.String(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("filials")

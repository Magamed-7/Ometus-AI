"""add email verification

Revision ID: 761c01bf96cb
Revises: ab4cb8201fca
Create Date: 2026-07-21 15:05:28.701707

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '761c01bf96cb'
down_revision: Union[str, Sequence[str], None] = 'ab4cb8201fca'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "users",
        sa.Column("is_verified", sa.Boolean(), nullable=False, server_default=sa.false()),
    )

    op.create_table(
        "email_verification_codes",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("code", sa.String(length=6), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("email_verification_codes")
    op.drop_column("users", "is_verified")

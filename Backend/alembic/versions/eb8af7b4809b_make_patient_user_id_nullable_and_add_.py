"""make patient user id nullable and add guardian

Revision ID: eb8af7b4809b
Revises: d5b39b41ec74
Create Date: 2026-07-24 11:31:09.274637

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'eb8af7b4809b'
down_revision: Union[str, Sequence[str], None] = 'd5b39b41ec74'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.alter_column("patients", "user_id", existing_type=sa.Integer(), nullable=True)
    op.add_column(
        "patients",
        sa.Column("guardian_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
    )
    op.create_index("ix_patients_guardian_user_id", "patients", ["guardian_user_id"])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("ix_patients_guardian_user_id", table_name="patients")
    op.drop_column("patients", "guardian_user_id")
    op.alter_column("patients", "user_id", existing_type=sa.Integer(), nullable=False)

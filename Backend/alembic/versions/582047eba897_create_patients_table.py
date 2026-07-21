"""create patients table

Revision ID: 582047eba897
Revises: ef7452ba0d30
Create Date: 2026-07-21 20:10:00.213174

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '582047eba897'
down_revision: Union[str, Sequence[str], None] = 'ef7452ba0d30'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "patients",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("full_name", sa.String(), nullable=True),
        sa.Column("date_of_birth", sa.Date(), nullable=True),
        sa.Column("phone", sa.String(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_unique_constraint("uq_patients_user_id", "patients", ["user_id"])
    op.create_index("ix_patients_user_id", "patients", ["user_id"])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("ix_patients_user_id", table_name="patients")
    op.drop_constraint("uq_patients_user_id", "patients", type_="unique")
    op.drop_table("patients")

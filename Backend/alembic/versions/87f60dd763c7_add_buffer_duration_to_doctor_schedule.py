"""add buffer duration to doctor schedule

Revision ID: 87f60dd763c7
Revises: 9f2633b3d3ca
Create Date: 2026-07-23 19:11:31.972937

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '87f60dd763c7'
down_revision: Union[str, Sequence[str], None] = '9f2633b3d3ca'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "doctor_schedule",
        sa.Column("buffer_duration", sa.Integer(), nullable=False, server_default="0"),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("doctor_schedule", "buffer_duration")

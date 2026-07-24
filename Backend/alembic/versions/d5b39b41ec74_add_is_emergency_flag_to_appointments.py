"""add is emergency flag to appointments

Revision ID: d5b39b41ec74
Revises: e3a2b0c1ed5e
Create Date: 2026-07-24 11:24:59.163268

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd5b39b41ec74'
down_revision: Union[str, Sequence[str], None] = 'e3a2b0c1ed5e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "appointments",
        sa.Column(
            "is_emergency", sa.Boolean(), nullable=False, server_default=sa.text("false")
        ),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("appointments", "is_emergency")

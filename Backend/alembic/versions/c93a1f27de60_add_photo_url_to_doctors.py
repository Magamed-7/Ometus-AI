"""add photo url to doctors

Revision ID: c93a1f27de60
Revises: b71c05e8d3af
Create Date: 2026-07-27 13:05:18.774219

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = 'c93a1f27de60'
down_revision: Union[str, Sequence[str], None] = 'b71c05e8d3af'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('doctors', sa.Column('photo_url', sa.String(length=255), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('doctors', 'photo_url')

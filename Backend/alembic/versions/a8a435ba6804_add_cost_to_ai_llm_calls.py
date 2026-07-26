"""add cost to ai llm calls

Revision ID: a8a435ba6804
Revises: 56a2e31a800e
Create Date: 2026-07-27 01:24:13.880084

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a8a435ba6804'
down_revision: Union[str, Sequence[str], None] = '56a2e31a800e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'ai_llm_calls',
        sa.Column('cost_usd', sa.Numeric(12, 6), nullable=False, server_default='0'),
    )


def downgrade() -> None:
    op.drop_column('ai_llm_calls', 'cost_usd')

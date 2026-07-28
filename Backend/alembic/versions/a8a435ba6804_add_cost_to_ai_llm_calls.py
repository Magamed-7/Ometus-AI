from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


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

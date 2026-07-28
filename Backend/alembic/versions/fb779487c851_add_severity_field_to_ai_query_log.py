from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'fb779487c851'
down_revision: Union[str, Sequence[str], None] = 'bc3918ae54b2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('ai_query_log', sa.Column('severity', sa.Integer(), nullable=False, server_default='0'))
    op.create_index('ix_ai_query_log_severity', 'ai_query_log', ['severity'])


def downgrade() -> None:
    op.drop_index('ix_ai_query_log_severity', 'ai_query_log')
    op.drop_column('ai_query_log', 'severity')

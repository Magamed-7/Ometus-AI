from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = 'b71c05e8d3af'
down_revision: Union[str, Sequence[str], None] = '904d484e96d9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('ai_messages', sa.Column('action', sa.String(length=32), nullable=True))
    op.add_column('ai_messages', sa.Column('payload', sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column('ai_messages', 'payload')
    op.drop_column('ai_messages', 'action')

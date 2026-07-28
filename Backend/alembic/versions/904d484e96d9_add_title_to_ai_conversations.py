from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = '904d484e96d9'
down_revision: Union[str, Sequence[str], None] = '8dfea1e06e05'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('ai_conversations', sa.Column('title', sa.String(length=120), nullable=True))


def downgrade() -> None:
    op.drop_column('ai_conversations', 'title')

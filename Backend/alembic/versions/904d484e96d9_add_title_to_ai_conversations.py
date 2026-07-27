"""add title to ai conversations

Revision ID: 904d484e96d9
Revises: 8dfea1e06e05
Create Date: 2026-07-27 08:13:11.091889

Заголовок диалога, чтобы список чатов читался как в обычном ассистенте.
Колонка nullable: у диалогов, заведённых до этой миграции, заголовка нет,
и придумывать его за пациента нечем — список покажет «Новый чат».
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = '904d484e96d9'
down_revision: Union[str, Sequence[str], None] = '8dfea1e06e05'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('ai_conversations', sa.Column('title', sa.String(length=120), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('ai_conversations', 'title')

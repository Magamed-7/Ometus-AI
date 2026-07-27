"""add action and payload to ai messages

Revision ID: b71c05e8d3af
Revises: 904d484e96d9
Create Date: 2026-07-27 12:20:44.512038

Ответ ассистента хранился одним текстом, поэтому старая переписка открывалась
голой строкой: карточки врачей, сетка слотов и карточка записи собирались из
живого ответа и никуда не сохранялись. Теперь рядом с текстом лежит `action`
и `payload` — ровно то, что нужно для отрисовки, без промптов и метрик.
Обе колонки nullable: у сообщений, написанных до этой миграции, данных для
карточек физически нет, и выдумывать их под старый текст нельзя.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = 'b71c05e8d3af'
down_revision: Union[str, Sequence[str], None] = '904d484e96d9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('ai_messages', sa.Column('action', sa.String(length=32), nullable=True))
    op.add_column('ai_messages', sa.Column('payload', sa.JSON(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('ai_messages', 'payload')
    op.drop_column('ai_messages', 'action')

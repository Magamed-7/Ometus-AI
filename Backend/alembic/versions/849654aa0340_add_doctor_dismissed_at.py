"""add doctor dismissed_at

Revision ID: 849654aa0340
Revises: fb779487c851
Create Date: 2026-07-27 00:23:03.435112

Автогенерация принесла сюда же удаление ai_conversations/ai_messages и перетряску
уникальных индексов users/patients/doctors — это чужой дрейф схемы, к увольнению врача
отношения не имеющий. Оставлено только то, ради чего миграция создавалась.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = '849654aa0340'
down_revision: Union[str, Sequence[str], None] = 'fb779487c851'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('doctors', sa.Column('dismissed_at', sa.Date(), nullable=True))
    op.create_index(op.f('ix_doctors_dismissed_at'), 'doctors', ['dismissed_at'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_doctors_dismissed_at'), table_name='doctors')
    op.drop_column('doctors', 'dismissed_at')

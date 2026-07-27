"""add conversation and message tables

Revision ID: bc3918ae54b2
Revises: d22995c74ac9
Create Date: 2026-07-26 22:05:08.511722

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'bc3918ae54b2'
down_revision: Union[str, Sequence[str], None] = 'd22995c74ac9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'ai_conversations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('patient_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['patient_id'], ['patients.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_ai_conversations_patient_id', 'ai_conversations', ['patient_id'])
    op.create_table(
        'ai_messages',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('conversation_id', sa.Integer(), nullable=False),
        sa.Column('role', sa.String(), nullable=False),
        sa.Column('content', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['conversation_id'], ['ai_conversations.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_ai_messages_conversation_id', 'ai_messages', ['conversation_id'])


def downgrade() -> None:
    op.drop_index('ix_ai_messages_conversation_id', 'ai_messages')
    op.drop_table('ai_messages')
    op.drop_index('ix_ai_conversations_patient_id', 'ai_conversations')
    op.drop_table('ai_conversations')

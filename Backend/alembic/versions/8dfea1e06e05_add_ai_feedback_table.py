"""add ai feedback table

Revision ID: 8dfea1e06e05
Revises: 295efe6d1450
Create Date: 2026-07-27 01:48:55.939488

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8dfea1e06e05'
down_revision: Union[str, Sequence[str], None] = '295efe6d1450'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'ai_feedback',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('message_id', sa.Integer(), nullable=False),
        sa.Column('patient_id', sa.Integer(), nullable=False),
        sa.Column('feedback', sa.String(), nullable=False),
        sa.Column('reason', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['message_id'], ['ai_messages.id'], ),
        sa.ForeignKeyConstraint(['patient_id'], ['patients.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('message_id', 'patient_id', name='uq_feedback_message')
    )
    op.create_index('ix_ai_feedback_message_id', 'ai_feedback', ['message_id'])
    op.create_index('ix_ai_feedback_patient_id', 'ai_feedback', ['patient_id'])
    op.create_index('ix_ai_feedback_feedback', 'ai_feedback', ['feedback'])


def downgrade() -> None:
    op.drop_index('ix_ai_feedback_feedback', 'ai_feedback')
    op.drop_index('ix_ai_feedback_patient_id', 'ai_feedback')
    op.drop_index('ix_ai_feedback_message_id', 'ai_feedback')
    op.drop_table('ai_feedback')

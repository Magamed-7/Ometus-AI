from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'f54ffeb13811'
down_revision: Union[str, Sequence[str], None] = '4302c3d539de'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'ai_tasks',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('patient_id', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('request_json', sa.JSON(), nullable=True),
        sa.Column('result_json', sa.JSON(), nullable=True),
        sa.Column('error', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('finished_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['patient_id'], ['patients.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_ai_tasks_patient_id', 'ai_tasks', ['patient_id'])
    op.create_index('ix_ai_tasks_status', 'ai_tasks', ['status'])


def downgrade() -> None:
    op.drop_index('ix_ai_tasks_status', 'ai_tasks')
    op.drop_index('ix_ai_tasks_patient_id', 'ai_tasks')
    op.drop_table('ai_tasks')

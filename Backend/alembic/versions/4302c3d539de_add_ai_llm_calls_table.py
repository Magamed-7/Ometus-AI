from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '4302c3d539de'
down_revision: Union[str, Sequence[str], None] = '849654aa0340'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'ai_llm_calls',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('provider', sa.String(), nullable=False),
        sa.Column('model', sa.String(), nullable=False),
        sa.Column('success', sa.Boolean(), nullable=False),
        sa.Column('duration_ms', sa.Integer(), nullable=False),
        sa.Column('prompt_tokens', sa.Integer(), nullable=True),
        sa.Column('completion_tokens', sa.Integer(), nullable=True),
        sa.Column('error', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_ai_llm_calls_user_id', 'ai_llm_calls', ['user_id'])
    op.create_index('ix_ai_llm_calls_provider', 'ai_llm_calls', ['provider'])
    op.create_index('ix_ai_llm_calls_model', 'ai_llm_calls', ['model'])
    op.create_index('ix_ai_llm_calls_success', 'ai_llm_calls', ['success'])
    op.create_index('ix_ai_llm_calls_created_at', 'ai_llm_calls', ['created_at'])


def downgrade() -> None:
    op.drop_index('ix_ai_llm_calls_created_at', 'ai_llm_calls')
    op.drop_index('ix_ai_llm_calls_success', 'ai_llm_calls')
    op.drop_index('ix_ai_llm_calls_model', 'ai_llm_calls')
    op.drop_index('ix_ai_llm_calls_provider', 'ai_llm_calls')
    op.drop_index('ix_ai_llm_calls_user_id', 'ai_llm_calls')
    op.drop_table('ai_llm_calls')

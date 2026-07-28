from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '56a2e31a800e'
down_revision: Union[str, Sequence[str], None] = 'f54ffeb13811'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'admin_action_log',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('admin_user_id', sa.Integer(), nullable=False),
        sa.Column('action', sa.String(), nullable=False),
        sa.Column('entity', sa.String(), nullable=False),
        sa.Column('entity_id', sa.Integer(), nullable=True),
        sa.Column('payload_json', sa.JSON(), nullable=True),
        sa.Column(
            'created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False
        ),
        sa.ForeignKeyConstraint(['admin_user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        op.f('ix_admin_action_log_admin_user_id'), 'admin_action_log', ['admin_user_id']
    )
    op.create_index(op.f('ix_admin_action_log_action'), 'admin_action_log', ['action'])
    op.create_index(op.f('ix_admin_action_log_entity'), 'admin_action_log', ['entity'])


def downgrade() -> None:
    op.drop_index(op.f('ix_admin_action_log_entity'), table_name='admin_action_log')
    op.drop_index(op.f('ix_admin_action_log_action'), table_name='admin_action_log')
    op.drop_index(op.f('ix_admin_action_log_admin_user_id'), table_name='admin_action_log')
    op.drop_table('admin_action_log')

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'd22995c74ac9'
down_revision: Union[str, Sequence[str], None] = 'eb8af7b4809b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('filials', sa.Column('legal_name', sa.String(), nullable=True))
    op.add_column('filials', sa.Column('inn', sa.String(), nullable=True))
    op.add_column('filials', sa.Column('license_number', sa.String(), nullable=True))
    op.add_column('filials', sa.Column('clinic_type', sa.String(), nullable=True))
    op.add_column('filials', sa.Column('opening_hours', sa.String(), nullable=True))
    op.create_index('ix_filials_inn', 'filials', ['inn'], unique=True)
    op.create_index('ix_filials_legal_name', 'filials', ['legal_name'])


def downgrade() -> None:
    op.drop_index('ix_filials_legal_name', 'filials')
    op.drop_index('ix_filials_inn', 'filials')
    op.drop_column('filials', 'opening_hours')
    op.drop_column('filials', 'clinic_type')
    op.drop_column('filials', 'license_number')
    op.drop_column('filials', 'inn')
    op.drop_column('filials', 'legal_name')

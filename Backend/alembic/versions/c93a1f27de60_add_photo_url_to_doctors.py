from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = 'c93a1f27de60'
down_revision: Union[str, Sequence[str], None] = 'b71c05e8d3af'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('doctors', sa.Column('photo_url', sa.String(length=255), nullable=True))


def downgrade() -> None:
    op.drop_column('doctors', 'photo_url')

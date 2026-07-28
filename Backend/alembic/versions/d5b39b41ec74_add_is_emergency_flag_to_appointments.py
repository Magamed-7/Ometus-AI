from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'd5b39b41ec74'
down_revision: Union[str, Sequence[str], None] = 'e3a2b0c1ed5e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "appointments",
        sa.Column(
            "is_emergency", sa.Boolean(), nullable=False, server_default=sa.text("false")
        ),
    )


def downgrade() -> None:
    op.drop_column("appointments", "is_emergency")

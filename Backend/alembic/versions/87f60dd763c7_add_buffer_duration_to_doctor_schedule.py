from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '87f60dd763c7'
down_revision: Union[str, Sequence[str], None] = '9f2633b3d3ca'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "doctor_schedule",
        sa.Column("buffer_duration", sa.Integer(), nullable=False, server_default="0"),
    )


def downgrade() -> None:
    op.drop_column("doctor_schedule", "buffer_duration")

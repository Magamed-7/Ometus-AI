from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '9632704049f8'
down_revision: Union[str, Sequence[str], None] = '2f728b32c086'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "departments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("filial_id", sa.Integer(), sa.ForeignKey("filials.id"), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_departments_filial_id", "departments", ["filial_id"])


def downgrade() -> None:
    op.drop_index("ix_departments_filial_id", table_name="departments")
    op.drop_table("departments")

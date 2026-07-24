"""create doctor specializations table

Revision ID: e3a2b0c1ed5e
Revises: 66f55e221ed8
Create Date: 2026-07-24 11:18:58.437740

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e3a2b0c1ed5e'
down_revision: Union[str, Sequence[str], None] = '66f55e221ed8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "doctor_specializations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("doctor_id", sa.Integer(), sa.ForeignKey("doctors.id"), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.UniqueConstraint("doctor_id", "name", name="uq_doctor_specialization"),
    )
    op.create_index(
        "ix_doctor_specializations_doctor_id", "doctor_specializations", ["doctor_id"]
    )
    op.create_index("ix_doctor_specializations_name", "doctor_specializations", ["name"])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("ix_doctor_specializations_name", table_name="doctor_specializations")
    op.drop_index("ix_doctor_specializations_doctor_id", table_name="doctor_specializations")
    op.drop_table("doctor_specializations")

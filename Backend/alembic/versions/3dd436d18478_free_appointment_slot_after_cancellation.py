"""free appointment slot after cancellation

Revision ID: 3dd436d18478
Revises: 70540dec953b
Create Date: 2026-07-22 10:26:03.774251

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '3dd436d18478'
down_revision: Union[str, Sequence[str], None] = '70540dec953b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.drop_constraint("uq_appointment_slot", "appointments", type_="unique")
    op.create_index(
        "uq_appointment_slot",
        "appointments",
        ["doctor_id", "date", "time"],
        unique=True,
        postgresql_where=sa.text("status <> 'cancelled'"),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("uq_appointment_slot", table_name="appointments")
    op.create_unique_constraint(
        "uq_appointment_slot", "appointments", ["doctor_id", "date", "time"]
    )

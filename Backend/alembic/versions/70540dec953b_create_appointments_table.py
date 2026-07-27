"""create appointments table

Revision ID: 70540dec953b
Revises: 2bf94a23e690
Create Date: 2026-07-22 10:12:44.318620

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '70540dec953b'
down_revision: Union[str, Sequence[str], None] = '2bf94a23e690'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "appointments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("patient_id", sa.Integer(), sa.ForeignKey("patients.id"), nullable=False),
        sa.Column("doctor_id", sa.Integer(), sa.ForeignKey("doctors.id"), nullable=False),
        sa.Column(
            "department_id", sa.Integer(), sa.ForeignKey("departments.id"), nullable=False
        ),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("time", sa.Time(), nullable=False),
        sa.Column("status", sa.String(), nullable=False, server_default="booked"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint("doctor_id", "date", "time", name="uq_appointment_slot"),
    )
    op.create_index("ix_appointments_patient_id", "appointments", ["patient_id"])
    op.create_index("ix_appointments_doctor_id", "appointments", ["doctor_id"])
    op.create_index("ix_appointments_department_id", "appointments", ["department_id"])
    op.create_index("ix_appointments_date", "appointments", ["date"])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("ix_appointments_date", table_name="appointments")
    op.drop_index("ix_appointments_department_id", table_name="appointments")
    op.drop_index("ix_appointments_doctor_id", table_name="appointments")
    op.drop_index("ix_appointments_patient_id", table_name="appointments")
    op.drop_table("appointments")

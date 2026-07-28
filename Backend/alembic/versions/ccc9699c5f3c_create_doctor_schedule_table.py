from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'ccc9699c5f3c'
down_revision: Union[str, Sequence[str], None] = '582047eba897'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "doctor_schedule",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("doctor_id", sa.Integer(), sa.ForeignKey("doctors.id"), nullable=False),
        sa.Column(
            "department_id", sa.Integer(), sa.ForeignKey("departments.id"), nullable=False
        ),
        sa.Column("weekday", sa.Integer(), nullable=False),
        sa.Column("start_time", sa.Time(), nullable=False),
        sa.Column("end_time", sa.Time(), nullable=False),
        sa.Column("slot_duration", sa.Integer(), nullable=False, server_default="20"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint(
            "doctor_id", "department_id", "weekday", name="uq_doctor_schedule_day"
        ),
    )
    op.create_index("ix_doctor_schedule_doctor_id", "doctor_schedule", ["doctor_id"])
    op.create_index("ix_doctor_schedule_department_id", "doctor_schedule", ["department_id"])


def downgrade() -> None:
    op.drop_index("ix_doctor_schedule_department_id", table_name="doctor_schedule")
    op.drop_index("ix_doctor_schedule_doctor_id", table_name="doctor_schedule")
    op.drop_table("doctor_schedule")

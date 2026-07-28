from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '66f55e221ed8'
down_revision: Union[str, Sequence[str], None] = '87f60dd763c7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "doctor_date_schedule",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("doctor_id", sa.Integer(), sa.ForeignKey("doctors.id"), nullable=False),
        sa.Column(
            "department_id", sa.Integer(), sa.ForeignKey("departments.id"), nullable=False
        ),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("start_time", sa.Time(), nullable=False),
        sa.Column("end_time", sa.Time(), nullable=False),
        sa.Column("slot_duration", sa.Integer(), nullable=False, server_default="20"),
        sa.Column("buffer_duration", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint(
            "doctor_id", "department_id", "date", name="uq_doctor_date_schedule"
        ),
    )
    op.create_index("ix_doctor_date_schedule_doctor_id", "doctor_date_schedule", ["doctor_id"])
    op.create_index(
        "ix_doctor_date_schedule_department_id", "doctor_date_schedule", ["department_id"]
    )
    op.create_index("ix_doctor_date_schedule_date", "doctor_date_schedule", ["date"])


def downgrade() -> None:
    op.drop_index("ix_doctor_date_schedule_date", table_name="doctor_date_schedule")
    op.drop_index("ix_doctor_date_schedule_department_id", table_name="doctor_date_schedule")
    op.drop_index("ix_doctor_date_schedule_doctor_id", table_name="doctor_date_schedule")
    op.drop_table("doctor_date_schedule")

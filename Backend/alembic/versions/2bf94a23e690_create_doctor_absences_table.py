from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '2bf94a23e690'
down_revision: Union[str, Sequence[str], None] = 'ccc9699c5f3c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "doctor_absences",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("doctor_id", sa.Integer(), sa.ForeignKey("doctors.id"), nullable=False),
        sa.Column("date_from", sa.Date(), nullable=False),
        sa.Column("date_to", sa.Date(), nullable=False),
        sa.Column("reason", sa.String(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_doctor_absences_doctor_id", "doctor_absences", ["doctor_id"])


def downgrade() -> None:
    op.drop_index("ix_doctor_absences_doctor_id", table_name="doctor_absences")
    op.drop_table("doctor_absences")

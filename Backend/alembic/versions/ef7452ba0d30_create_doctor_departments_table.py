"""create doctor departments table

Revision ID: ef7452ba0d30
Revises: 6e7df51c7e0f
Create Date: 2026-07-21 15:57:13.194430

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ef7452ba0d30'
down_revision: Union[str, Sequence[str], None] = '6e7df51c7e0f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "doctor_departments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("doctor_id", sa.Integer(), sa.ForeignKey("doctors.id"), nullable=False),
        sa.Column(
            "department_id", sa.Integer(), sa.ForeignKey("departments.id"), nullable=False
        ),
        sa.UniqueConstraint("doctor_id", "department_id", name="uq_doctor_department"),
    )
    op.create_index("ix_doctor_departments_doctor_id", "doctor_departments", ["doctor_id"])
    op.create_index(
        "ix_doctor_departments_department_id", "doctor_departments", ["department_id"]
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("ix_doctor_departments_department_id", table_name="doctor_departments")
    op.drop_index("ix_doctor_departments_doctor_id", table_name="doctor_departments")
    op.drop_table("doctor_departments")

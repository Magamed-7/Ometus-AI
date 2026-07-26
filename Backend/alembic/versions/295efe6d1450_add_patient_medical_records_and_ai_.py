"""add patient medical records and ai consent

Revision ID: 295efe6d1450
Revises: a8a435ba6804
Create Date: 2026-07-27 01:41:57.418109

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '295efe6d1450'
down_revision: Union[str, Sequence[str], None] = 'a8a435ba6804'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'patients',
        sa.Column('ai_consent', sa.Boolean(), nullable=False, server_default=sa.text('false')),
    )
    op.create_table(
        'patient_medical_records',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('patient_id', sa.Integer(), nullable=False),
        sa.Column('kind', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('note', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['patient_id'], ['patients.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_patient_medical_records_patient_id', 'patient_medical_records', ['patient_id'])
    op.create_index('ix_patient_medical_records_kind', 'patient_medical_records', ['kind'])


def downgrade() -> None:
    op.drop_index('ix_patient_medical_records_kind', 'patient_medical_records')
    op.drop_index('ix_patient_medical_records_patient_id', 'patient_medical_records')
    op.drop_table('patient_medical_records')
    op.drop_column('patients', 'ai_consent')

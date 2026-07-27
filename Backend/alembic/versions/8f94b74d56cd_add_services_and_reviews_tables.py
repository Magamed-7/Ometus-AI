"""add services and reviews tables

Revision ID: 8f94b74d56cd
Revises: c93a1f27de60
Create Date: 2026-07-27 15:10:32.084246

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8f94b74d56cd'
down_revision: Union[str, Sequence[str], None] = 'c93a1f27de60'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'services',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('category', sa.String(length=32), nullable=False),
        sa.Column('price', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('currency', sa.String(length=3), server_default=sa.text("'TJS'"), nullable=False),
        sa.Column('duration_minutes', sa.Integer(), nullable=True),
        sa.Column('department_id', sa.Integer(), nullable=True),
        sa.Column('filial_id', sa.Integer(), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default=sa.text('true'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['department_id'], ['departments.id'], ),
        sa.ForeignKeyConstraint(['filial_id'], ['filials.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_services_name'), 'services', ['name'])
    op.create_index(op.f('ix_services_category'), 'services', ['category'])
    op.create_index(op.f('ix_services_department_id'), 'services', ['department_id'])
    op.create_index(op.f('ix_services_filial_id'), 'services', ['filial_id'])

    op.create_table(
        'reviews',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('patient_id', sa.Integer(), nullable=False),
        sa.Column('doctor_id', sa.Integer(), nullable=True),
        sa.Column('filial_id', sa.Integer(), nullable=True),
        sa.Column('appointment_id', sa.Integer(), nullable=False),
        sa.Column('rating', sa.Integer(), nullable=False),
        sa.Column('text', sa.Text(), nullable=True),
        sa.Column('is_published', sa.Boolean(), server_default=sa.text('true'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['patient_id'], ['patients.id'], ),
        sa.ForeignKeyConstraint(['doctor_id'], ['doctors.id'], ),
        sa.ForeignKeyConstraint(['filial_id'], ['filials.id'], ),
        sa.ForeignKeyConstraint(['appointment_id'], ['appointments.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('appointment_id'),
    )
    op.create_index(op.f('ix_reviews_patient_id'), 'reviews', ['patient_id'])
    op.create_index(op.f('ix_reviews_doctor_id'), 'reviews', ['doctor_id'])
    op.create_index(op.f('ix_reviews_filial_id'), 'reviews', ['filial_id'])
    op.create_index(op.f('ix_reviews_rating'), 'reviews', ['rating'])
    op.create_index(op.f('ix_reviews_is_published'), 'reviews', ['is_published'])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_reviews_is_published'), table_name='reviews')
    op.drop_index(op.f('ix_reviews_rating'), table_name='reviews')
    op.drop_index(op.f('ix_reviews_filial_id'), table_name='reviews')
    op.drop_index(op.f('ix_reviews_doctor_id'), table_name='reviews')
    op.drop_index(op.f('ix_reviews_patient_id'), table_name='reviews')
    op.drop_table('reviews')

    op.drop_index(op.f('ix_services_filial_id'), table_name='services')
    op.drop_index(op.f('ix_services_department_id'), table_name='services')
    op.drop_index(op.f('ix_services_category'), table_name='services')
    op.drop_index(op.f('ix_services_name'), table_name='services')
    op.drop_table('services')

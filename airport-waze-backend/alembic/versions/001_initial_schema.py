"""Initial schema with users and wait_time_reports tables

Revision ID: 001
Revises:
Create Date: 2026-01-11 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create initial database schema."""
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('hashed_password', sa.String(), nullable=False),
        sa.Column('full_name', sa.String(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('is_superuser', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('has_tsa_precheck', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('has_global_entry', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('default_mobility_factor', sa.String(), nullable=False, server_default='1.0'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('last_login', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)

    # Create wait_time_reports table
    op.create_table(
        'wait_time_reports',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('airport_code', sa.String(length=3), nullable=False),
        sa.Column('checkpoint_id', sa.String(length=50), nullable=False),
        sa.Column('reported_wait_minutes', sa.Integer(), nullable=False),
        sa.Column('reporter_id', sa.String(length=100), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('user_lat', sa.Float(), nullable=True),
        sa.Column('user_lng', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_wait_time_reports_id'), 'wait_time_reports', ['id'], unique=False)
    op.create_index(op.f('ix_wait_time_reports_airport_code'), 'wait_time_reports', ['airport_code'], unique=False)
    op.create_index(op.f('ix_wait_time_reports_checkpoint_id'), 'wait_time_reports', ['checkpoint_id'], unique=False)
    op.create_index(op.f('ix_wait_time_reports_created_at'), 'wait_time_reports', ['created_at'], unique=False)

    # Create composite index for common queries
    op.create_index(
        'idx_airport_checkpoint_created',
        'wait_time_reports',
        ['airport_code', 'checkpoint_id', 'created_at'],
        unique=False
    )


def downgrade() -> None:
    """Drop all tables."""
    # Drop wait_time_reports table and its indexes
    op.drop_index('idx_airport_checkpoint_created', table_name='wait_time_reports')
    op.drop_index(op.f('ix_wait_time_reports_created_at'), table_name='wait_time_reports')
    op.drop_index(op.f('ix_wait_time_reports_checkpoint_id'), table_name='wait_time_reports')
    op.drop_index(op.f('ix_wait_time_reports_airport_code'), table_name='wait_time_reports')
    op.drop_index(op.f('ix_wait_time_reports_id'), table_name='wait_time_reports')
    op.drop_table('wait_time_reports')

    # Drop users table and its indexes
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_index(op.f('ix_users_id'), table_name='users')
    op.drop_table('users')

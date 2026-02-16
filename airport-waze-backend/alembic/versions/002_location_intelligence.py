"""Add location intelligence tables

Revision ID: 002_location_intelligence
Revises: 001_initial_schema
Create Date: 2026-01-11

This migration adds tables for intelligent location tracking:
- location_traces: User GPS breadcrumbs for movement analysis
- discovered_checkpoints: Auto-discovered checkpoints via ML clustering
- airline_checkpoint_mappings: Airline-specific check-in counter locations
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


# revision identifiers, used by Alembic.
revision = '002_location_intelligence'
down_revision = '001_initial_schema'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create location_traces table
    op.create_table(
        'location_traces',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('session_id', sa.String(100), nullable=False, index=True),
        sa.Column('airport_code', sa.String(3), nullable=False, index=True),
        sa.Column('airline', sa.String(50), nullable=True),
        sa.Column('flight_number', sa.String(20), nullable=True),
        sa.Column('terminal', sa.String(50), nullable=True),
        sa.Column('lat', sa.Float(), nullable=False),
        sa.Column('lng', sa.Float(), nullable=False),
        sa.Column('accuracy', sa.Float(), nullable=True),
        sa.Column('speed', sa.Float(), nullable=True),
        sa.Column('heading', sa.Float(), nullable=True),
        sa.Column('is_stationary', sa.Boolean(), default=False),
        sa.Column('activity_type', sa.String(50), nullable=True),
        sa.Column('detected_checkpoint_id', sa.String(50), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=False, index=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('metadata', JSONB, nullable=True),
    )

    # Create composite indexes for location_traces
    op.create_index(
        'idx_airport_airline_timestamp',
        'location_traces',
        ['airport_code', 'airline', 'timestamp']
    )
    op.create_index(
        'idx_session_timestamp',
        'location_traces',
        ['session_id', 'timestamp']
    )
    op.create_index(
        'idx_location_stationary',
        'location_traces',
        ['airport_code', 'is_stationary', 'timestamp']
    )

    # Create discovered_checkpoints table
    op.create_table(
        'discovered_checkpoints',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('airport_code', sa.String(3), nullable=False, index=True),
        sa.Column('terminal', sa.String(50), nullable=True),
        sa.Column('center_lat', sa.Float(), nullable=False),
        sa.Column('center_lng', sa.Float(), nullable=False),
        sa.Column('radius_meters', sa.Float(), nullable=False),
        sa.Column('checkpoint_type', sa.String(50), nullable=False),
        sa.Column('airline', sa.String(50), nullable=True),
        sa.Column('confidence_score', sa.Float(), default=0.0),
        sa.Column('sample_size', sa.Integer(), default=0),
        sa.Column('avg_dwell_time_seconds', sa.Integer(), nullable=True),
        sa.Column('first_detected', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('last_updated', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.Column('cluster_data', JSONB, nullable=True),
        sa.Column('is_verified', sa.Boolean(), default=False),
        sa.Column('is_active', sa.Boolean(), default=True),
    )

    # Create indexes for discovered_checkpoints
    op.create_index(
        'idx_airport_airline',
        'discovered_checkpoints',
        ['airport_code', 'airline']
    )
    op.create_index(
        'idx_checkpoint_type',
        'discovered_checkpoints',
        ['checkpoint_type', 'confidence_score']
    )

    # Create airline_checkpoint_mappings table
    op.create_table(
        'airline_checkpoint_mappings',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('airport_code', sa.String(3), nullable=False, index=True),
        sa.Column('airline', sa.String(50), nullable=False, index=True),
        sa.Column('terminal', sa.String(50), nullable=True),
        sa.Column('lat', sa.Float(), nullable=False),
        sa.Column('lng', sa.Float(), nullable=False),
        sa.Column('counter_numbers', JSONB, nullable=True),
        sa.Column('operating_hours', JSONB, nullable=True),
        sa.Column('discovery_method', sa.String(50), default='crowdsourced'),
        sa.Column('confidence_score', sa.Float(), default=0.0),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.Column('is_verified', sa.Boolean(), default=False),
        sa.Column('is_active', sa.Boolean(), default=True),
    )

    # Create index for airline_checkpoint_mappings
    op.create_index(
        'idx_airport_airline_terminal',
        'airline_checkpoint_mappings',
        ['airport_code', 'airline', 'terminal']
    )


def downgrade() -> None:
    # Drop indexes first
    op.drop_index('idx_airport_airline_terminal', table_name='airline_checkpoint_mappings')
    op.drop_index('idx_checkpoint_type', table_name='discovered_checkpoints')
    op.drop_index('idx_airport_airline', table_name='discovered_checkpoints')
    op.drop_index('idx_location_stationary', table_name='location_traces')
    op.drop_index('idx_session_timestamp', table_name='location_traces')
    op.drop_index('idx_airport_airline_timestamp', table_name='location_traces')

    # Drop tables
    op.drop_table('airline_checkpoint_mappings')
    op.drop_table('discovered_checkpoints')
    op.drop_table('location_traces')

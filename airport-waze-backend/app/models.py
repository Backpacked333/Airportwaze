"""
SQLAlchemy ORM models for AirportWaze.
Includes models for airports, checkpoints, telemetry, and learned distributions.
"""

from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, ForeignKey, JSON, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.database import Base


class Airport(Base):
    """Airport master data"""
    __tablename__ = "airports"

    code = Column(String(3), primary_key=True)
    name = Column(String(255), nullable=False)
    city = Column(String(255), nullable=False)
    lat = Column(Float, nullable=False)
    lng = Column(Float, nullable=False)
    terminals = Column(JSONB)  # List of terminal names
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    checkpoints = relationship("Checkpoint", back_populates="airport")
    telemetry_batches = relationship("TelemetryBatch", back_populates="airport")


class Checkpoint(Base):
    """Security checkpoints, bag check, passport control locations"""
    __tablename__ = "checkpoints"

    id = Column(String(50), primary_key=True)
    airport_code = Column(String(3), ForeignKey("airports.code"), nullable=False)
    name = Column(String(255), nullable=False)
    type = Column(String(50), nullable=False)  # 'tsa', 'tsa_precheck', 'bag_check', 'passport_control'
    terminal = Column(String(100), nullable=False)
    lat = Column(Float, nullable=False)
    lng = Column(Float, nullable=False)
    base_wait_minutes = Column(Integer, nullable=False)
    discovered = Column(Boolean, default=False)  # True if found via zone discovery
    confidence = Column(Float)  # 0-1, confidence in discovered location
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    airport = relationship("Airport", back_populates="checkpoints")
    observations = relationship("WaitTimeObservation", back_populates="checkpoint")
    distribution = relationship("CheckpointDistribution", back_populates="checkpoint", uselist=False)

    # Indexes
    __table_args__ = (
        Index('idx_checkpoint_airport_terminal', 'airport_code', 'terminal'),
        Index('idx_checkpoint_type', 'type'),
    )


class TelemetryBatch(Base):
    """
    Batch of telemetry points uploaded by users.
    TimescaleDB hypertable partitioned by uploaded_at.
    """
    __tablename__ = "telemetry_batches"

    batch_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False)  # Anonymous client-generated UUID
    airport_code = Column(String(3), ForeignKey("airports.code"), nullable=False)
    session_id = Column(UUID(as_uuid=True), nullable=False)  # UUID for this airport visit
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    points = Column(JSONB, nullable=False)  # Array of telemetry points
    device_info = Column(JSONB)  # Optional device metadata

    # Relationships
    airport = relationship("Airport", back_populates="telemetry_batches")

    # Indexes
    __table_args__ = (
        Index('idx_telemetry_airport_time', 'airport_code', 'uploaded_at'),
        Index('idx_telemetry_session', 'session_id'),
    )


class ZoneDwellEvent(Base):
    """
    Preprocessed zone dwell events (computed on-device or server-side).
    TimescaleDB hypertable partitioned by enter_time.
    """
    __tablename__ = "zone_dwell_events"

    event_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    zone_id = Column(String(100), nullable=False)  # Could be checkpoint_id or discovered zone
    zone_type = Column(String(50), nullable=False)  # 'security', 'bag_check', 'passport_control'
    enter_time = Column(DateTime(timezone=True), nullable=False)
    exit_time = Column(DateTime(timezone=True))
    dwell_seconds = Column(Integer)
    confidence = Column(Float)  # 0-1, how confident we are in classification
    user_id = Column(UUID(as_uuid=True), nullable=False)
    session_id = Column(UUID(as_uuid=True), nullable=False)

    # Indexes
    __table_args__ = (
        Index('idx_zone_dwell_zone_time', 'zone_id', 'enter_time'),
        Index('idx_zone_dwell_type', 'zone_type'),
    )


class WaitTimeObservation(Base):
    """
    Individual wait time observations from various sources.
    Used for learning checkpoint distributions.
    TimescaleDB hypertable partitioned by observed_at.
    """
    __tablename__ = "wait_time_observations"

    observation_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    checkpoint_id = Column(String(50), ForeignKey("checkpoints.id"), nullable=False)
    observed_at = Column(DateTime(timezone=True), nullable=False)
    wait_minutes = Column(Integer, nullable=False)
    source = Column(String(50), nullable=False)  # 'telemetry', 'crowdsourced', 'tsa_api', 'cbp_api'
    confidence = Column(Float)  # 0-1, confidence in observation
    user_id = Column(UUID(as_uuid=True))  # Optional, for crowdsourced
    session_id = Column(UUID(as_uuid=True))  # Optional

    # Relationships
    checkpoint = relationship("Checkpoint", back_populates="observations")

    # Indexes
    __table_args__ = (
        Index('idx_wait_obs_checkpoint_time', 'checkpoint_id', 'observed_at'),
        Index('idx_wait_obs_source', 'source'),
    )


class CheckpointDistribution(Base):
    """
    Learned wait time distribution parameters for each checkpoint.
    Updated periodically by Bayesian learning algorithm.
    """
    __tablename__ = "checkpoint_distributions"

    checkpoint_id = Column(String(50), ForeignKey("checkpoints.id"), primary_key=True)
    mu = Column(Float, nullable=False)  # Log-normal mu parameter
    sigma = Column(Float, nullable=False)  # Log-normal sigma parameter
    sample_size = Column(Integer, nullable=False, default=0)
    confidence = Column(String(20), nullable=False)  # 'low', 'medium', 'high'
    last_updated = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    checkpoint = relationship("Checkpoint", back_populates="distribution")


class FlightSchedule(Base):
    """
    Flight schedules for demand forecasting.
    Fetched periodically from flight data APIs.
    """
    __tablename__ = "flight_schedules"

    flight_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    flight_number = Column(String(20), nullable=False)
    airline = Column(String(3), nullable=False)  # IATA airline code
    airport_code = Column(String(3), ForeignKey("airports.code"), nullable=False)
    departure_time = Column(DateTime(timezone=True), nullable=False)
    terminal = Column(String(100))
    gate = Column(String(20))
    estimated_passengers = Column(Integer)
    fetched_at = Column(DateTime(timezone=True), server_default=func.now())

    # Indexes
    __table_args__ = (
        Index('idx_flight_airport_departure', 'airport_code', 'departure_time'),
        Index('idx_flight_number', 'flight_number'),
    )


class TripEvent(Base):
    """
    User-confirmed trip events from 1-tap prompts.
    High-confidence signals for model calibration.
    """
    __tablename__ = "trip_events"

    event_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_type = Column(String(50), nullable=False)  # 'entered_security_line', 'cleared_security', etc.
    checkpoint_id = Column(String(50), ForeignKey("checkpoints.id"))
    timestamp = Column(DateTime(timezone=True), nullable=False)
    lat = Column(Float, nullable=False)
    lng = Column(Float, nullable=False)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    session_id = Column(UUID(as_uuid=True), nullable=False)

    # Indexes
    __table_args__ = (
        Index('idx_trip_event_checkpoint', 'checkpoint_id', 'timestamp'),
        Index('idx_trip_event_type', 'event_type'),
    )


class CrowdsourcedReport(Base):
    """
    User-submitted wait time reports (legacy model, now using WaitTimeObservation).
    Keeping for backward compatibility.
    """
    __tablename__ = "crowdsourced_reports"

    report_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    airport_code = Column(String(3), ForeignKey("airports.code"), nullable=False)
    checkpoint_id = Column(String(50), ForeignKey("checkpoints.id"), nullable=False)
    reported_wait_minutes = Column(Integer, nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    reporter_id = Column(String(100))  # Optional user identifier
    user_lat = Column(Float)
    user_lng = Column(Float)

    # Indexes
    __table_args__ = (
        Index('idx_report_checkpoint_time', 'checkpoint_id', 'timestamp'),
    )

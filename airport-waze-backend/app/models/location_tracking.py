"""Location tracking model for user movements."""
from sqlalchemy import Column, String, Integer, Float, DateTime, Boolean, Index, Interval
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime
from app.core.database import Base


class LocationTrace(Base):
    """Track user location breadcrumbs for movement analysis."""

    __tablename__ = "location_traces"

    id = Column(Integer, primary_key=True, index=True)

    # User identification
    user_id = Column(Integer, nullable=True)  # Authenticated users
    session_id = Column(String(100), index=True, nullable=False)  # Anonymous session tracking

    # Flight information
    airport_code = Column(String(3), index=True, nullable=False)
    airline = Column(String(50), nullable=True)  # User's airline
    flight_number = Column(String(20), nullable=True)
    terminal = Column(String(50), nullable=True)

    # Location data
    lat = Column(Float, nullable=False)
    lng = Column(Float, nullable=False)
    accuracy = Column(Float, nullable=True)  # GPS accuracy in meters

    # Movement metadata
    speed = Column(Float, nullable=True)  # meters per second
    heading = Column(Float, nullable=True)  # degrees (0-360)
    is_stationary = Column(Boolean, default=False)  # Detected as standing still

    # Context
    activity_type = Column(String(50), nullable=True)  # "walking", "standing", "check_in", "security", etc.
    detected_checkpoint_id = Column(String(50), nullable=True)  # Auto-detected checkpoint

    # Timestamps
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Additional metadata
    metadata = Column(JSONB, nullable=True)  # Battery level, app version, etc.

    # Composite indexes for efficient queries
    __table_args__ = (
        Index('idx_airport_airline_timestamp', 'airport_code', 'airline', 'timestamp'),
        Index('idx_session_timestamp', 'session_id', 'timestamp'),
        Index('idx_location_stationary', 'airport_code', 'is_stationary', 'timestamp'),
        # GiST index for geospatial queries (PostGIS extension)
        # Index('idx_location_gist', 'lat', 'lng', postgresql_using='gist'),
    )

    def __repr__(self):
        return f"<LocationTrace {self.airport_code} {self.airline} @ ({self.lat}, {self.lng})>"


class DiscoveredCheckpoint(Base):
    """Dynamically discovered checkpoints from crowdsourced location data."""

    __tablename__ = "discovered_checkpoints"

    id = Column(Integer, primary_key=True, index=True)

    # Location
    airport_code = Column(String(3), index=True, nullable=False)
    terminal = Column(String(50), nullable=True)

    # Centroid of clustered locations
    center_lat = Column(Float, nullable=False)
    center_lng = Column(Float, nullable=False)
    radius_meters = Column(Float, nullable=False)  # Cluster radius

    # Checkpoint classification
    checkpoint_type = Column(String(50), nullable=False)  # "airline_checkin", "security", "gate", etc.
    airline = Column(String(50), nullable=True)  # Specific airline if detected
    confidence_score = Column(Float, default=0.0)  # 0.0 to 1.0

    # Statistics
    sample_size = Column(Integer, default=0)  # Number of location traces used
    avg_dwell_time_seconds = Column(Integer, nullable=True)  # Average time users spend here
    first_detected = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Clustering metadata
    cluster_data = Column(JSONB, nullable=True)  # DBSCAN parameters, density, etc.

    # Verification
    is_verified = Column(Boolean, default=False)  # Manually verified by admin
    is_active = Column(Boolean, default=True)  # Still relevant

    __table_args__ = (
        Index('idx_airport_airline', 'airport_code', 'airline'),
        Index('idx_checkpoint_type', 'checkpoint_type', 'confidence_score'),
    )

    def __repr__(self):
        airline_str = f" - {self.airline}" if self.airline else ""
        return f"<DiscoveredCheckpoint {self.checkpoint_type}{airline_str} @ {self.airport_code}>"


class AirlineCheckpointMapping(Base):
    """Map airlines to their check-in counter locations."""

    __tablename__ = "airline_checkpoint_mappings"

    id = Column(Integer, primary_key=True, index=True)

    # Identification
    airport_code = Column(String(3), index=True, nullable=False)
    airline = Column(String(50), index=True, nullable=False)
    terminal = Column(String(50), nullable=True)

    # Location
    lat = Column(Float, nullable=False)
    lng = Column(Float, nullable=False)

    # Metadata
    counter_numbers = Column(JSONB, nullable=True)  # ["1-5", "A", "B", etc.]
    operating_hours = Column(JSONB, nullable=True)  # {"start": "04:00", "end": "22:00"}

    # Discovery method
    discovery_method = Column(String(50), default="crowdsourced")  # "crowdsourced", "manual", "official"
    confidence_score = Column(Float, default=0.0)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Status
    is_verified = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)

    __table_args__ = (
        Index('idx_airport_airline_terminal', 'airport_code', 'airline', 'terminal'),
    )

    def __repr__(self):
        return f"<AirlineCheckpointMapping {self.airline} @ {self.airport_code} {self.terminal}>"

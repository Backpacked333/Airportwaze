"""Wait time report model for crowdsourced data."""
from sqlalchemy import Column, String, Integer, Float, DateTime, Index
from datetime import datetime
from app.core.database import Base


class WaitTimeReport(Base):
    """Crowdsourced wait time reports from users."""

    __tablename__ = "wait_time_reports"

    id = Column(Integer, primary_key=True, index=True)
    airport_code = Column(String(3), index=True, nullable=False)
    checkpoint_id = Column(String(50), index=True, nullable=False)
    reported_wait_minutes = Column(Integer, nullable=False)

    # User information (optional)
    reporter_id = Column(String(100), nullable=True)
    user_id = Column(Integer, nullable=True)  # Foreign key to User if authenticated

    # Location data
    user_lat = Column(Float, nullable=True)
    user_lng = Column(Float, nullable=True)

    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Composite indexes for common queries
    __table_args__ = (
        Index('idx_airport_checkpoint_created', 'airport_code', 'checkpoint_id', 'created_at'),
    )

    def __repr__(self):
        return f"<WaitTimeReport {self.airport_code}-{self.checkpoint_id}: {self.reported_wait_minutes}min>"

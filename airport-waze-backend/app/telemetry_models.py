"""
Telemetry data models for user-contributed wait time observations.
Implements privacy-preserving k-anonymity protection.
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class UserState(str, Enum):
    """User activity state detected from phone sensors"""
    WALKING = "walking"
    WAITING_IN_QUEUE = "waiting_in_queue"
    RIDING_SHUTTLE = "riding_shuttle"
    IDLE = "idle"
    UNKNOWN = "unknown"


class TelemetryPoint(BaseModel):
    """Single telemetry data point from user's phone"""
    timestamp: str
    lat: float
    lng: float
    speed: Optional[float] = None  # m/s
    acceleration: Optional[float] = None  # m/s^2
    heading: Optional[float] = None  # degrees
    altitude: Optional[float] = None  # meters (from barometer)
    battery_level: Optional[float] = None  # 0-100
    horizontal_accuracy: Optional[float] = None  # meters


class TelemetryBatch(BaseModel):
    """Batch of telemetry points (uploaded when user on WiFi)"""
    user_id: str  # Anonymous UUID generated client-side
    airport_code: str
    session_id: str  # UUID for this airport visit
    points: List[TelemetryPoint]
    device_info: Optional[dict] = None


class ZoneDwellEvent(BaseModel):
    """Preprocessed zone dwell event (computed on-device)"""
    zone_id: str
    zone_type: str  # "security", "bag_check", "passport_control"
    enter_time: str
    exit_time: str
    dwell_seconds: int
    confidence: float = Field(ge=0.0, le=1.0)  # 0-1, confidence in classification


class TripEvent(BaseModel):
    """User-confirmed trip event (1-tap prompts)"""
    event_type: str  # "entered_security_line", "cleared_security", "dropped_bag"
    checkpoint_id: Optional[str] = None
    timestamp: str
    lat: float
    lng: float


class WaitTimeObservation(BaseModel):
    """
    A processed wait time observation from telemetry data.
    This is derived from zone dwell events or user reports.
    """
    checkpoint_id: str
    wait_time_minutes: int
    observed_at: datetime
    confidence: float = Field(ge=0.0, le=1.0)
    source: str  # "telemetry", "user_report", "zone_dwell"
    session_id: str
    context: Optional[dict] = None  # hour, day_of_week, etc.


class TelemetryStats(BaseModel):
    """Aggregated telemetry statistics (k-anonymity protected)"""
    airport_code: str
    active_sessions_24h: int
    total_observations: int
    coverage_quality: str  # "insufficient", "limited", "good", "excellent"
    last_updated: str
    checkpoint_coverage: dict  # checkpoint_id -> observation_count

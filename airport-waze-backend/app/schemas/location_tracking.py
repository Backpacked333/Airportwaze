"""Pydantic schemas for location tracking."""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class LocationTraceCreate(BaseModel):
    """Schema for creating a location trace."""
    session_id: str = Field(..., description="Anonymous session identifier")
    airport_code: str = Field(..., min_length=3, max_length=3)
    airline: Optional[str] = None
    flight_number: Optional[str] = None
    terminal: Optional[str] = None
    lat: float = Field(..., ge=-90, le=90)
    lng: float = Field(..., ge=-180, le=180)
    accuracy: Optional[float] = Field(None, ge=0)
    speed: Optional[float] = Field(None, ge=0)
    heading: Optional[float] = Field(None, ge=0, le=360)
    timestamp: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None


class LocationTraceResponse(BaseModel):
    """Schema for location trace response."""
    id: int
    session_id: str
    airport_code: str
    airline: Optional[str]
    lat: float
    lng: float
    is_stationary: bool
    activity_type: Optional[str]
    detected_checkpoint_id: Optional[str]
    timestamp: datetime

    class Config:
        from_attributes = True


class MovementPattern(BaseModel):
    """Analyzed movement pattern for a session."""
    session_id: str
    total_traces: int
    duration_seconds: int
    stationary_periods: List[Dict[str, Any]]  # {lat, lng, duration, detected_activity}
    movement_path: List[Dict[str, float]]  # [{lat, lng, timestamp}]
    average_speed: float
    detected_checkpoints: List[str]


class DiscoveredCheckpointResponse(BaseModel):
    """Schema for discovered checkpoint."""
    id: int
    airport_code: str
    terminal: Optional[str]
    center_lat: float
    center_lng: float
    radius_meters: float
    checkpoint_type: str
    airline: Optional[str]
    confidence_score: float
    sample_size: int
    avg_dwell_time_seconds: Optional[int]
    is_verified: bool

    class Config:
        from_attributes = True


class AirlineCheckpointResponse(BaseModel):
    """Schema for airline checkpoint mapping."""
    id: int
    airport_code: str
    airline: str
    terminal: Optional[str]
    lat: float
    lng: float
    counter_numbers: Optional[List[str]]
    confidence_score: float
    is_verified: bool

    class Config:
        from_attributes = True


class CheckpointDiscoveryRequest(BaseModel):
    """Request to trigger checkpoint discovery for an airport."""
    airport_code: str = Field(..., min_length=3, max_length=3)
    airline: Optional[str] = None
    min_samples: int = Field(default=10, ge=5)
    max_radius_meters: float = Field(default=50, ge=10, le=200)


class HeatmapRequest(BaseModel):
    """Request for location heatmap data."""
    airport_code: str = Field(..., min_length=3, max_length=3)
    airline: Optional[str] = None
    terminal: Optional[str] = None
    hours_back: int = Field(default=24, ge=1, le=168)  # Max 1 week
    activity_type: Optional[str] = None


class HeatmapResponse(BaseModel):
    """Heatmap data response."""
    airport_code: str
    points: List[Dict[str, Any]]  # [{lat, lng, intensity, count}]
    clusters: List[Dict[str, Any]]  # Discovered clusters
    total_traces: int
    time_range: Dict[str, datetime]


class DwellTimeAnalysis(BaseModel):
    """Analysis of how long users spend at locations."""
    checkpoint_id: Optional[str]
    location: Dict[str, float]  # {lat, lng}
    avg_dwell_time_seconds: int
    median_dwell_time_seconds: int
    p95_dwell_time_seconds: int
    sample_size: int
    confidence: str  # "high", "medium", "low"


class AirlineCheckpointSuggestion(BaseModel):
    """Suggested airline checkpoint location."""
    airline: str
    airport_code: str
    terminal: Optional[str]
    suggested_lat: float
    suggested_lng: float
    confidence_score: float
    supporting_evidence: Dict[str, Any]
    sample_size: int
    avg_dwell_time_seconds: int
    should_verify: bool

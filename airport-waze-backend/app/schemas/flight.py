"""Flight and prediction Pydantic schemas."""
from pydantic import BaseModel
from typing import Optional, List
from app.schemas.wait_time import WaitTimeDistribution


class Flight(BaseModel):
    """User's flight information."""
    flight_number: Optional[str] = None
    airline: Optional[str] = None
    departure_time: str  # ISO format
    terminal: str
    gate: str
    airport_code: str


class WillIMakeItRequest(BaseModel):
    """Request for 'Will I make it?' probability calculation."""
    flight: Flight
    has_tsa_precheck: bool = False
    has_global_entry: bool = False
    has_checked_bags: bool = True
    mobility_factor: float = 1.0
    current_time: Optional[str] = None  # ISO format, defaults to now
    user_lat: Optional[float] = None
    user_lng: Optional[float] = None


class SegmentDistribution(BaseModel):
    """Time distribution for a journey segment."""
    step_name: str
    location: str
    lat: float
    lng: float
    wait_distribution: Optional[WaitTimeDistribution] = None
    walk_minutes: int
    walk_distance_meters: int
    checkpoint_id: Optional[str] = None


class WillIMakeItResponse(BaseModel):
    """Response with probability of making flight."""
    probability_of_making_it: float  # 0.0 to 1.0
    probability_percentage: int  # 0 to 100
    status: str  # "safe", "good", "risky", "unlikely", "very_unlikely"
    status_message: str
    total_time_p50: int  # median total time
    total_time_p80: int  # 80th percentile
    total_time_p90: int  # 90th percentile
    total_time_p95: int  # 95th percentile
    time_until_boarding: int  # minutes until boarding closes
    buffer_minutes: int  # recommended buffer
    leave_by_80: str  # ISO time to leave for 80% confidence
    leave_by_90: str  # ISO time to leave for 90% confidence
    leave_by_95: str  # ISO time to leave for 95% confidence
    segments: List[SegmentDistribution]
    simulation_runs: int  # number of Monte Carlo simulations
    boarding_cutoff_minutes: int  # minutes before departure when boarding closes

"""Journey planning Pydantic schemas."""
from pydantic import BaseModel
from typing import Optional, List


class JourneyRequest(BaseModel):
    """Schema for journey planning request."""
    airport_code: str
    terminal: str
    gate: str
    has_tsa_precheck: bool = False
    has_global_entry: bool = False
    has_checked_bags: bool = True
    mobility_factor: float = 1.0
    departure_time: Optional[str] = None
    user_lat: Optional[float] = None
    user_lng: Optional[float] = None


class JourneyStep(BaseModel):
    """Schema for a single journey step."""
    step_name: str
    location: str
    lat: float
    lng: float
    estimated_wait_minutes: int
    estimated_walk_minutes: int
    distance_meters: int
    checkpoint_id: Optional[str] = None


class JourneyPlan(BaseModel):
    """Schema for complete journey plan."""
    total_time_minutes: int
    total_distance_meters: int
    recommended_arrival_time: str
    steps: List[JourneyStep]
    buffer_minutes: int

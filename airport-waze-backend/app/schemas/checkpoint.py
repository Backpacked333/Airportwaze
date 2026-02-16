"""Checkpoint-related Pydantic schemas."""
from pydantic import BaseModel


class Checkpoint(BaseModel):
    """Schema for a checkpoint (security, bag check, etc.)."""
    id: str
    name: str
    type: str  # tsa, tsa_precheck, bag_check, passport_control
    terminal: str
    lat: float
    lng: float
    current_wait_minutes: int
    historical_avg_minutes: int
    status: str  # low, moderate, high, very_high
    last_updated: str

"""Airport-related Pydantic schemas."""
from pydantic import BaseModel
from typing import List
from app.schemas.checkpoint import Checkpoint


class Airport(BaseModel):
    """Schema for an airport."""
    code: str
    name: str
    city: str
    lat: float
    lng: float
    terminals: List[str]
    checkpoints: List[Checkpoint]

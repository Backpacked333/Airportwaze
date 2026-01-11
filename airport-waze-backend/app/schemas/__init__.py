"""Pydantic schemas for request/response validation."""
from app.schemas.checkpoint import Checkpoint
from app.schemas.airport import Airport
from app.schemas.journey import (
    JourneyRequest,
    JourneyStep,
    JourneyPlan,
)
from app.schemas.wait_time import (
    WaitTimeReport,
    WaitTimeDistribution,
)
from app.schemas.flight import (
    Flight,
    WillIMakeItRequest,
    WillIMakeItResponse,
    SegmentDistribution,
)
from app.schemas.user import (
    UserCreate,
    UserLogin,
    UserResponse,
    Token,
)

__all__ = [
    "Checkpoint",
    "Airport",
    "JourneyRequest",
    "JourneyStep",
    "JourneyPlan",
    "WaitTimeReport",
    "WaitTimeDistribution",
    "Flight",
    "WillIMakeItRequest",
    "WillIMakeItResponse",
    "SegmentDistribution",
    "UserCreate",
    "UserLogin",
    "UserResponse",
    "Token",
]

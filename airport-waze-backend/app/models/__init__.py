"""Database models."""
from app.models.wait_time_report import WaitTimeReport
from app.models.user import User
from app.models.location_tracking import (
    LocationTrace,
    DiscoveredCheckpoint,
    AirlineCheckpointMapping
)
from app.models.notifications import (
    NotificationPreference,
    NotificationHistory,
    AlertRule,
    UserLearningProfile
)

__all__ = [
    "WaitTimeReport",
    "User",
    "LocationTrace",
    "DiscoveredCheckpoint",
    "AirlineCheckpointMapping",
    "NotificationPreference",
    "NotificationHistory",
    "AlertRule",
    "UserLearningProfile"
]

"""
Notification models for smart alerts and user preferences.
"""
from sqlalchemy import (
    Column, String, Boolean, DateTime, Integer, Float, Text, JSON, ForeignKey
)
from sqlalchemy.orm import relationship
from datetime import datetime
from enum import Enum as PyEnum
from app.core.database import Base


class NotificationType(str, PyEnum):
    """Types of notifications that can be sent."""
    GATE_CHANGE = "gate_change"
    FLIGHT_DELAY = "flight_delay"
    SECURITY_SPIKE = "security_spike"
    LEAVE_NOW = "leave_now"
    BOARDING_ALERT = "boarding_alert"
    ROUTE_SUGGESTION = "route_suggestion"
    CHECKPOINT_ALERT = "checkpoint_alert"
    WEATHER_DELAY = "weather_delay"
    REMINDER = "reminder"
    PERSONALIZED_TIP = "personalized_tip"


class NotificationPriority(str, PyEnum):
    """Priority levels for notifications."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class NotificationChannel(str, PyEnum):
    """Channels for sending notifications."""
    PUSH = "push"
    EMAIL = "email"
    SMS = "sms"
    IN_APP = "in_app"


class NotificationPreference(Base):
    """
    User notification preferences and settings.
    Allows users to customize what notifications they receive and how.
    """

    __tablename__ = "notification_preferences"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)

    # Channel preferences
    enable_push = Column(Boolean, default=True, nullable=False)
    enable_email = Column(Boolean, default=True, nullable=False)
    enable_sms = Column(Boolean, default=False, nullable=False)
    enable_in_app = Column(Boolean, default=True, nullable=False)

    # Notification type preferences
    enable_gate_changes = Column(Boolean, default=True, nullable=False)
    enable_flight_delays = Column(Boolean, default=True, nullable=False)
    enable_security_alerts = Column(Boolean, default=True, nullable=False)
    enable_leave_now_alerts = Column(Boolean, default=True, nullable=False)
    enable_boarding_alerts = Column(Boolean, default=True, nullable=False)
    enable_route_suggestions = Column(Boolean, default=True, nullable=False)
    enable_weather_alerts = Column(Boolean, default=True, nullable=False)
    enable_reminders = Column(Boolean, default=True, nullable=False)
    enable_personalized_tips = Column(Boolean, default=False, nullable=False)

    # Advanced preferences
    min_probability_threshold = Column(Float, default=0.7, nullable=False)  # 70% confidence
    advance_notice_minutes = Column(Integer, default=120, nullable=False)  # 2 hours
    quiet_hours_start = Column(Integer, default=22, nullable=True)  # 10 PM
    quiet_hours_end = Column(Integer, default=7, nullable=True)  # 7 AM

    # Personalization settings
    average_walking_speed_mpm = Column(Float, default=80.0, nullable=False)  # meters per minute
    preferred_buffer_minutes = Column(Integer, default=30, nullable=False)
    learned_pace_multiplier = Column(Float, default=1.0, nullable=False)  # Auto-adjusted

    # Push notification tokens
    push_tokens = Column(JSON, default=list, nullable=False)  # List of device tokens

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", backref="notification_preference")

    def __repr__(self):
        return f"<NotificationPreference user_id={self.user_id}>"


class NotificationHistory(Base):
    """
    History of all notifications sent to users.
    Used for analytics, debugging, and preventing duplicate notifications.
    """

    __tablename__ = "notification_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # Notification details
    notification_type = Column(String, nullable=False, index=True)
    priority = Column(String, nullable=False)
    channel = Column(String, nullable=False)

    # Content
    title = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    data = Column(JSON, default=dict, nullable=False)  # Additional structured data

    # Context
    flight_number = Column(String, nullable=True, index=True)
    airport_code = Column(String, nullable=True, index=True)
    checkpoint_id = Column(String, nullable=True)

    # Delivery status
    sent_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    delivered_at = Column(DateTime, nullable=True)
    read_at = Column(DateTime, nullable=True)
    dismissed_at = Column(DateTime, nullable=True)

    # Tracking
    delivery_status = Column(String, default="pending", nullable=False)  # pending, sent, delivered, failed
    error_message = Column(Text, nullable=True)

    # Analytics
    was_acted_upon = Column(Boolean, default=False, nullable=False)
    action_taken = Column(String, nullable=True)  # e.g., "opened_app", "changed_route"

    # Relationships
    user = relationship("User", backref="notification_history")

    def __repr__(self):
        return f"<NotificationHistory {self.notification_type} to user {self.user_id}>"


class AlertRule(Base):
    """
    Configurable alert rules for custom notifications.
    Allows users to set up personalized alerts based on specific conditions.
    """

    __tablename__ = "alert_rules"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # Rule configuration
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)

    # Conditions (stored as JSON for flexibility)
    conditions = Column(JSON, nullable=False)
    # Example: {
    #   "airport_code": "JFK",
    #   "checkpoint_type": "tsa",
    #   "wait_time_threshold": 20,
    #   "time_window": {"start": "06:00", "end": "09:00"}
    # }

    # Actions
    notification_type = Column(String, nullable=False)
    priority = Column(String, default="medium", nullable=False)
    custom_message = Column(Text, nullable=True)

    # Constraints
    max_triggers_per_day = Column(Integer, default=5, nullable=False)
    cooldown_minutes = Column(Integer, default=60, nullable=False)  # Don't re-trigger within 1 hour

    # Tracking
    last_triggered_at = Column(DateTime, nullable=True)
    trigger_count_today = Column(Integer, default=0, nullable=False)
    total_trigger_count = Column(Integer, default=0, nullable=False)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", backref="alert_rules")

    def __repr__(self):
        return f"<AlertRule {self.name} for user {self.user_id}>"


class UserLearningProfile(Base):
    """
    Machine learning profile for personalized predictions.
    Learns user behavior patterns over time to improve recommendations.
    """

    __tablename__ = "user_learning_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True, index=True)

    # Learned patterns
    average_security_wait_actual = Column(Float, nullable=True)  # vs predicted
    average_walking_speed_actual = Column(Float, nullable=True)  # vs default
    typical_buffer_preference = Column(Integer, nullable=True)  # minutes before boarding

    # Behavioral patterns (JSON for flexibility)
    checkpoint_preferences = Column(JSON, default=dict, nullable=False)
    # Example: {"JFK": {"preferred_tsa_lane": "B3", "avg_time": 15}}

    travel_patterns = Column(JSON, default=dict, nullable=False)
    # Example: {"most_frequent_airports": ["JFK", "LAX"], "typical_travel_days": [1, 4, 5]}

    historical_accuracy = Column(JSON, default=dict, nullable=False)
    # Track how accurate our predictions were for this user
    # Example: {"predictions_made": 25, "predictions_accurate": 22, "accuracy_rate": 0.88}

    # Personalization scores
    prefers_safety_buffer = Column(Boolean, default=True, nullable=False)
    risk_tolerance = Column(Float, default=0.5, nullable=False)  # 0=very cautious, 1=risk-taker

    # Training data
    total_trips_tracked = Column(Integer, default=0, nullable=False)
    last_trip_date = Column(DateTime, nullable=True)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", backref="learning_profile")

    def __repr__(self):
        return f"<UserLearningProfile user_id={self.user_id} trips={self.total_trips_tracked}>"

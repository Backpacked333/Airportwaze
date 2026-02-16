"""User model for authentication and personalization."""
from sqlalchemy import Column, String, Boolean, DateTime, Integer
from datetime import datetime
from app.core.database import Base


class User(Base):
    """User model for authentication."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False)

    # User preferences
    has_tsa_precheck = Column(Boolean, default=False, nullable=False)
    has_global_entry = Column(Boolean, default=False, nullable=False)
    default_mobility_factor = Column(String, default="1.0", nullable=False)

    # Tracking
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_login = Column(DateTime, nullable=True)

    def __repr__(self):
        return f"<User {self.email}>"

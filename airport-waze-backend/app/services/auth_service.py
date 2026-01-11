"""Authentication service for user management."""
import logging
from typing import Optional
from sqlalchemy.orm import Session
from datetime import datetime

from app.models.user import User
from app.schemas.user import UserCreate, UserLogin, Token, UserResponse
from app.core.security import hash_password, verify_password, create_access_token, create_refresh_token

logger = logging.getLogger(__name__)


class AuthService:
    """Service for authentication operations."""

    @staticmethod
    def create_user(db: Session, user_data: UserCreate) -> User:
        """Create a new user."""
        # Check if user already exists
        existing_user = db.query(User).filter(User.email == user_data.email).first()
        if existing_user:
            raise ValueError("Email already registered")

        # Create new user
        db_user = User(
            email=user_data.email,
            hashed_password=hash_password(user_data.password),
            full_name=user_data.full_name,
            has_tsa_precheck=user_data.has_tsa_precheck,
            has_global_entry=user_data.has_global_entry,
            default_mobility_factor=str(user_data.default_mobility_factor),
        )

        db.add(db_user)
        db.commit()
        db.refresh(db_user)

        logger.info(f"Created new user: {user_data.email}")
        return db_user

    @staticmethod
    def authenticate_user(db: Session, credentials: UserLogin) -> Optional[User]:
        """Authenticate user with email and password."""
        user = db.query(User).filter(User.email == credentials.email).first()

        if not user:
            logger.warning(f"Authentication failed: user not found - {credentials.email}")
            return None

        if not verify_password(credentials.password, user.hashed_password):
            logger.warning(f"Authentication failed: invalid password - {credentials.email}")
            return None

        if not user.is_active:
            logger.warning(f"Authentication failed: user inactive - {credentials.email}")
            return None

        # Update last login
        user.last_login = datetime.utcnow()
        db.commit()

        logger.info(f"User authenticated: {credentials.email}")
        return user

    @staticmethod
    def create_tokens(user: User) -> Token:
        """Create access and refresh tokens for user."""
        token_data = {
            "sub": user.id,
            "email": user.email,
            "is_superuser": user.is_superuser
        }

        access_token = create_access_token(token_data)
        refresh_token = create_refresh_token(token_data)

        return Token(
            access_token=access_token,
            refresh_token=refresh_token
        )

    @staticmethod
    def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
        """Get user by ID."""
        return db.query(User).filter(User.id == user_id).first()

    @staticmethod
    def get_user_by_email(db: Session, email: str) -> Optional[User]:
        """Get user by email."""
        return db.query(User).filter(User.email == email).first()

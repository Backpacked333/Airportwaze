"""Authentication routes for user registration and login."""
import logging
from fastapi import APIRouter, HTTPException, Depends, Request, status
from sqlalchemy.orm import Session

from app.services.auth_service import AuthService
from app.schemas.user import UserCreate, UserLogin, Token, UserResponse
from app.core.database import get_db
from app.core.security import require_auth
from app.middleware.rate_limit import limiter

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("10/hour")
async def register_user(
    request: Request,
    user_data: UserCreate,
    db: Session = Depends(get_db)
) -> UserResponse:
    """
    Register a new user account.

    Args:
        user_data: User registration data including email, password, and preferences
        db: Database session

    Returns:
        Created user information (without password)

    Raises:
        HTTPException: 400 if email already registered or validation fails
    """
    try:
        user = AuthService.create_user(db, user_data)
        return UserResponse.from_orm(user)
    except ValueError as e:
        logger.warning(f"Registration failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error during registration: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user account"
        )


@router.post("/login", response_model=Token)
@limiter.limit("20/hour")
async def login_user(
    request: Request,
    credentials: UserLogin,
    db: Session = Depends(get_db)
) -> Token:
    """
    Authenticate user and return access tokens.

    Args:
        credentials: User login credentials (email and password)
        db: Database session

    Returns:
        Access and refresh tokens

    Raises:
        HTTPException: 401 if authentication fails
    """
    user = AuthService.authenticate_user(db, credentials)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"}
        )

    try:
        tokens = AuthService.create_tokens(user)
        logger.info(f"User logged in: {user.email}")
        return tokens
    except Exception as e:
        logger.error(f"Error creating tokens: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate authentication tokens"
        )


@router.get("/me", response_model=UserResponse)
@limiter.limit("100/minute")
async def get_current_user(
    request: Request,
    current_user: dict = Depends(require_auth),
    db: Session = Depends(get_db)
) -> UserResponse:
    """
    Get current authenticated user's information.

    Args:
        current_user: Current user from JWT token
        db: Database session

    Returns:
        Current user information

    Raises:
        HTTPException: 401 if not authenticated, 404 if user not found
    """
    user_id = current_user.get("sub")

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token"
        )

    user = AuthService.get_user_by_id(db, user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return UserResponse.from_orm(user)

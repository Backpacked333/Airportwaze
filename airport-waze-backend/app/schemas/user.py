"""User-related Pydantic schemas."""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime


class UserCreate(BaseModel):
    """Schema for user registration."""
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: Optional[str] = None
    has_tsa_precheck: bool = False
    has_global_entry: bool = False
    default_mobility_factor: float = 1.0


class UserLogin(BaseModel):
    """Schema for user login."""
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    """Schema for user response."""
    id: int
    email: str
    full_name: Optional[str]
    is_active: bool
    has_tsa_precheck: bool
    has_global_entry: bool
    default_mobility_factor: float
    created_at: datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    """Schema for authentication token."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    """Schema for token payload."""
    sub: Optional[int] = None
    exp: Optional[datetime] = None

from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from uuid import UUID
from typing import Optional
from app.models.user import UserRole


# Request schemas
class UserRegisterRequest(BaseModel):
    """Schema for user registration"""
    email: EmailStr = Field(..., max_length=255)
    password: str = Field(..., min_length=8, max_length=100)


class UserLoginRequest(BaseModel):
    """Schema for user login"""
    email: EmailStr
    password: str


# Response schemas
class UserBase(BaseModel):
    """Base user schema"""
    id: UUID
    email: str
    role: UserRole
    is_active: bool

    model_config = {"from_attributes": True}


class UserResponse(UserBase):
    """Detailed user profile response"""
    is_locked: bool
    created_at: datetime
    updated_at: datetime


class UserLoginResponse(BaseModel):
    """Login response with session token"""
    session_token: str
    user: UserBase

    model_config = {"from_attributes": True}

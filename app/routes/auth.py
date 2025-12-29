from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.dependencies.auth import get_current_user
from app.models import User
from app.schemas.user import (
    UserRegisterRequest,
    UserLoginRequest,
    UserResponse,
    UserLoginResponse,
    UserBase
)
from app.services import auth_service


router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse, status_code=201)
async def register(
    request: Request,
    data: UserRegisterRequest,
    db: AsyncSession = Depends(get_db)
):
    """Register a new user account"""
    user = await auth_service.register_user(
        db=db,
        email=data.email,
        password=data.password,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent")
    )
    return user


@router.post("/login", response_model=UserLoginResponse)
async def login(
    request: Request,
    data: UserLoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """Authenticate user and create session"""
    user, session_token = await auth_service.login_user(
        db=db,
        email=data.email,
        password=data.password,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent")
    )

    return {
        "session_token": session_token,
        "user": user
    }


@router.post("/logout")
async def logout(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Invalidate current session (logout)"""
    # Get session token from request state (set by get_current_user)
    session = getattr(request.state, "session", None)
    session_token = session.session_token if session else None

    if session_token:
        await auth_service.logout_user(
            db=db,
            session_token=session_token,
            user=current_user,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent")
        )

    return {"message": "Logged out successfully"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(
    current_user: User = Depends(get_current_user)
):
    """Get current authenticated user profile"""
    return current_user

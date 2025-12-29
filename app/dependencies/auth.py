from fastapi import Depends, HTTPException, Header, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timezone
from typing import List, Optional
from app.core.database import get_db
from app.models import User, Session, UserRole


async def get_current_user(
    request: Request,
    authorization: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Dependency to get current authenticated user from session token.
    Validates session and returns user object or raises 401.
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="Not authenticated")

    # Extract token from Bearer scheme
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")

    session_token = parts[1]

    # Query session
    stmt = select(Session).where(Session.session_token == session_token)
    result = await db.execute(stmt)
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(status_code=401, detail="Invalid or expired session token")

    # Check session validity
    if not session.is_valid:
        raise HTTPException(status_code=401, detail="Session has been invalidated")

    if session.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=401, detail="Session has expired")

    # Load user
    stmt = select(User).where(User.id == session.user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    # Check user status
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is inactive")

    if user.is_locked:
        raise HTTPException(status_code=403, detail="Account is locked")

    # Store request info for audit logging
    request.state.current_user = user
    request.state.session = session

    return user


def require_role(required_roles: List[UserRole]):
    """
    Dependency factory to check if user has required role.
    Usage: Depends(require_role([UserRole.ADMIN, UserRole.SUPER_ADMIN]))
    """
    async def role_checker(user: User = Depends(get_current_user)) -> User:
        if user.role not in required_roles:
            raise HTTPException(
                status_code=403,
                detail=f"Insufficient permissions. Required role: {[r.value for r in required_roles]}"
            )
        return user

    return role_checker


# Convenience dependencies for common role checks
async def require_admin(user: User = Depends(get_current_user)) -> User:
    """Require ADMIN or SUPER_ADMIN role"""
    if user.role not in [UserRole.ADMIN, UserRole.SUPER_ADMIN]:
        raise HTTPException(status_code=403, detail="Admin privileges required")
    return user


async def require_super_admin(user: User = Depends(get_current_user)) -> User:
    """Require SUPER_ADMIN role"""
    if user.role != UserRole.SUPER_ADMIN:
        raise HTTPException(status_code=403, detail="Super Admin privileges required")
    return user

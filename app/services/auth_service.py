from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException
from datetime import datetime, timedelta, timezone
from typing import Optional
from app.models import User, Session, UserRole
from app.core.security import hash_password, verify_password, generate_session_token
from app.core.config import settings
from app.services.audit_service import create_audit_log


async def register_user(
    db: AsyncSession,
    email: str,
    password: str,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None
) -> User:
    """
    Register a new user.

    Args:
        db: Database session
        email: User email (will be lowercased)
        password: Plain text password (will be hashed)
        ip_address: IP address for audit log
        user_agent: User agent for audit log

    Returns:
        Created User object

    Raises:
        HTTPException: If email already exists
    """
    # Normalize email to lowercase
    email = email.lower()

    # Check if email already exists
    stmt = select(User).where(User.email == email)
    result = await db.execute(stmt)
    existing_user = result.scalar_one_or_none()

    if existing_user:
        raise HTTPException(status_code=409, detail="Email already exists")

    # Create user
    user = User(
        email=email,
        password_hash=hash_password(password),
        role=UserRole.USER,
        is_active=True,
        is_locked=False
    )

    db.add(user)
    await db.commit()
    await db.refresh(user)

    # Create audit log
    await create_audit_log(
        db=db,
        actor_id=user.id,
        action="USER_REGISTERED",
        resource_type="USER",
        resource_id=user.id,
        ip_address=ip_address,
        user_agent=user_agent
    )

    return user


async def login_user(
    db: AsyncSession,
    email: str,
    password: str,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None
) -> tuple[User, str]:
    """
    Authenticate user and create session.

    Args:
        db: Database session
        email: User email
        password: Plain text password
        ip_address: IP address for session and audit
        user_agent: User agent for session and audit

    Returns:
        Tuple of (User object, session_token string)

    Raises:
        HTTPException: If credentials invalid or account locked/inactive
    """
    # Normalize email
    email = email.lower()

    # Find user
    stmt = select(User).where(User.email == email)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user or not verify_password(password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    # Check account status
    if user.is_locked:
        raise HTTPException(status_code=403, detail="Account is locked")

    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is inactive")

    # Create session
    session_token = generate_session_token()
    expires_at = datetime.now(timezone.utc) + timedelta(hours=settings.SESSION_EXPIRY_HOURS)

    session = Session(
        session_token=session_token,
        user_id=user.id,
        ip_address=ip_address,
        user_agent=user_agent,
        expires_at=expires_at,
        is_valid=True
    )

    db.add(session)
    await db.commit()

    # Create audit log
    await create_audit_log(
        db=db,
        actor_id=user.id,
        action="USER_LOGIN",
        resource_type="USER",
        resource_id=user.id,
        ip_address=ip_address,
        user_agent=user_agent
    )

    return user, session_token


async def logout_user(
    db: AsyncSession,
    session_token: str,
    user: User,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None
) -> None:
    """
    Invalidate user session (logout).

    Args:
        db: Database session
        session_token: Session token to invalidate
        user: Current user
        ip_address: IP address for audit
        user_agent: User agent for audit
    """
    # Find and invalidate session
    stmt = select(Session).where(Session.session_token == session_token)
    result = await db.execute(stmt)
    session = result.scalar_one_or_none()

    if session:
        session.is_valid = False
        await db.commit()

    # Create audit log
    await create_audit_log(
        db=db,
        actor_id=user.id,
        action="USER_LOGOUT",
        resource_type="USER",
        resource_id=user.id,
        ip_address=ip_address,
        user_agent=user_agent
    )

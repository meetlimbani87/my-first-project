from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from fastapi import HTTPException
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID
from app.models import User, AdminRequest, AdminRequestStatus, UserRole
from app.services.audit_service import create_audit_log


async def create_admin_request(
    db: AsyncSession,
    user: User,
    request_reason: Optional[str] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None
) -> AdminRequest:
    """Create admin role request"""
    # Check if user is already Admin or Super Admin
    if user.role in [UserRole.ADMIN, UserRole.SUPER_ADMIN]:
        raise HTTPException(status_code=403, detail="User already has admin privileges")

    # Check for existing pending request
    stmt = select(AdminRequest).where(
        and_(
            AdminRequest.user_id == user.id,
            AdminRequest.status == AdminRequestStatus.PENDING
        )
    )
    result = await db.execute(stmt)
    existing_request = result.scalar_one_or_none()

    if existing_request:
        raise HTTPException(status_code=400, detail="User already has pending admin request")

    # Create request
    admin_request = AdminRequest(
        user_id=user.id,
        status=AdminRequestStatus.PENDING,
        request_reason=request_reason
    )

    db.add(admin_request)
    await db.commit()
    await db.refresh(admin_request)

    # Create audit log
    await create_audit_log(
        db=db,
        actor_id=user.id,
        action="ADMIN_REQUESTED",
        resource_type="ADMIN_REQUEST",
        resource_id=admin_request.id,
        ip_address=ip_address,
        user_agent=user_agent
    )

    return admin_request


async def approve_admin_request(
    db: AsyncSession,
    request_id: UUID,
    approved_by: User,
    admin_notes: Optional[str] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None
) -> AdminRequest:
    """Approve admin role request"""
    # Get request
    stmt = select(AdminRequest).where(AdminRequest.id == request_id)
    result = await db.execute(stmt)
    admin_request = result.scalar_one_or_none()

    if not admin_request:
        raise HTTPException(status_code=404, detail="Admin request not found")

    if admin_request.status != AdminRequestStatus.PENDING:
        raise HTTPException(status_code=400, detail="Request already resolved")

    # Get user
    stmt = select(User).where(User.id == admin_request.user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Update request
    admin_request.status = AdminRequestStatus.APPROVED
    admin_request.approved_by = approved_by.id
    admin_request.admin_notes = admin_notes
    admin_request.resolved_at = datetime.now(timezone.utc)

    # Update user role
    user.role = UserRole.ADMIN

    await db.commit()
    await db.refresh(admin_request)

    # Create audit log
    await create_audit_log(
        db=db,
        actor_id=approved_by.id,
        action="ADMIN_APPROVED",
        resource_type="ADMIN_REQUEST",
        resource_id=admin_request.id,
        details={"user_id": str(user.id)},
        ip_address=ip_address,
        user_agent=user_agent
    )

    return admin_request


async def reject_admin_request(
    db: AsyncSession,
    request_id: UUID,
    rejected_by: User,
    admin_notes: Optional[str] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None
) -> AdminRequest:
    """Reject admin role request"""
    # Get request
    stmt = select(AdminRequest).where(AdminRequest.id == request_id)
    result = await db.execute(stmt)
    admin_request = result.scalar_one_or_none()

    if not admin_request:
        raise HTTPException(status_code=404, detail="Admin request not found")

    if admin_request.status != AdminRequestStatus.PENDING:
        raise HTTPException(status_code=400, detail="Request already resolved")

    # Update request
    admin_request.status = AdminRequestStatus.REJECTED
    admin_request.approved_by = rejected_by.id
    admin_request.admin_notes = admin_notes
    admin_request.resolved_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(admin_request)

    # Create audit log
    await create_audit_log(
        db=db,
        actor_id=rejected_by.id,
        action="ADMIN_REJECTED",
        resource_type="ADMIN_REQUEST",
        resource_id=admin_request.id,
        details={"user_id": str(admin_request.user_id)},
        ip_address=ip_address,
        user_agent=user_agent
    )

    return admin_request


async def revoke_admin_role(
    db: AsyncSession,
    user_id: UUID,
    revoked_by: User,
    reason: Optional[str] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None
) -> User:
    """Revoke admin role from user"""
    # Get user
    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.role != UserRole.ADMIN:
        raise HTTPException(status_code=400, detail="User is not an Admin")

    old_role = user.role
    user.role = UserRole.USER
    user.updated_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(user)

    # Create audit log
    await create_audit_log(
        db=db,
        actor_id=revoked_by.id,
        action="ADMIN_REVOKED",
        resource_type="USER",
        resource_id=user.id,
        details={"reason": reason, "old_role": old_role.value, "new_role": user.role.value},
        ip_address=ip_address,
        user_agent=user_agent
    )

    return user


async def lock_user(
    db: AsyncSession,
    user_id: UUID,
    locked_by: User,
    reason: Optional[str] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None
) -> User:
    """Lock user account"""
    # Get user
    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.role == UserRole.SUPER_ADMIN:
        raise HTTPException(status_code=400, detail="Cannot lock SUPER_ADMIN accounts")

    if user.is_locked:
        raise HTTPException(status_code=400, detail="Account already locked")

    user.is_locked = True
    user.updated_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(user)

    # Create audit log
    await create_audit_log(
        db=db,
        actor_id=locked_by.id,
        action="USER_LOCKED",
        resource_type="USER",
        resource_id=user.id,
        details={"reason": reason},
        ip_address=ip_address,
        user_agent=user_agent
    )

    return user


async def unlock_user(
    db: AsyncSession,
    user_id: UUID,
    unlocked_by: User,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None
) -> User:
    """Unlock user account"""
    # Get user
    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if not user.is_locked:
        raise HTTPException(status_code=400, detail="Account already unlocked")

    user.is_locked = False
    user.updated_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(user)

    # Create audit log
    await create_audit_log(
        db=db,
        actor_id=unlocked_by.id,
        action="USER_UNLOCKED",
        resource_type="USER",
        resource_id=user.id,
        ip_address=ip_address,
        user_agent=user_agent
    )

    return user

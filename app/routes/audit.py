from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from datetime import datetime
from typing import Optional
from uuid import UUID
from app.core.database import get_db
from app.dependencies.auth import require_super_admin
from app.models import User, AuditLog
from app.schemas.audit_log import (
    PaginatedAuditLogsResponse,
    AuditLogResponse,
    AuditActorInfo
)


router = APIRouter(prefix="/audit", tags=["Audit Logs"])


@router.get("/logs", response_model=PaginatedAuditLogsResponse)
async def get_audit_logs(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_super_admin),
    action: Optional[str] = None,
    actor_id: Optional[UUID] = None,
    resource_type: Optional[str] = None,
    resource_id: Optional[UUID] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200)
):
    """View system-wide audit logs (Super Admin only)"""
    # Build query
    query = select(AuditLog)
    conditions = []

    if action:
        conditions.append(AuditLog.action == action)
    if actor_id:
        conditions.append(AuditLog.actor_id == actor_id)
    if resource_type:
        conditions.append(AuditLog.resource_type == resource_type)
    if resource_id:
        conditions.append(AuditLog.resource_id == resource_id)
    if start_date:
        conditions.append(AuditLog.created_at >= start_date)
    if end_date:
        conditions.append(AuditLog.created_at <= end_date)

    if conditions:
        query = query.where(and_(*conditions))

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    result = await db.execute(count_query)
    total = result.scalar()

    # Get paginated results (newest first)
    query = query.order_by(AuditLog.created_at.desc()).offset((page - 1) * limit).limit(limit)
    result = await db.execute(query)
    logs = result.scalars().all()

    # Load actor info for each log
    log_responses = []
    for log in logs:
        actor = None
        if log.actor_id:
            stmt = select(User).where(User.id == log.actor_id)
            actor_result = await db.execute(stmt)
            actor_user = actor_result.scalar_one_or_none()
            if actor_user:
                actor = AuditActorInfo(id=actor_user.id, email=actor_user.email, role=actor_user.role)

        log_responses.append(
            AuditLogResponse(
                id=log.id,
                actor=actor,
                action=log.action,
                resource_type=log.resource_type,
                resource_id=log.resource_id,
                details=log.details,
                ip_address=log.ip_address,
                user_agent=log.user_agent,
                created_at=log.created_at
            )
        )

    return {
        "total": total,
        "page": page,
        "limit": limit,
        "logs": log_responses
    }


@router.get("/users/{user_id}", response_model=PaginatedAuditLogsResponse)
async def get_user_audit_logs(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_super_admin),
    action: Optional[str] = None,
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200)
):
    """View audit logs for specific user (Super Admin only)"""
    # Verify user exists
    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Build query
    query = select(AuditLog).where(AuditLog.actor_id == user_id)

    if action:
        query = query.where(AuditLog.action == action)

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    result = await db.execute(count_query)
    total = result.scalar()

    # Get paginated results (newest first)
    query = query.order_by(AuditLog.created_at.desc()).offset((page - 1) * limit).limit(limit)
    result = await db.execute(query)
    logs = result.scalars().all()

    # Build responses with actor info
    log_responses = []
    for log in logs:
        log_responses.append(
            AuditLogResponse(
                id=log.id,
                actor=AuditActorInfo(id=user.id, email=user.email, role=user.role),
                action=log.action,
                resource_type=log.resource_type,
                resource_id=log.resource_id,
                details=log.details,
                ip_address=log.ip_address,
                user_agent=log.user_agent,
                created_at=log.created_at
            )
        )

    return {
        "total": total,
        "page": page,
        "limit": limit,
        "logs": log_responses
    }

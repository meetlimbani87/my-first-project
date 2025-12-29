from fastapi import APIRouter, Depends, Request, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional
from uuid import UUID
from app.core.database import get_db
from app.dependencies.auth import require_super_admin
from app.models import User, AdminRequest, AdminRequestStatus, UserRole
from app.schemas.admin_request import (
    AdminRequestApproveRequest,
    AdminRequestRejectRequest,
    AdminRequestActionResponse,
    RevokeAdminRequest,
    RevokeAdminResponse,
    LockUserRequest,
    LockUserResponse,
    PaginatedAdminRequestsResponse,
    AdminRequestWithUserResponse,
    RequesterInfo,
    ApproverInfo
)
from app.services import admin_service


router = APIRouter(prefix="/admin", tags=["Admin Management"])


@router.get("/requests", response_model=PaginatedAdminRequestsResponse)
async def get_all_admin_requests(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_super_admin),
    status: Optional[AdminRequestStatus] = None,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100)
):
    """View all admin role requests (Super Admin only)"""
    # Build query
    query = select(AdminRequest)

    if status:
        query = query.where(AdminRequest.status == status)

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    result = await db.execute(count_query)
    total = result.scalar()

    # Get paginated results - PENDING first, then by created_at desc
    query = query.order_by(
        (AdminRequest.status == AdminRequestStatus.PENDING).desc(),
        AdminRequest.created_at.desc()
    ).offset((page - 1) * limit).limit(limit)

    result = await db.execute(query)
    requests = result.scalars().all()

    # Load user and approver info for each request
    request_responses = []
    for req in requests:
        # Load requester
        stmt = select(User).where(User.id == req.user_id)
        user_result = await db.execute(stmt)
        requester = user_result.scalar_one()

        # Load approver if exists
        approver = None
        if req.approved_by:
            stmt = select(User).where(User.id == req.approved_by)
            approver_result = await db.execute(stmt)
            approver_user = approver_result.scalar_one_or_none()
            if approver_user:
                approver = ApproverInfo(id=approver_user.id, email=approver_user.email)

        request_responses.append(
            AdminRequestWithUserResponse(
                id=req.id,
                user=RequesterInfo(
                    id=requester.id,
                    email=requester.email,
                    role=requester.role,
                    created_at=requester.created_at
                ),
                status=req.status,
                request_reason=req.request_reason,
                admin_notes=req.admin_notes,
                created_at=req.created_at,
                resolved_at=req.resolved_at,
                approved_by=approver
            )
        )

    return {
        "total": total,
        "page": page,
        "limit": limit,
        "requests": request_responses
    }


@router.post("/requests/{request_id}/approve", response_model=AdminRequestActionResponse)
async def approve_admin_request(
    request_id: UUID,
    data: AdminRequestApproveRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_super_admin)
):
    """Approve admin role request (Super Admin only)"""
    admin_request = await admin_service.approve_admin_request(
        db=db,
        request_id=request_id,
        approved_by=current_user,
        admin_notes=data.admin_notes,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent")
    )

    # Load approver info
    stmt = select(User).where(User.id == admin_request.approved_by)
    result = await db.execute(stmt)
    approver = result.scalar_one()

    return AdminRequestActionResponse(
        id=admin_request.id,
        user_id=admin_request.user_id,
        status=admin_request.status,
        admin_notes=admin_request.admin_notes,
        resolved_at=admin_request.resolved_at,
        approved_by=ApproverInfo(id=approver.id, email=approver.email)
    )


@router.post("/requests/{request_id}/reject", response_model=AdminRequestActionResponse)
async def reject_admin_request(
    request_id: UUID,
    data: AdminRequestRejectRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_super_admin)
):
    """Reject admin role request (Super Admin only)"""
    admin_request = await admin_service.reject_admin_request(
        db=db,
        request_id=request_id,
        rejected_by=current_user,
        admin_notes=data.admin_notes,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent")
    )

    # Load approver info
    stmt = select(User).where(User.id == admin_request.approved_by)
    result = await db.execute(stmt)
    approver = result.scalar_one()

    return AdminRequestActionResponse(
        id=admin_request.id,
        user_id=admin_request.user_id,
        status=admin_request.status,
        admin_notes=admin_request.admin_notes,
        resolved_at=admin_request.resolved_at,
        approved_by=ApproverInfo(id=approver.id, email=approver.email)
    )


@router.post("/users/{user_id}/revoke-admin", response_model=RevokeAdminResponse)
async def revoke_admin_role(
    user_id: UUID,
    data: RevokeAdminRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_super_admin)
):
    """Revoke Admin role from user (Super Admin only)"""
    old_role = UserRole.ADMIN
    user = await admin_service.revoke_admin_role(
        db=db,
        user_id=user_id,
        revoked_by=current_user,
        reason=data.reason,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent")
    )

    return RevokeAdminResponse(
        user_id=user.id,
        email=user.email,
        old_role=old_role,
        new_role=user.role,
        updated_at=user.updated_at
    )


@router.post("/users/{user_id}/lock", response_model=LockUserResponse)
async def lock_user(
    user_id: UUID,
    data: LockUserRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_super_admin)
):
    """Lock user account (Super Admin only)"""
    user = await admin_service.lock_user(
        db=db,
        user_id=user_id,
        locked_by=current_user,
        reason=data.reason,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent")
    )

    return LockUserResponse(
        user_id=user.id,
        email=user.email,
        is_locked=user.is_locked,
        updated_at=user.updated_at
    )


@router.post("/users/{user_id}/unlock", response_model=LockUserResponse)
async def unlock_user(
    user_id: UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_super_admin)
):
    """Unlock user account (Super Admin only)"""
    user = await admin_service.unlock_user(
        db=db,
        user_id=user_id,
        unlocked_by=current_user,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent")
    )

    return LockUserResponse(
        user_id=user.id,
        email=user.email,
        is_locked=user.is_locked,
        updated_at=user.updated_at
    )

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.dependencies.auth import get_current_user
from app.models import User, AdminRequest
from app.schemas.user import UserResponse
from app.schemas.admin_request import (
    AdminRequestCreateRequest,
    AdminRequestCreateResponse,
    AdminRequestStatusResponse,
    AdminRequestResponse,
    ApproverInfo
)
from app.services import admin_service


router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/profile", response_model=UserResponse)
async def get_profile(
    current_user: User = Depends(get_current_user)
):
    """Get current user's detailed profile"""
    return current_user


@router.post("/request-admin", response_model=AdminRequestCreateResponse, status_code=201)
async def request_admin_role(
    request: Request,
    data: AdminRequestCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Request Admin role upgrade"""
    admin_request = await admin_service.create_admin_request(
        db=db,
        user=current_user,
        request_reason=data.request_reason,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent")
    )
    return admin_request


@router.get("/admin-request-status", response_model=AdminRequestStatusResponse)
async def get_admin_request_status(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Check status of current user's admin request"""
    # Get most recent admin request for user
    stmt = select(AdminRequest).where(
        AdminRequest.user_id == current_user.id
    ).order_by(AdminRequest.created_at.desc())

    result = await db.execute(stmt)
    admin_request = result.scalar_one_or_none()

    if not admin_request:
        return {
            "has_request": False,
            "request": None
        }

    # Load approver if exists
    approver = None
    if admin_request.approved_by:
        stmt = select(User).where(User.id == admin_request.approved_by)
        result = await db.execute(stmt)
        approver_user = result.scalar_one_or_none()
        if approver_user:
            approver = ApproverInfo(id=approver_user.id, email=approver_user.email)

    return {
        "has_request": True,
        "request": AdminRequestResponse(
            id=admin_request.id,
            status=admin_request.status,
            request_reason=admin_request.request_reason,
            admin_notes=admin_request.admin_notes,
            created_at=admin_request.created_at,
            resolved_at=admin_request.resolved_at,
            approved_by=approver
        )
    }

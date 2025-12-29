from pydantic import BaseModel, Field
from datetime import datetime
from uuid import UUID
from typing import Optional, List
from app.models.admin_request import AdminRequestStatus
from app.models.user import UserRole


# Request schemas
class AdminRequestCreateRequest(BaseModel):
    """Schema for creating admin role request"""
    request_reason: Optional[str] = Field(None, max_length=1000)


class AdminRequestApproveRequest(BaseModel):
    """Schema for approving admin request"""
    admin_notes: Optional[str] = None


class AdminRequestRejectRequest(BaseModel):
    """Schema for rejecting admin request"""
    admin_notes: Optional[str] = None


class RevokeAdminRequest(BaseModel):
    """Schema for revoking admin role"""
    reason: Optional[str] = None


class LockUserRequest(BaseModel):
    """Schema for locking user account"""
    reason: Optional[str] = None


# Response schemas
class ApproverInfo(BaseModel):
    """Approver information"""
    id: UUID
    email: str

    model_config = {"from_attributes": True}


class RequesterInfo(BaseModel):
    """Requester information"""
    id: UUID
    email: str
    role: UserRole
    created_at: datetime

    model_config = {"from_attributes": True}


class AdminRequestCreateResponse(BaseModel):
    """Response for admin request creation"""
    id: UUID
    user_id: UUID
    status: AdminRequestStatus
    request_reason: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


class AdminRequestResponse(BaseModel):
    """Detailed admin request response"""
    id: UUID
    status: AdminRequestStatus
    request_reason: Optional[str]
    admin_notes: Optional[str]
    created_at: datetime
    resolved_at: Optional[datetime]
    approved_by: Optional[ApproverInfo]

    model_config = {"from_attributes": True}


class AdminRequestStatusResponse(BaseModel):
    """User's admin request status response"""
    has_request: bool
    request: Optional[AdminRequestResponse]


class AdminRequestWithUserResponse(BaseModel):
    """Admin request with user info (for super admin view)"""
    id: UUID
    user: RequesterInfo
    status: AdminRequestStatus
    request_reason: Optional[str]
    admin_notes: Optional[str]
    created_at: datetime
    resolved_at: Optional[datetime]
    approved_by: Optional[ApproverInfo]

    model_config = {"from_attributes": True}


class AdminRequestActionResponse(BaseModel):
    """Response for approve/reject actions"""
    id: UUID
    user_id: UUID
    status: AdminRequestStatus
    admin_notes: Optional[str]
    resolved_at: datetime
    approved_by: ApproverInfo


class RevokeAdminResponse(BaseModel):
    """Response for admin role revocation"""
    user_id: UUID
    email: str
    old_role: UserRole
    new_role: UserRole
    updated_at: datetime


class LockUserResponse(BaseModel):
    """Response for user lock action"""
    user_id: UUID
    email: str
    is_locked: bool
    updated_at: datetime


class PaginatedAdminRequestsResponse(BaseModel):
    """Paginated admin requests response"""
    total: int
    page: int
    limit: int
    requests: List[AdminRequestWithUserResponse]

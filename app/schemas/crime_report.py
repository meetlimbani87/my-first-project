from pydantic import BaseModel, Field
from datetime import datetime
from uuid import UUID
from typing import Optional, List
from app.models.crime_report import ReportStatus, ReportPriority
from app.models.user import UserRole


# Request schemas
class CrimeReportCreateRequest(BaseModel):
    """Schema for creating a crime report"""
    title: str = Field(..., max_length=255)
    description: str = Field(...)
    location: Optional[str] = Field(None, max_length=500)
    incident_date: Optional[datetime] = None
    priority: Optional[ReportPriority] = ReportPriority.MEDIUM


class ReportStatusUpdateRequest(BaseModel):
    """Schema for updating report status"""
    status: ReportStatus
    notes: Optional[str] = None


class ReportPriorityUpdateRequest(BaseModel):
    """Schema for updating report priority"""
    priority: ReportPriority


class ReportNotesUpdateRequest(BaseModel):
    """Schema for updating admin notes"""
    admin_notes: str


# Response schemas
class ReportCreatorBrief(BaseModel):
    """Brief creator info for reports"""
    id: UUID
    email: str

    model_config = {"from_attributes": True}


class ReportCreatorDetail(ReportCreatorBrief):
    """Detailed creator info (includes role for admin view)"""
    role: UserRole


class CrimeReportBriefResponse(BaseModel):
    """Brief report summary (for list view accessible to all)"""
    id: UUID
    title: str
    status: ReportStatus
    priority: Optional[ReportPriority]
    user_id: UUID
    created_at: datetime

    model_config = {"from_attributes": True}


class CrimeReportUserResponse(BaseModel):
    """Report details for user (own reports, no admin_notes)"""
    id: UUID
    title: str
    description: str
    location: Optional[str]
    incident_date: Optional[datetime]
    user_id: UUID
    status: ReportStatus
    priority: Optional[ReportPriority]
    created_at: datetime
    updated_at: datetime
    creator: ReportCreatorBrief

    model_config = {"from_attributes": True}


class CrimeReportAdminResponse(CrimeReportUserResponse):
    """Report details for admin (includes admin_notes and creator role)"""
    admin_notes: Optional[str]
    creator: ReportCreatorDetail


class CrimeReportCreateResponse(BaseModel):
    """Response for report creation"""
    id: UUID
    title: str
    description: str
    location: Optional[str]
    incident_date: Optional[datetime]
    user_id: UUID
    status: ReportStatus
    priority: Optional[ReportPriority]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ReportStatusUpdateResponse(BaseModel):
    """Response for status update"""
    id: UUID
    status: ReportStatus
    updated_at: datetime

    model_config = {"from_attributes": True}


class ReportPriorityUpdateResponse(BaseModel):
    """Response for priority update"""
    id: UUID
    priority: ReportPriority
    updated_at: datetime

    model_config = {"from_attributes": True}


class ReportNotesUpdateResponse(BaseModel):
    """Response for notes update"""
    id: UUID
    admin_notes: str
    updated_at: datetime

    model_config = {"from_attributes": True}


class ReportDeleteResponse(BaseModel):
    """Response for report deletion"""
    message: str
    id: UUID


class ReportHistoryItemResponse(BaseModel):
    """Single status history item"""
    id: UUID
    old_status: Optional[ReportStatus]
    new_status: ReportStatus
    notes: Optional[str]
    changed_by: ReportCreatorDetail
    created_at: datetime

    model_config = {"from_attributes": True}


class ReportHistoryResponse(BaseModel):
    """Report status history response"""
    report_id: UUID
    history: List[ReportHistoryItemResponse]


class PaginatedReportsResponse(BaseModel):
    """Paginated reports response"""
    total: int
    page: int
    limit: int
    reports: List[CrimeReportBriefResponse]


class PaginatedMyReportsResponse(BaseModel):
    """Paginated my reports response"""
    total: int
    page: int
    limit: int
    reports: List[CrimeReportUserResponse]

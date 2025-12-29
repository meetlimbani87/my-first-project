from fastapi import APIRouter, Depends, Request, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from typing import Optional
from uuid import UUID
from app.core.database import get_db
from app.dependencies.auth import get_current_user, require_admin
from app.models import User, CrimeReport, ReportStatusHistory, UserRole, ReportStatus, ReportPriority
from app.schemas.crime_report import (
    CrimeReportCreateRequest,
    CrimeReportCreateResponse,
    CrimeReportBriefResponse,
    CrimeReportUserResponse,
    CrimeReportAdminResponse,
    ReportStatusUpdateRequest,
    ReportStatusUpdateResponse,
    ReportPriorityUpdateRequest,
    ReportPriorityUpdateResponse,
    ReportNotesUpdateRequest,
    ReportNotesUpdateResponse,
    ReportDeleteResponse,
    ReportHistoryResponse,
    ReportHistoryItemResponse,
    PaginatedReportsResponse,
    PaginatedMyReportsResponse,
    ReportCreatorBrief,
    ReportCreatorDetail
)
from app.services import report_service


router = APIRouter(prefix="/reports", tags=["Crime Reports"])


@router.post("", response_model=CrimeReportCreateResponse, status_code=201)
async def create_report(
    request: Request,
    data: CrimeReportCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create new crime report"""
    report = await report_service.create_report(
        db=db,
        user=current_user,
        title=data.title,
        description=data.description,
        location=data.location,
        incident_date=data.incident_date,
        priority=data.priority,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent")
    )
    return report


@router.get("/my-reports", response_model=PaginatedMyReportsResponse)
async def get_my_reports(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    status: Optional[ReportStatus] = None
):
    """Get all reports created by current user"""
    # Build query
    query = select(CrimeReport).where(
        and_(
            CrimeReport.user_id == current_user.id,
            CrimeReport.is_deleted == False
        )
    )

    if status:
        query = query.where(CrimeReport.status == status)

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    result = await db.execute(count_query)
    total = result.scalar()

    # Get paginated results
    query = query.order_by(CrimeReport.created_at.desc()).offset((page - 1) * limit).limit(limit)
    result = await db.execute(query)
    reports = result.scalars().all()

    # Load creator for each report
    report_responses = []
    for report in reports:
        stmt = select(User).where(User.id == report.user_id)
        user_result = await db.execute(stmt)
        creator = user_result.scalar_one()

        report_responses.append(
            CrimeReportUserResponse(
                id=report.id,
                title=report.title,
                description=report.description,
                location=report.location,
                incident_date=report.incident_date,
                user_id=report.user_id,
                status=report.status,
                priority=report.priority,
                created_at=report.created_at,
                updated_at=report.updated_at,
                creator=ReportCreatorBrief(id=creator.id, email=creator.email)
            )
        )

    return {
        "total": total,
        "page": page,
        "limit": limit,
        "reports": report_responses
    }


@router.get("", response_model=PaginatedReportsResponse)
async def get_all_reports(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    status: Optional[ReportStatus] = None,
    priority: Optional[ReportPriority] = None
):
    """Get brief summary of all reports (accessible to all authenticated users)"""
    # Build query
    query = select(CrimeReport).where(CrimeReport.is_deleted == False)

    if status:
        query = query.where(CrimeReport.status == status)
    if priority:
        query = query.where(CrimeReport.priority == priority)

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    result = await db.execute(count_query)
    total = result.scalar()

    # Get paginated results
    query = query.order_by(CrimeReport.created_at.desc()).offset((page - 1) * limit).limit(limit)
    result = await db.execute(query)
    reports = result.scalars().all()

    # Return only brief summary
    brief_reports = [
        CrimeReportBriefResponse(
            id=report.id,
            title=report.title,
            status=report.status,
            priority=report.priority,
            user_id=report.user_id,
            created_at=report.created_at
        )
        for report in reports
    ]

    return {
        "total": total,
        "page": page,
        "limit": limit,
        "reports": brief_reports
    }


@router.get("/{report_id}")
async def get_report_by_id(
    report_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get full details of specific report"""
    report = await report_service.get_report_by_id(db, report_id)

    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    # Load creator
    stmt = select(User).where(User.id == report.user_id)
    result = await db.execute(stmt)
    creator = result.scalar_one()

    # Check access permissions
    is_admin = current_user.role in [UserRole.ADMIN, UserRole.SUPER_ADMIN]
    is_owner = report.user_id == current_user.id

    # USER can only view their own reports
    if not is_admin and not is_owner:
        raise HTTPException(status_code=403, detail="Insufficient permissions to view this report")

    # Return appropriate response based on role
    if is_admin:
        return CrimeReportAdminResponse(
            id=report.id,
            title=report.title,
            description=report.description,
            location=report.location,
            incident_date=report.incident_date,
            user_id=report.user_id,
            status=report.status,
            priority=report.priority,
            admin_notes=report.admin_notes,
            created_at=report.created_at,
            updated_at=report.updated_at,
            creator=ReportCreatorDetail(id=creator.id, email=creator.email, role=creator.role)
        )
    else:
        return CrimeReportUserResponse(
            id=report.id,
            title=report.title,
            description=report.description,
            location=report.location,
            incident_date=report.incident_date,
            user_id=report.user_id,
            status=report.status,
            priority=report.priority,
            created_at=report.created_at,
            updated_at=report.updated_at,
            creator=ReportCreatorBrief(id=creator.id, email=creator.email)
        )


@router.patch("/{report_id}/status", response_model=ReportStatusUpdateResponse)
async def update_report_status(
    report_id: UUID,
    data: ReportStatusUpdateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Update report status (Admin/Super Admin only)"""
    report = await report_service.get_report_by_id(db, report_id)

    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    report = await report_service.update_report_status(
        db=db,
        report=report,
        new_status=data.status,
        changed_by=current_user,
        notes=data.notes,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent")
    )

    return ReportStatusUpdateResponse(
        id=report.id,
        status=report.status,
        updated_at=report.updated_at
    )


@router.patch("/{report_id}/priority", response_model=ReportPriorityUpdateResponse)
async def update_report_priority(
    report_id: UUID,
    data: ReportPriorityUpdateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Update report priority (Admin/Super Admin only)"""
    report = await report_service.get_report_by_id(db, report_id)

    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    report = await report_service.update_report_priority(
        db=db,
        report=report,
        new_priority=data.priority,
        changed_by=current_user,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent")
    )

    return ReportPriorityUpdateResponse(
        id=report.id,
        priority=report.priority,
        updated_at=report.updated_at
    )


@router.patch("/{report_id}/notes", response_model=ReportNotesUpdateResponse)
async def update_report_notes(
    report_id: UUID,
    data: ReportNotesUpdateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Add or update admin notes on report (Admin/Super Admin only)"""
    report = await report_service.get_report_by_id(db, report_id)

    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    report = await report_service.update_report_notes(
        db=db,
        report=report,
        admin_notes=data.admin_notes,
        changed_by=current_user,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent")
    )

    return ReportNotesUpdateResponse(
        id=report.id,
        admin_notes=report.admin_notes,
        updated_at=report.updated_at
    )


@router.delete("/{report_id}", response_model=ReportDeleteResponse)
async def delete_report(
    report_id: UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Soft delete report (Admin/Super Admin only)"""
    report = await report_service.get_report_by_id(db, report_id)

    if not report:
        raise HTTPException(status_code=404, detail="Report not found or already deleted")

    await report_service.soft_delete_report(
        db=db,
        report=report,
        deleted_by=current_user,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent")
    )

    return ReportDeleteResponse(
        message="Report deleted successfully",
        id=report_id
    )


@router.get("/{report_id}/history", response_model=ReportHistoryResponse)
async def get_report_history(
    report_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get status change history for report"""
    report = await report_service.get_report_by_id(db, report_id)

    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    # Check access permissions
    is_admin = current_user.role in [UserRole.ADMIN, UserRole.SUPER_ADMIN]
    is_owner = report.user_id == current_user.id

    if not is_admin and not is_owner:
        raise HTTPException(status_code=403, detail="Insufficient permissions to view this report's history")

    # Get history
    stmt = select(ReportStatusHistory).where(
        ReportStatusHistory.report_id == report_id
    ).order_by(ReportStatusHistory.created_at.asc())

    result = await db.execute(stmt)
    history_entries = result.scalars().all()

    # Load changer info for each entry
    history_responses = []
    for entry in history_entries:
        stmt = select(User).where(User.id == entry.changed_by)
        user_result = await db.execute(stmt)
        changer = user_result.scalar_one()

        history_responses.append(
            ReportHistoryItemResponse(
                id=entry.id,
                old_status=entry.old_status,
                new_status=entry.new_status,
                notes=entry.notes,
                changed_by=ReportCreatorDetail(id=changer.id, email=changer.email, role=changer.role),
                created_at=entry.created_at
            )
        )

    return ReportHistoryResponse(
        report_id=report_id,
        history=history_responses
    )

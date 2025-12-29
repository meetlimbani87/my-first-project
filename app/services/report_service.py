from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from fastapi import HTTPException
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID
from app.models import CrimeReport, ReportStatusHistory, User, ReportStatus, ReportPriority
from app.services.audit_service import create_audit_log


async def create_report(
    db: AsyncSession,
    user: User,
    title: str,
    description: str,
    location: Optional[str] = None,
    incident_date: Optional[datetime] = None,
    priority: Optional[ReportPriority] = ReportPriority.MEDIUM,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None
) -> CrimeReport:
    """Create a new crime report"""
    report = CrimeReport(
        title=title,
        description=description,
        location=location,
        incident_date=incident_date,
        user_id=user.id,
        status=ReportStatus.NEW,
        priority=priority,
        is_deleted=False
    )

    db.add(report)
    await db.flush()  # Flush to get report.id

    # Create initial status history entry
    history = ReportStatusHistory(
        report_id=report.id,
        old_status=None,
        new_status=ReportStatus.NEW,
        changed_by=user.id,
        notes=None
    )
    db.add(history)

    await db.commit()
    await db.refresh(report)

    # Create audit log
    await create_audit_log(
        db=db,
        actor_id=user.id,
        action="REPORT_CREATED",
        resource_type="CRIME_REPORT",
        resource_id=report.id,
        ip_address=ip_address,
        user_agent=user_agent
    )

    return report


async def get_report_by_id(
    db: AsyncSession,
    report_id: UUID
) -> Optional[CrimeReport]:
    """Get report by ID (excluding soft-deleted)"""
    stmt = select(CrimeReport).where(
        and_(
            CrimeReport.id == report_id,
            CrimeReport.is_deleted == False
        )
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def update_report_status(
    db: AsyncSession,
    report: CrimeReport,
    new_status: ReportStatus,
    changed_by: User,
    notes: Optional[str] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None
) -> CrimeReport:
    """Update report status and create history entry"""
    old_status = report.status

    report.status = new_status
    report.updated_at = datetime.now(timezone.utc)

    # Create history entry
    history = ReportStatusHistory(
        report_id=report.id,
        old_status=old_status,
        new_status=new_status,
        changed_by=changed_by.id,
        notes=notes
    )
    db.add(history)

    await db.commit()
    await db.refresh(report)

    # Create audit log
    await create_audit_log(
        db=db,
        actor_id=changed_by.id,
        action="REPORT_STATUS_CHANGED",
        resource_type="CRIME_REPORT",
        resource_id=report.id,
        details={"old": old_status.value, "new": new_status.value},
        ip_address=ip_address,
        user_agent=user_agent
    )

    return report


async def update_report_priority(
    db: AsyncSession,
    report: CrimeReport,
    new_priority: ReportPriority,
    changed_by: User,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None
) -> CrimeReport:
    """Update report priority"""
    old_priority = report.priority

    report.priority = new_priority
    report.updated_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(report)

    # Create audit log
    await create_audit_log(
        db=db,
        actor_id=changed_by.id,
        action="REPORT_PRIORITY_CHANGED",
        resource_type="CRIME_REPORT",
        resource_id=report.id,
        details={"old": old_priority.value if old_priority else None, "new": new_priority.value},
        ip_address=ip_address,
        user_agent=user_agent
    )

    return report


async def update_report_notes(
    db: AsyncSession,
    report: CrimeReport,
    admin_notes: str,
    changed_by: User,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None
) -> CrimeReport:
    """Update admin notes on report"""
    report.admin_notes = admin_notes
    report.updated_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(report)

    # Create audit log
    await create_audit_log(
        db=db,
        actor_id=changed_by.id,
        action="REPORT_NOTES_UPDATED",
        resource_type="CRIME_REPORT",
        resource_id=report.id,
        ip_address=ip_address,
        user_agent=user_agent
    )

    return report


async def soft_delete_report(
    db: AsyncSession,
    report: CrimeReport,
    deleted_by: User,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None
) -> None:
    """Soft delete a report"""
    if report.is_deleted:
        raise HTTPException(status_code=404, detail="Report not found or already deleted")

    report.is_deleted = True
    report.deleted_at = datetime.now(timezone.utc)

    await db.commit()

    # Create audit log
    await create_audit_log(
        db=db,
        actor_id=deleted_by.id,
        action="REPORT_DELETED",
        resource_type="CRIME_REPORT",
        resource_id=report.id,
        ip_address=ip_address,
        user_agent=user_agent
    )

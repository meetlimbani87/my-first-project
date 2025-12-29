from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from typing import Optional, Dict, Any
from app.models import AuditLog


async def create_audit_log(
    db: AsyncSession,
    actor_id: Optional[UUID],
    action: str,
    resource_type: Optional[str] = None,
    resource_id: Optional[UUID] = None,
    details: Optional[Dict[str, Any]] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None
) -> AuditLog:
    """
    Create an audit log entry.

    Args:
        db: Database session
        actor_id: ID of user performing action (None for system actions)
        action: Action being performed (e.g., 'USER_REGISTERED', 'REPORT_CREATED')
        resource_type: Type of resource affected (e.g., 'USER', 'CRIME_REPORT')
        resource_id: ID of affected resource
        details: Additional context as JSON
        ip_address: IP address of request
        user_agent: User agent string from request

    Returns:
        Created AuditLog object
    """
    audit_log = AuditLog(
        actor_id=actor_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        details=details,
        ip_address=ip_address,
        user_agent=user_agent
    )

    db.add(audit_log)
    await db.commit()
    await db.refresh(audit_log)

    return audit_log

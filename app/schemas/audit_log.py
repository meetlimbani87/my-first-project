from pydantic import BaseModel
from datetime import datetime
from uuid import UUID
from typing import Optional, List, Dict, Any
from app.models.user import UserRole


# Response schemas
class AuditActorInfo(BaseModel):
    """Actor information in audit logs"""
    id: UUID
    email: str
    role: UserRole

    model_config = {"from_attributes": True}


class AuditLogResponse(BaseModel):
    """Audit log entry response"""
    id: UUID
    actor: Optional[AuditActorInfo]
    action: str
    resource_type: Optional[str]
    resource_id: Optional[UUID]
    details: Optional[Dict[str, Any]]
    ip_address: Optional[str]
    user_agent: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


class PaginatedAuditLogsResponse(BaseModel):
    """Paginated audit logs response"""
    total: int
    page: int
    limit: int
    logs: List[AuditLogResponse]

from sqlalchemy import Column, Text, DateTime, ForeignKey, Enum as SQLEnum, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum
from app.core.database import Base


class AdminRequestStatus(str, enum.Enum):
    """Admin request status enumeration"""
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class AdminRequest(Base):
    """Admin role request model"""
    __tablename__ = "admin_requests"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    status = Column(SQLEnum(AdminRequestStatus), default=AdminRequestStatus.PENDING, nullable=False, index=True)
    approved_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    request_reason = Column(Text, nullable=True)
    admin_notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    resolved_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    requester = relationship("User", back_populates="admin_requests", foreign_keys=[user_id])
    approver = relationship("User", back_populates="approved_requests", foreign_keys=[approved_by])

    # Note: Unique constraint for one pending request per user handled in service layer
    # PostgreSQL partial unique index would require raw SQL or text() construct
    __table_args__ = ()

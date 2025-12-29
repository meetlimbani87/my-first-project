from sqlalchemy import Column, String, Text, Boolean, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum
from app.core.database import Base


class ReportStatus(str, enum.Enum):
    """Crime report status enumeration"""
    NEW = "NEW"
    ASSIGNED = "ASSIGNED"
    INVESTIGATING = "INVESTIGATING"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"


class ReportPriority(str, enum.Enum):
    """Crime report priority enumeration"""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class CrimeReport(Base):
    """Crime report model"""
    __tablename__ = "crime_reports"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    location = Column(String(500), nullable=True)
    incident_date = Column(DateTime(timezone=True), nullable=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    status = Column(SQLEnum(ReportStatus), default=ReportStatus.NEW, nullable=False, index=True)
    priority = Column(SQLEnum(ReportPriority), default=ReportPriority.MEDIUM, nullable=True, index=True)
    admin_notes = Column(Text, nullable=True)
    is_deleted = Column(Boolean, default=False, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    creator = relationship("User", back_populates="reports", foreign_keys=[user_id])
    status_history = relationship("ReportStatusHistory", back_populates="report", cascade="all, delete-orphan")

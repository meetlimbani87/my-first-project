from sqlalchemy import Column, Text, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from app.core.database import Base
from app.models.crime_report import ReportStatus


class ReportStatusHistory(Base):
    """Report status change history model"""
    __tablename__ = "report_status_history"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    report_id = Column(UUID(as_uuid=True), ForeignKey("crime_reports.id", ondelete="CASCADE"), nullable=False, index=True)
    old_status = Column(SQLEnum(ReportStatus), nullable=True)  # null for initial creation
    new_status = Column(SQLEnum(ReportStatus), nullable=False)
    changed_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), index=True)

    # Relationships
    report = relationship("CrimeReport", back_populates="status_history")
    changer = relationship("User")

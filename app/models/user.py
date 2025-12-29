from sqlalchemy import Column, String, Boolean, DateTime, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum
from app.core.database import Base


class UserRole(str, enum.Enum):
    """User role enumeration"""
    USER = "USER"
    ADMIN = "ADMIN"
    SUPER_ADMIN = "SUPER_ADMIN"


class User(Base):
    """User model for authentication and authorization"""
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(SQLEnum(UserRole), default=UserRole.USER, nullable=False, index=True)
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    is_locked = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    # Relationships
    reports = relationship("CrimeReport", back_populates="creator", foreign_keys="CrimeReport.user_id")
    admin_requests = relationship("AdminRequest", back_populates="requester", foreign_keys="AdminRequest.user_id")
    approved_requests = relationship("AdminRequest", back_populates="approver", foreign_keys="AdminRequest.approved_by")
    audit_logs = relationship("AuditLog", back_populates="actor")
    sessions = relationship("Session", back_populates="user", cascade="all, delete-orphan")

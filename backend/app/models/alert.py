"""Alert model."""

from datetime import datetime
from sqlalchemy import Column, String, DateTime, BigInteger, Boolean, Enum, Index
from app.database import Base
import enum


class AlertSeverity(str, enum.Enum):
    """Alert severity enum."""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class Alert(Base):
    """System alert table."""
    
    __tablename__ = "alert"
    
    alert_id = Column(BigInteger, primary_key=True, autoincrement=True, comment="알림 ID")
    alert_type = Column(String(50), nullable=False, comment="알림 타입")
    severity = Column(
        Enum(AlertSeverity),
        nullable=False,
        default=AlertSeverity.INFO,
        comment="심각도"
    )
    title = Column(String(100), nullable=False, comment="제목")
    message = Column(String(500), nullable=False, comment="메시지")
    source_type = Column(String(30), nullable=True, comment="출처 타입")
    source_id = Column(String(50), nullable=True, comment="출처 ID")
    is_resolved = Column(Boolean, nullable=False, default=False, comment="해결 여부")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)
    
    __table_args__ = (
        Index("idx_alert_resolved_created", "is_resolved", "created_at"),
        Index("idx_alert_severity_created", "severity", "created_at"),
    )

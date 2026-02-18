"""Waybill and ScanLog models."""

from datetime import datetime
from sqlalchemy import Column, String, DateTime, Enum, BigInteger, Float, ForeignKey, Index
from sqlalchemy.orm import relationship
from app.database import Base
import enum


class LogisticsStatus(str, enum.Enum):
    """Logistics item status enum."""
    READY = "READY"
    MOVING = "MOVING"
    COMPLETED = "COMPLETED"
    ERROR = "ERROR"


class LogisticsItem(Base):
    """Main logistics item (waybill) table."""
    
    __tablename__ = "logistics_item"
    
    tracking_number = Column(String(50), primary_key=True, comment="운송장 번호")
    destination = Column(String(20), nullable=True, comment="목표 지역")
    image_file = Column(String(200), nullable=True, comment="OCR 원본 이미지 JSON 파일명")
    status = Column(
        Enum(LogisticsStatus),
        nullable=False,
        default=LogisticsStatus.READY,
        comment="상태"
    )
    created_at = Column(DateTime, nullable=False, default=datetime.now, comment="생성 시간")
    completed_at = Column(DateTime, nullable=True, comment="완료 시간")
    updated_at = Column(
        DateTime,
        nullable=False,
        default=datetime.now,
        onupdate=datetime.now,
        comment="최종 수정 시간"
    )
    
    # Relationships
    scan_logs = relationship("ScanLog", back_populates="logistics_item", cascade="all, delete-orphan")
    waybill_map = relationship("WaybillMap", back_populates="logistics_item", uselist=False, cascade="all, delete-orphan")
    
    __table_args__ = (
        Index("idx_li_created_at", "created_at"),
        Index("idx_li_status_created", "status", "created_at"),
        Index("idx_li_destination_created", "destination", "created_at"),
    )


class ScanLog(Base):
    """Scan log (OCR recognition history) table."""
    
    __tablename__ = "scan_log"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="로그 고유 ID")
    tracking_number = Column(
        String(50),
        ForeignKey("logistics_item.tracking_number", ondelete="CASCADE"),
        nullable=False,
        comment="운송장 번호"
    )
    camera_id = Column(String(20), nullable=False, comment="촬영한 카메라 ID")
    detected_destination = Column(String(20), nullable=True, comment="AI가 인식한 지역명")
    confidence_score = Column(Float, nullable=True, comment="AI 신뢰도(0~100)")
    scanned_at = Column(DateTime, nullable=False, default=datetime.now, comment="스캔 시간")
    
    # Relationships
    logistics_item = relationship("LogisticsItem", back_populates="scan_logs")
    
    __table_args__ = (
        Index("idx_sl_tracking_scanned", "tracking_number", "scanned_at"),
        Index("idx_sl_scanned_at", "scanned_at"),
    )


class WaybillMap(Base):
    """Waybill ID to tracking number mapping table."""
    
    __tablename__ = "waybill_map"
    
    waybill_id = Column(BigInteger, primary_key=True, autoincrement=True, comment="내부 운송장 ID")
    tracking_number = Column(
        String(50),
        ForeignKey("logistics_item.tracking_number", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        comment="운송장 번호"
    )
    
    # Relationships
    logistics_item = relationship("LogisticsItem", back_populates="waybill_map")

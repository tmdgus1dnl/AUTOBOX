"""Device status model."""

from datetime import datetime
from sqlalchemy import Column, String, DateTime, Integer, Float, Boolean, Enum, Index
from app.database import Base
import enum


class OperationStatus(str, enum.Enum):
    """Device operation status enum."""
    LOAD = "LOAD"
    TRANSPORT = "TRANSPORT"
    STOP = "STOP"


class DeviceStatus(Base):
    """Device status table."""
    
    __tablename__ = "device_status"
    
    device_id = Column(String(50), primary_key=True, comment="기기 ID")
    battery_level = Column(Integer, nullable=False, comment="배터리 잔량(0~100)")
    is_connected = Column(Boolean, nullable=False, comment="연결 상태")
    last_heartbeat = Column(DateTime, nullable=False, default=datetime.utcnow, comment="마지막 통신 시간")
    cpu_temperature = Column(Float, nullable=True, comment="CPU 온도")
    location = Column(String(50), nullable=True, comment="위치 정보")
    operation_status = Column(
        Enum(OperationStatus),
        nullable=False,
        default=OperationStatus.STOP,
        comment="동작 상태"
    )
    
    __table_args__ = (
        Index("idx_ds_heartbeat", "last_heartbeat"),
    )

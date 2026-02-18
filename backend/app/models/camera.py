"""Camera model."""

from datetime import datetime
from sqlalchemy import Column, String, DateTime, Enum, Index
from app.database import Base
import enum


class CameraType(str, enum.Enum):
    """Camera type enum."""
    LIVE = "live"
    CAPTURE = "capture"


class CameraStatus(str, enum.Enum):
    """Camera status enum."""
    ONLINE = "online"
    OFFLINE = "offline"


class Camera(Base):
    """Camera metadata and status table."""
    
    __tablename__ = "camera"
    
    camera_id = Column(String(20), primary_key=True, comment="카메라 ID")
    camera_name = Column(String(100), nullable=False, comment="카메라 이름")
    camera_type = Column(Enum(CameraType), nullable=False, comment="카메라 타입")
    location = Column(String(100), nullable=True, comment="설치 위치")
    ip_address = Column(String(50), nullable=True, comment="제조 설비(Jetson) IP 주소")
    relay_address = Column(String(50), nullable=True, comment="중계 장치(Raspberry Pi) IP 주소")
    stream_port = Column(String(10), nullable=True, comment="스트림 포트")
    stream_url = Column(String(255), nullable=True, comment="스트림 URL")
    status = Column(
        Enum(CameraStatus),
        nullable=False,
        default=CameraStatus.OFFLINE,
        comment="상태"
    )
    last_heartbeat = Column(DateTime, nullable=True, comment="마지막 하트비트")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        Index("idx_camera_status", "status"),
        Index("idx_camera_heartbeat", "last_heartbeat"),
    )

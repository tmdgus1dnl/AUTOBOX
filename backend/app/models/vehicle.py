"""Vehicle, Map, and Sensor models for real-time monitoring."""

from datetime import datetime
from sqlalchemy import Column, String, DateTime, Float, Integer, BigInteger, Text, Index
from sqlalchemy.dialects.mysql import JSON
from app.database import Base
import enum


class VehicleMode(str, enum.Enum):
    """Vehicle operation mode enum."""
    AUTO = "AUTO"
    MANUAL = "MANUAL"
    IDLE = "IDLE"
    EMERGENCY_STOP = "EMERGENCY_STOP"


class SensorStatusType(str, enum.Enum):
    """Sensor status type enum."""
    OK = "ok"
    WARNING = "warning"
    ERROR = "error"
    OFFLINE = "offline"


class VehiclePosition(Base):
    """Vehicle position tracking table."""
    
    __tablename__ = "vehicle_position"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="위치 레코드 ID")
    vehicle_id = Column(String(50), nullable=False, comment="차량 ID")
    x = Column(Float, nullable=False, comment="X 좌표")
    y = Column(Float, nullable=False, comment="Y 좌표")
    angle = Column(Float, nullable=False, default=0, comment="차량 방향 (0-360도)")
    speed = Column(Float, nullable=False, default=0, comment="속도 (km/h)")
    battery = Column(Integer, nullable=False, default=100, comment="배터리 레벨 (0-100)")
    mode = Column(String(20), nullable=False, default="IDLE", comment="운행 모드")
    updated_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        comment="마지막 업데이트 시간"
    )
    
    __table_args__ = (
        Index("idx_vp_vehicle_id", "vehicle_id"),
        Index("idx_vp_updated_at", "updated_at"),
    )


class MapData(Base):
    """Static map data table (waypoints, buildings, obstacles)."""
    
    __tablename__ = "map_data"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="맵 데이터 ID")
    map_id = Column(String(50), unique=True, nullable=False, comment="맵 식별자")
    name = Column(String(100), nullable=True, comment="맵 이름")
    waypoints = Column(JSON, nullable=True, comment="웨이포인트 배열 (JSON)")
    buildings = Column(JSON, nullable=True, comment="건물/장애물 배열 (JSON)")
    obstacles = Column(JSON, nullable=True, comment="동적 장애물 배열 (JSON)")
    roads = Column(JSON, nullable=True, comment="도로 경로 배열 (JSON)")
    zones = Column(JSON, nullable=True, comment="작업 구역 배열 (JSON)")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, comment="생성 시간")
    updated_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        comment="수정 시간"
    )
    
    __table_args__ = (
        Index("idx_md_map_id", "map_id"),
    )


class SensorStatus(Base):
    """Sensor status monitoring table."""
    
    __tablename__ = "sensor_status"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="센서 상태 ID")
    vehicle_id = Column(String(50), nullable=False, comment="차량 ID")
    sensor_name = Column(String(50), nullable=False, comment="센서 이름 (LIDAR, Camera, GPS, IMU)")
    sensor_type = Column(String(50), nullable=True, comment="센서 유형")
    status = Column(String(20), nullable=False, default="ok", comment="상태 (ok, warning, error, offline)")
    health = Column(Integer, nullable=True, default=100, comment="센서 상태 (0-100%)")
    value = Column(String(200), nullable=True, comment="센서 값 또는 설명")
    data = Column(JSON, nullable=True, comment="센서 상세 데이터 (JSON)")
    updated_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        comment="마지막 업데이트 시간"
    )
    
    __table_args__ = (
        Index("idx_ss_vehicle_id", "vehicle_id"),
        Index("idx_ss_vehicle_sensor", "vehicle_id", "sensor_name"),
        Index("idx_ss_updated_at", "updated_at"),
    )

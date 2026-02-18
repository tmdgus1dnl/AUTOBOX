"""Vehicle, Map, and Sensor schemas for real-time monitoring."""

from datetime import datetime
from typing import Optional, List, Any, Dict
from pydantic import BaseModel, Field


# ============== Vehicle Position Schemas ==============

class VehiclePositionData(BaseModel):
    """Vehicle position data schema (matches frontend expectation)."""
    x: float = Field(..., description="X 좌표")
    y: float = Field(..., description="Y 좌표")
    angle: float = Field(default=0, description="차량 방향 (0-360도)")
    speed: float = Field(default=0, description="속도 (km/h)")
    battery: int = Field(default=100, ge=0, le=100, description="배터리 레벨 (0-100)")
    mode: str = Field(default="IDLE", description="운행 모드 (AUTO, MANUAL, IDLE)")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="타임스탬프")

    class Config:
        from_attributes = True


class VehiclePositionResponse(BaseModel):
    """Full response for vehicle position."""
    success: bool = True
    data: VehiclePositionData


# ============== Map Data Schemas ==============

class Waypoint(BaseModel):
    """Waypoint schema."""
    id: int = Field(..., description="웨이포인트 ID")
    label: str = Field(..., description="라벨 (A, B, C, D 등)")
    x: float = Field(..., description="X 좌표")
    y: float = Field(..., description="Y 좌표")
    color: str = Field(default="#10b981", description="표시 색상")
    type: Optional[str] = Field(default=None, description="유형 (pickup, dropoff, charging, parking)")


class Building(BaseModel):
    """Building/obstacle schema."""
    id: int = Field(..., description="건물 ID")
    x: float = Field(..., description="X 좌표")
    y: float = Field(..., description="Y 좌표")
    width: float = Field(..., description="너비")
    height: float = Field(..., description="높이")
    type: str = Field(default="building", description="유형 (building, obstacle 등)")


class Road(BaseModel):
    """Road path schema."""
    id: str = Field(..., description="도로 ID")
    type: str = Field(default="path", description="도로 유형")
    points: List[Dict[str, float]] = Field(default=[], description="도로 좌표 포인트 배열")
    width: float = Field(default=8, description="도로 폭")


class Zone(BaseModel):
    """Zone/area schema."""
    id: str = Field(..., description="구역 ID")
    name: str = Field(..., description="구역 이름")
    type: str = Field(default="work_area", description="구역 유형")
    polygon: List[Dict[str, float]] = Field(default=[], description="구역 경계 좌표")


class MapDataContent(BaseModel):
    """Map data content schema (matches frontend expectation)."""
    map_id: Optional[str] = Field(default="default", description="맵 ID")
    waypoints: List[Waypoint] = Field(default=[], description="웨이포인트 배열")
    buildings: List[Building] = Field(default=[], description="건물 배열")
    obstacles: List[Dict[str, Any]] = Field(default=[], description="장애물 배열")
    roads: Optional[List[Road]] = Field(default=[], description="도로 배열")
    zones: Optional[List[Zone]] = Field(default=[], description="구역 배열")


class MapDataResponse(BaseModel):
    """Full response for map data."""
    success: bool = True
    data: MapDataContent


# ============== Sensor Status Schemas ==============

class SensorInfo(BaseModel):
    """Individual sensor info schema (matches frontend expectation)."""
    name: str = Field(..., description="센서 이름 (LIDAR, Camera, GPS, IMU)")
    status: str = Field(default="ok", description="상태 (ok, warning, error, offline)")
    value: str = Field(default="정상", description="센서 값 또는 설명")
    type: Optional[str] = Field(default=None, description="센서 유형")
    health: Optional[int] = Field(default=100, ge=0, le=100, description="센서 상태 (0-100%)")
    data: Optional[Dict[str, Any]] = Field(default=None, description="센서 상세 데이터")
    last_update: Optional[datetime] = Field(default=None, description="마지막 업데이트 시간")

    class Config:
        from_attributes = True


class SensorStatusData(BaseModel):
    """Sensor status data schema (matches frontend expectation)."""
    sensors: List[SensorInfo] = Field(default=[], description="센서 상태 배열")
    vehicle_id: Optional[str] = Field(default=None, description="차량 ID")
    timestamp: Optional[datetime] = Field(default_factory=datetime.utcnow, description="타임스탬프")


class SensorStatusResponse(BaseModel):
    """Full response for sensor status."""
    success: bool = True
    data: SensorStatusData


# ============== Update Request Schemas (for MQTT/internal use) ==============

class VehiclePositionUpdateRequest(BaseModel):
    """Request schema for updating vehicle position."""
    vehicle_id: str = Field(..., description="차량 ID")
    x: float = Field(..., description="X 좌표")
    y: float = Field(..., description="Y 좌표")
    angle: Optional[float] = Field(default=0, description="차량 방향")
    speed: Optional[float] = Field(default=0, description="속도")
    battery: Optional[int] = Field(default=100, description="배터리 레벨")
    mode: Optional[str] = Field(default="IDLE", description="운행 모드")


class SensorStatusUpdateRequest(BaseModel):
    """Request schema for updating sensor status."""
    vehicle_id: str = Field(..., description="차량 ID")
    sensor_name: str = Field(..., description="센서 이름")
    status: str = Field(default="ok", description="상태")
    value: Optional[str] = Field(default=None, description="센서 값")
    health: Optional[int] = Field(default=100, description="센서 상태")
    data: Optional[Dict[str, Any]] = Field(default=None, description="상세 데이터")


# ============== Command Schemas (for sending commands to Raspberry Pi) ==============

class BoxCountCommandRequest(BaseModel):
    """Request schema for sending box count command to Raspberry Pi."""
    box_count: int = Field(..., ge=1, description="처리할 박스 개수")
    vehicle_id: Optional[str] = Field(default="AGV-001", description="차량 ID")
    priority: Optional[str] = Field(default="normal", description="우선순위 (high, normal, low)")


class BoxCountCommandData(BaseModel):
    """Response data for box count command."""
    command_id: str = Field(..., description="명령 ID")
    box_count: int = Field(..., description="전송된 박스 개수")
    vehicle_id: str = Field(..., description="대상 차량 ID")
    status: str = Field(default="sent", description="명령 상태 (sent, received, processing, completed)")
    sent_at: datetime = Field(default_factory=datetime.utcnow, description="전송 시간")


class BoxCountCommandResponse(BaseModel):
    """Full response for box count command."""
    success: bool = True
    data: BoxCountCommandData
    message: str = "명령이 전송되었습니다."


class VehicleCommandRequest(BaseModel):
    """General vehicle command request schema."""
    vehicle_id: Optional[str] = Field(default="AGV-001", description="차량 ID")
    command: str = Field(..., description="명령 유형 (start, stop, pause, resume, emergency_stop)")
    parameters: Optional[Dict[str, Any]] = Field(default=None, description="추가 파라미터")


class VehicleCommandResponse(BaseModel):
    """Response for vehicle command."""
    success: bool = True
    data: Dict[str, Any]
    message: str = "명령이 전송되었습니다."

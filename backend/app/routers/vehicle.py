"""Vehicle, Map, and Sensor API routes for real-time monitoring."""

from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.database import get_db
from app.models.vehicle import VehiclePosition, MapData, SensorStatus
from app.schemas.vehicle import (
    VehiclePositionData,
    VehiclePositionResponse,
    VehiclePositionUpdateRequest,
    MapDataContent,
    MapDataResponse,
    Waypoint,
    Building,
    SensorInfo,
    SensorStatusData,
    SensorStatusResponse,
    SensorStatusUpdateRequest,
    BoxCountCommandRequest,
    BoxCountCommandData,
    BoxCountCommandResponse,
    VehicleCommandRequest,
    VehicleCommandResponse,
)
from app.services.websocket import manager
from app.services.mqtt import mqtt_service
import uuid

router = APIRouter(tags=["차량/맵/센서"])


# ============== Default Data for Initial Setup ==============

DEFAULT_WAYPOINTS = [
    {"id": 1, "label": "A", "x": 200, "y": 300, "color": "#10b981", "type": "pickup"},
    {"id": 2, "label": "B", "x": 500, "y": 200, "color": "#f59e0b", "type": "dropoff"},
    {"id": 3, "label": "C", "x": 750, "y": 300, "color": "#ef4444", "type": "dropoff"},
    {"id": 4, "label": "D", "x": 500, "y": 600, "color": "#3b82f6", "type": "charging"},
]

DEFAULT_BUILDINGS = [
    {"id": 1, "x": 150, "y": 150, "width": 100, "height": 80, "type": "building"},
    {"id": 2, "x": 650, "y": 150, "width": 120, "height": 100, "type": "building"},
    {"id": 3, "x": 150, "y": 450, "width": 90, "height": 110, "type": "building"},
    {"id": 4, "x": 700, "y": 450, "width": 100, "height": 90, "type": "building"},
]

DEFAULT_SENSORS = [
    {"name": "LIDAR", "status": "ok", "value": "정상 (360°)", "type": "lidar", "health": 100},
    {"name": "Camera", "status": "ok", "value": "정상 (1080p)", "type": "rgb_camera", "health": 100},
    {"name": "GPS", "status": "ok", "value": "정확도 ±2m", "type": "gnss", "health": 95},
    {"name": "IMU", "status": "ok", "value": "정상", "type": "inertial", "health": 100},
]


# ============== RC State API (Read from logs) ==============

@router.get("/vehicle/rc-state")
async def get_rc_state():
    """
    RC-001: RC 상태 조회 (로그 파일에서 읽기).
    
    MQTT를 통해 수신된 최신 RC 상태를 로그 파일에서 읽어 반환합니다.
    0.5초마다 업데이트되는 rc_state_latest.json 파일에서 데이터를 읽습니다.
    """
    import os
    import json
    
    log_file = "./logs/rc_state_latest.json"
    
    # 파일이 없으면 기본값 반환
    if not os.path.exists(log_file):
        return {
            "success": True,
            "connected": False,
            "data": {
                "device_id": "rc1",
                "speed": 0,
                "state": "IDLE",
                "x": 0.0,
                "y": 0.0,
                "theta": 0.0,
                "path": "",
                "remain_dist": 0.0,
                "remain_time": 0
            },
            "message": "로그 파일이 아직 생성되지 않았습니다."
        }
    
    try:
        with open(log_file, "r", encoding="utf-8") as f:
            log_data = json.load(f)
        
        # saved_at 타임스탬프 확인하여 연결 상태 판단 (5초 이내면 Connected)
        saved_at = log_data.get("saved_at", "")
        is_connected = False
        
        if saved_at:
            from datetime import datetime, timedelta
            try:
                saved_time = datetime.fromisoformat(saved_at)
                is_connected = (datetime.now() - saved_time) < timedelta(seconds=5)
            except:
                pass
        
        rc_data = log_data.get("data", {})
        
        return {
            "success": True,
            "connected": is_connected,
            "data": {
                "device_id": rc_data.get("device_id", "rc1"),
                "speed": abs(rc_data.get("speed", 0)),  # 절대값으로 변환
                "state": rc_data.get("state", "IDLE"),
                "x": rc_data.get("x", 0.0),
                "y": rc_data.get("y", 0.0),
                "theta": rc_data.get("theta", 0.0),
                "path": rc_data.get("path", ""),
                "remain_dist": rc_data.get("remain_dist", 0.0),
                "remain_time": rc_data.get("remain_time", 0)
            },
            "saved_at": saved_at,
            "received_at": log_data.get("received_at", "")
        }
        
    except Exception as e:
        return {
            "success": False,
            "connected": False,
            "data": None,
            "message": f"로그 파일 읽기 오류: {str(e)}"
        }


# ============== Vehicle Position API ==============

@router.get("/vehicle/position", response_model=VehiclePositionResponse)
async def get_vehicle_position(
    vehicle_id: Optional[str] = Query(default=None, description="차량 ID (미지정시 최신 데이터)"),
    db: Session = Depends(get_db)
):
    """
    VH-001: 차량 위치 정보 조회.
    
    실시간으로 차량의 위치, 방향, 속도, 배터리 정보를 반환합니다.
    DB에 데이터가 없으면 기본값을 반환합니다.
    """
    query = db.query(VehiclePosition)
    
    if vehicle_id:
        query = query.filter(VehiclePosition.vehicle_id == vehicle_id)
    
    # Get the most recent position
    position = query.order_by(desc(VehiclePosition.updated_at)).first()
    
    if not position:
        # Return default position if no data
        return VehiclePositionResponse(
            success=True,
            data=VehiclePositionData(
                x=450.0,
                y=350.0,
                angle=0.0,
                speed=0.0,
                battery=100,
                mode="IDLE",
                timestamp=datetime.utcnow()
            )
        )
    
    return VehiclePositionResponse(
        success=True,
        data=VehiclePositionData(
            x=position.x,
            y=position.y,
            angle=position.angle,
            speed=position.speed,
            battery=position.battery,
            mode=position.mode,
            timestamp=position.updated_at
        )
    )


@router.put("/vehicle/position", response_model=VehiclePositionResponse)
async def update_vehicle_position(
    request: VehiclePositionUpdateRequest,
    db: Session = Depends(get_db)
):
    """
    VH-002: 차량 위치 업데이트 (UPSERT).
    
    MQTT 또는 라즈베리파이에서 차량 위치를 업데이트할 때 사용합니다.
    """
    # Check if position exists for this vehicle
    position = db.query(VehiclePosition).filter(
        VehiclePosition.vehicle_id == request.vehicle_id
    ).first()
    
    now = datetime.utcnow()
    
    if position:
        # Update existing
        position.x = request.x
        position.y = request.y
        position.angle = request.angle or 0
        position.speed = request.speed or 0
        position.battery = request.battery or 100
        position.mode = request.mode or "IDLE"
        position.updated_at = now
    else:
        # Create new
        position = VehiclePosition(
            vehicle_id=request.vehicle_id,
            x=request.x,
            y=request.y,
            angle=request.angle or 0,
            speed=request.speed or 0,
            battery=request.battery or 100,
            mode=request.mode or "IDLE",
            updated_at=now
        )
        db.add(position)
    
    db.commit()
    db.refresh(position)
    
    # Broadcast via WebSocket
    await manager.broadcast({
        "type": "vehicle_position",
        "data": {
            "vehicle_id": position.vehicle_id,
            "x": position.x,
            "y": position.y,
            "angle": position.angle,
            "speed": position.speed,
            "battery": position.battery,
            "mode": position.mode,
            "timestamp": now.isoformat()
        }
    })
    
    return VehiclePositionResponse(
        success=True,
        data=VehiclePositionData(
            x=position.x,
            y=position.y,
            angle=position.angle,
            speed=position.speed,
            battery=position.battery,
            mode=position.mode,
            timestamp=position.updated_at
        )
    )


# ============== Map Data API ==============

@router.get("/map/data", response_model=MapDataResponse)
async def get_map_data(
    map_id: Optional[str] = Query(default=None, description="맵 ID (미지정시 기본 맵)"),
    db: Session = Depends(get_db)
):
    """
    MAP-001: 맵 데이터 조회.
    
    웨이포인트, 건물, 장애물 등 정적 맵 정보를 반환합니다.
    DB에 데이터가 없으면 기본 맵 데이터를 반환합니다.
    """
    query = db.query(MapData)
    
    if map_id:
        query = query.filter(MapData.map_id == map_id)
    
    map_data = query.first()
    
    if not map_data:
        # Return default map data
        return MapDataResponse(
            success=True,
            data=MapDataContent(
                map_id="default",
                waypoints=[Waypoint(**wp) for wp in DEFAULT_WAYPOINTS],
                buildings=[Building(**b) for b in DEFAULT_BUILDINGS],
                obstacles=[],
                roads=[],
                zones=[]
            )
        )
    
    # Parse JSON data from database
    waypoints = [Waypoint(**wp) for wp in (map_data.waypoints or [])]
    buildings = [Building(**b) for b in (map_data.buildings or [])]
    
    return MapDataResponse(
        success=True,
        data=MapDataContent(
            map_id=map_data.map_id,
            waypoints=waypoints,
            buildings=buildings,
            obstacles=map_data.obstacles or [],
            roads=map_data.roads or [],
            zones=map_data.zones or []
        )
    )


# ============== Sensor Status API ==============

@router.get("/sensors/status", response_model=SensorStatusResponse)
async def get_sensor_status(
    vehicle_id: Optional[str] = Query(default=None, description="차량 ID (미지정시 모든 센서)"),
    db: Session = Depends(get_db)
):
    """
    SEN-001: 센서 상태 조회.
    
    LIDAR, Camera, GPS, IMU 등 센서의 실시간 상태를 반환합니다.
    DB에 데이터가 없으면 기본 센서 상태를 반환합니다.
    """
    query = db.query(SensorStatus)
    
    if vehicle_id:
        query = query.filter(SensorStatus.vehicle_id == vehicle_id)
    
    sensors = query.order_by(desc(SensorStatus.updated_at)).all()
    
    if not sensors:
        # Return default sensor status
        return SensorStatusResponse(
            success=True,
            data=SensorStatusData(
                sensors=[SensorInfo(**s) for s in DEFAULT_SENSORS],
                vehicle_id=vehicle_id,
                timestamp=datetime.utcnow()
            )
        )
    
    # Group by sensor_name to get unique sensors
    sensor_map = {}
    for sensor in sensors:
        if sensor.sensor_name not in sensor_map:
            sensor_map[sensor.sensor_name] = SensorInfo(
                name=sensor.sensor_name,
                status=sensor.status,
                value=sensor.value or "정상",
                type=sensor.sensor_type,
                health=sensor.health,
                data=sensor.data,
                last_update=sensor.updated_at
            )
    
    return SensorStatusResponse(
        success=True,
        data=SensorStatusData(
            sensors=list(sensor_map.values()),
            vehicle_id=vehicle_id,
            timestamp=datetime.utcnow()
        )
    )


@router.put("/sensors/status", response_model=SensorStatusResponse)
async def update_sensor_status(
    request: SensorStatusUpdateRequest,
    db: Session = Depends(get_db)
):
    """
    SEN-002: 센서 상태 업데이트 (UPSERT).
    
    MQTT 또는 라즈베리파이에서 센서 상태를 업데이트할 때 사용합니다.
    """
    # Check if sensor status exists
    sensor = db.query(SensorStatus).filter(
        SensorStatus.vehicle_id == request.vehicle_id,
        SensorStatus.sensor_name == request.sensor_name
    ).first()
    
    now = datetime.utcnow()
    
    if sensor:
        # Update existing
        sensor.status = request.status
        sensor.value = request.value
        sensor.health = request.health or 100
        sensor.data = request.data
        sensor.updated_at = now
    else:
        # Create new
        sensor = SensorStatus(
            vehicle_id=request.vehicle_id,
            sensor_name=request.sensor_name,
            status=request.status,
            value=request.value,
            health=request.health or 100,
            data=request.data,
            updated_at=now
        )
        db.add(sensor)
    
    db.commit()
    db.refresh(sensor)
    
    # Broadcast via WebSocket
    await manager.broadcast({
        "type": "sensor_status",
        "data": {
            "vehicle_id": sensor.vehicle_id,
            "sensor_name": sensor.sensor_name,
            "status": sensor.status,
            "value": sensor.value,
            "health": sensor.health,
            "timestamp": now.isoformat()
        }
    })
    
    # Return updated sensor status
    return SensorStatusResponse(
        success=True,
        data=SensorStatusData(
            sensors=[SensorInfo(
                name=sensor.sensor_name,
                status=sensor.status,
                value=sensor.value or "정상",
                health=sensor.health,
                data=sensor.data,
                last_update=sensor.updated_at
            )],
            vehicle_id=request.vehicle_id,
            timestamp=now
        )
    )


# ============== Command API (Send commands to Raspberry Pi via MQTT) ==============

@router.post("/vehicle/command/box-count", response_model=BoxCountCommandResponse)
async def send_box_count_command(request: BoxCountCommandRequest):
    """
    CMD-001: 박스 개수 명령 전송.
    
    프론트엔드에서 입력받은 박스 개수를 MQTT를 통해 라즈베리파이로 전송.
    라즈베리파이는 'autobox/command/box-count' 토픽을 구독하여 명령을 수신.
    """
    command_id = f"CMD-{uuid.uuid4().hex[:8].upper()}"
    now = datetime.utcnow()
    
    # MQTT 메시지 페이로드 구성
    payload = {
        "command_id": command_id,
        "command_type": "box_count",
        "box_count": request.box_count,
        "vehicle_id": request.vehicle_id,
        "priority": request.priority,
        "timestamp": now.isoformat()
    }
    
    # MQTT로 라즈베리파이에 명령 전송
    mqtt_topic = "command/box-count"
    success = mqtt_service.publish(mqtt_topic, payload, qos=1)
    
    if not success:
        # 여기에 알맞느 에러메시지
        raise HTTPException(
            status_code=500,
            detail="명령을 라즈베리파이에 전송하지 못했습니다. MQTT 연결 상태를 확인해주세요."
        )
    
    # WebSocket으로도 브로드캐스트 (실시간 UI 업데이트용)
    await manager.broadcast({
        "type": "command_sent",
        "data": payload
    })
    
    return BoxCountCommandResponse(
        success=True,
        data=BoxCountCommandData(
            command_id=command_id,
            box_count=request.box_count,
            vehicle_id=request.vehicle_id,
            status="sent",
            sent_at=now
        ),
        message=f"박스 개수 {request.box_count}개 명령이 전송되었습니다."
    )


@router.post("/vehicle/command", response_model=VehicleCommandResponse)
async def send_vehicle_command(request: VehicleCommandRequest):
    """
    CMD-002: 차량 제어 명령 전송.
    
    차량의 시작, 정지, 일시정지 등 제어 명령을 MQTT를 통해 라즈베리파이로 전송합니다.
    라즈베리파이는 'autobox/command/vehicle' 토픽을 구독하여 명령을 수신합니다.
    """
    command_id = f"CMD-{uuid.uuid4().hex[:8].upper()}"
    now = datetime.utcnow()
    
    # 허용된 명령 검증
    allowed_commands = ["start", "stop", "pause", "resume", "emergency_stop", "reset"]
    if request.command not in allowed_commands:
        raise HTTPException(
            status_code=400,
            detail=f"허용되지 않는 명령입니다. 허용 명령: {', '.join(allowed_commands)}"
        )
    
    # MQTT 메시지 페이로드 구성
    payload = {
        "command_id": command_id,
        "command_type": "vehicle_control",
        "command": request.command,
        "vehicle_id": request.vehicle_id,
        "parameters": request.parameters or {},
        "timestamp": now.isoformat()
    }
    
    # MQTT로 라즈베리파이에 명령 전송
    mqtt_topic = "command/vehicle"
    mqtt_service.publish(mqtt_topic, payload, qos=1)
    
    # WebSocket으로도 브로드캐스트
    await manager.broadcast({
        "type": "command_sent",
        "data": payload
    })
    
    return VehicleCommandResponse(
        success=True,
        data={
            "command_id": command_id,
            "command": request.command,
            "vehicle_id": request.vehicle_id,
            "status": "sent",
            "sent_at": now.isoformat()
        },
        message=f"'{request.command}' 명령이 전송되었습니다."
    )

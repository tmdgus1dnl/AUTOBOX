"""System status API routes."""

from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.device import DeviceStatus, OperationStatus
from app.schemas.device import DeviceStatusOut, DeviceStatusUpdateRequest
from app.services.websocket import manager

router = APIRouter(prefix="/system", tags=["시스템"])


@router.get("/status", response_model=dict)
async def get_system_status(db: Session = Depends(get_db)):
    """SYS-001: 시스템 상태 조회."""
    # Get the first device (or a specific one)
    device = db.query(DeviceStatus).first()
    
    if not device:
        # Return default status if no device registered
        return {
            "success": True,
            "data": {
                "device_id": None,
                "battery_level": 0,
                "is_connected": False,
                "operation_status": "STOP",
                "last_heartbeat": None
            }
        }
    
    return {
        "success": True,
        "data": DeviceStatusOut(
            device_id=device.device_id,
            battery_level=device.battery_level,
            is_connected=device.is_connected,
            operation_status=device.operation_status,
            last_heartbeat=device.last_heartbeat
        )
    }


@router.put("/status", response_model=dict)
async def update_system_status(
    request: DeviceStatusUpdateRequest,
    db: Session = Depends(get_db)
):
    """SYS-002: 시스템 상태 업데이트 (UPSERT)."""
    device = db.query(DeviceStatus).filter(
        DeviceStatus.device_id == request.device_id
    ).first()
    
    now = datetime.now()
    
    if device:
        # Update existing
        device.battery_level = request.battery_level
        device.is_connected = request.is_connected
        device.operation_status = request.operation_status
        device.cpu_temperature = request.cpu_temperature
        device.location = request.location
        device.last_heartbeat = now
    else:
        # Create new
        device = DeviceStatus(
            device_id=request.device_id,
            battery_level=request.battery_level,
            is_connected=request.is_connected,
            operation_status=request.operation_status,
            cpu_temperature=request.cpu_temperature,
            location=request.location,
            last_heartbeat=now
        )
        db.add(device)
    
    db.commit()
    db.refresh(device)
    
    # Broadcast via WebSocket
    await manager.broadcast({
        "type": "system_status",
        "data": {
            "device_id": device.device_id,
            "battery_level": device.battery_level,
            "is_connected": device.is_connected,
            "operation_status": device.operation_status.value
        }
    })
    
    return {
        "success": True,
        "data": DeviceStatusOut(
            device_id=device.device_id,
            battery_level=device.battery_level,
            is_connected=device.is_connected,
            operation_status=device.operation_status,
            last_heartbeat=device.last_heartbeat
        )
    }

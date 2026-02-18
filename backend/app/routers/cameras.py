"""Camera API routes."""

from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.database import get_db
from app.models.camera import Camera, CameraStatus
from app.schemas.camera import CameraOut, CameraStatusRequest

router = APIRouter(prefix="/cameras", tags=["카메라"])


@router.get("", response_model=dict)
async def list_cameras(db: Session = Depends(get_db)):
    """SYS-003: 카메라 목록 조회."""
    cameras = db.query(Camera).all()
    
    return {
        "success": True,
        "data": [
            CameraOut(
                camera_id=c.camera_id,
                camera_name=c.camera_name,
                camera_type=c.camera_type,
                location=c.location,
                ip_address=c.ip_address,
                relay_address=c.relay_address,
                stream_port=c.stream_port,
                stream_url=c.stream_url,
                status=c.status,
                last_heartbeat=c.last_heartbeat
            )
            for c in cameras
        ]
    }


@router.put("/{camera_id}/status", response_model=dict)
async def update_camera_status(
    camera_id: str,
    request: CameraStatusRequest,
    db: Session = Depends(get_db)
):
    """SYS-004: 카메라 상태 업데이트."""
    camera = db.query(Camera).filter(Camera.camera_id == camera_id).first()
    if not camera:
        raise HTTPException(status_code=404, detail={
            "code": "CAMERA_NOT_FOUND",
            "message": "카메라를 찾을 수 없습니다"
        })
    
    camera.status = request.status
    camera.last_heartbeat = datetime.now()
    camera.updated_at = datetime.now()
    db.commit()
    
    return {
        "success": True,
        "data": CameraOut(
            camera_id=camera.camera_id,
            camera_name=camera.camera_name,
            camera_type=camera.camera_type,
            location=camera.location,
            ip_address=camera.ip_address,
            relay_address=camera.relay_address,
            stream_port=camera.stream_port,
            stream_url=camera.stream_url,
            status=camera.status,
            last_heartbeat=camera.last_heartbeat
        )
    }

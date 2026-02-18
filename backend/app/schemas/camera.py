"""Camera schemas."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from app.models.camera import CameraType, CameraStatus


class CameraOut(BaseModel):
    """Camera output schema."""
    camera_id: str
    camera_name: str
    camera_type: CameraType
    location: Optional[str] = None
    ip_address: Optional[str] = None
    relay_address: Optional[str] = None
    stream_port: Optional[str] = None
    stream_url: Optional[str] = None
    status: CameraStatus
    last_heartbeat: Optional[datetime] = None

    class Config:
        from_attributes = True


class CameraStatusRequest(BaseModel):
    """Request schema for updating camera status."""
    status: CameraStatus


class LatestScanLogData(BaseModel):
    """Latest scan log data."""
    tracking_number: str
    camera_id: str
    detected_destination: Optional[str] = None
    confidence_score: Optional[float] = None
    scanned_at: datetime

    class Config:
        from_attributes = True


class LatestRecognitionData(BaseModel):
    """Latest recognition data wrapper."""
    scan_log: Optional[LatestScanLogData] = None


class LatestRecognitionResponse(BaseModel):
    """Full response for latest recognition."""
    success: bool = True
    data: LatestRecognitionData

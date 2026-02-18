"""Device status schemas."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from app.models.device import OperationStatus


class DeviceStatusOut(BaseModel):
    """Device status output schema."""
    device_id: str
    battery_level: int
    is_connected: bool
    operation_status: OperationStatus
    last_heartbeat: datetime

    class Config:
        from_attributes = True


class DeviceStatusUpdateRequest(BaseModel):
    """Request schema for updating device status."""
    device_id: str
    battery_level: int = Field(ge=0, le=100)
    is_connected: bool
    operation_status: OperationStatus
    cpu_temperature: Optional[float] = None
    location: Optional[str] = None

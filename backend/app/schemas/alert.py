"""Alert schemas."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from app.models.alert import AlertSeverity


class AlertOut(BaseModel):
    """Alert output schema."""
    alert_id: int
    alert_type: str
    severity: AlertSeverity
    title: str
    message: str
    source_type: Optional[str] = None
    source_id: Optional[str] = None
    is_resolved: bool
    created_at: datetime
    resolved_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class AlertCreateRequest(BaseModel):
    """Request schema for creating alert."""
    alert_type: str
    severity: AlertSeverity = AlertSeverity.INFO
    title: str
    message: str
    source_type: Optional[str] = None
    source_id: Optional[str] = None

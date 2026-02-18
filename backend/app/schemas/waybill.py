"""Waybill schemas."""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field
from app.models.waybill import LogisticsStatus


# Request schemas
class WaybillScanRequest(BaseModel):
    """Request schema for waybill scan start."""
    camera_id: str


class RecognitionRequest(BaseModel):
    """Request schema for OCR recognition result."""
    recognized_text: str
    destination: str
    confidence_score: float = Field(ge=0, le=100)
    camera_id: str


class ErrorRequest(BaseModel):
    """Request schema for error status."""
    error_reason: str


# Response data schemas
class WaybillScanData(BaseModel):
    """Response data for waybill scan."""
    waybill_id: int
    tracking_number: str
    status: LogisticsStatus
    created_at: datetime

    class Config:
        from_attributes = True


class RecognitionData(BaseModel):
    """Response data for recognition result."""
    waybill_id: int
    tracking_number: str
    status: LogisticsStatus
    destination: str
    confidence_score: float
    scanned_at: datetime

    class Config:
        from_attributes = True


class StartSortingData(BaseModel):
    """Response data for start sorting."""
    waybill_id: int
    tracking_number: str
    status: LogisticsStatus
    updated_at: datetime

    class Config:
        from_attributes = True


class CompleteData(BaseModel):
    """Response data for completion."""
    waybill_id: int
    tracking_number: str
    status: LogisticsStatus
    completed_at: datetime
    process_time_sec: int

    class Config:
        from_attributes = True


class ErrorStatusData(BaseModel):
    """Response data for error status."""
    waybill_id: int
    tracking_number: str
    status: LogisticsStatus
    alert_id: int
    updated_at: datetime

    class Config:
        from_attributes = True


# List schemas
class WaybillListItem(BaseModel):
    """Waybill list item schema."""
    waybill_id: int
    tracking_number: str
    destination: Optional[str] = None
    status: LogisticsStatus
    created_at: datetime
    completed_at: Optional[datetime] = None
    process_time_sec: Optional[int] = None

    class Config:
        from_attributes = True


class WaybillListData(BaseModel):
    """Waybill list data with pagination."""
    items: List[WaybillListItem]
    total: int
    page: int
    size: int
    total_pages: int


# Detail schemas
class ScanLogOut(BaseModel):
    """Scan log output schema."""
    camera_id: str
    detected_destination: Optional[str] = None
    confidence_score: Optional[float] = None
    scanned_at: datetime

    class Config:
        from_attributes = True


class WaybillDetailItem(BaseModel):
    """Waybill detail item schema."""
    waybill_id: int
    tracking_number: str
    destination: Optional[str] = None
    status: LogisticsStatus
    created_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class WaybillDetailData(BaseModel):
    """Waybill detail data schema."""
    item: WaybillDetailItem
    scan_logs: List[ScanLogOut]


# Full response schemas (for type hints)
class WaybillScanResponse(BaseModel):
    """Full response for waybill scan."""
    success: bool = True
    data: WaybillScanData


class RecognitionResponse(BaseModel):
    """Full response for recognition."""
    success: bool = True
    data: RecognitionData


class StartSortingResponse(BaseModel):
    """Full response for start sorting."""
    success: bool = True
    data: StartSortingData


class CompleteResponse(BaseModel):
    """Full response for completion."""
    success: bool = True
    data: CompleteData


class ErrorStatusResponse(BaseModel):
    """Full response for error status."""
    success: bool = True
    data: ErrorStatusData


class WaybillListResponse(BaseModel):
    """Full response for waybill list."""
    success: bool = True
    data: WaybillListData


class WaybillDetailResponse(BaseModel):
    """Full response for waybill detail."""
    success: bool = True
    data: WaybillDetailData

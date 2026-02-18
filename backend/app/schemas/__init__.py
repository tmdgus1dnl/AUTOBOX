"""Pydantic schemas."""

from app.schemas.common import SuccessResponse, ErrorResponse, ErrorDetail
from app.schemas.waybill import (
    WaybillScanRequest,
    WaybillScanResponse,
    RecognitionRequest,
    RecognitionResponse,
    StartSortingResponse,
    CompleteResponse,
    ErrorRequest,
    ErrorStatusResponse,
    WaybillListItem,
    WaybillListResponse,
    WaybillDetailResponse,
    ScanLogOut,
)
from app.schemas.region import RegionOut, RegionCreateRequest, RegionStatusRequest
from app.schemas.device import DeviceStatusOut, DeviceStatusUpdateRequest
from app.schemas.alert import AlertOut, AlertCreateRequest
from app.schemas.camera import CameraOut, CameraStatusRequest, LatestRecognitionResponse
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

__all__ = [
    # Common
    "SuccessResponse",
    "ErrorResponse",
    "ErrorDetail",
    # Waybill
    "WaybillScanRequest",
    "WaybillScanResponse",
    "RecognitionRequest",
    "RecognitionResponse",
    "StartSortingResponse",
    "CompleteResponse",
    "ErrorRequest",
    "ErrorStatusResponse",
    "WaybillListItem",
    "WaybillListResponse",
    "WaybillDetailResponse",
    "ScanLogOut",
    # Region
    "RegionOut",
    "RegionCreateRequest",
    "RegionStatusRequest",
    # Device
    "DeviceStatusOut",
    "DeviceStatusUpdateRequest",
    # Alert
    "AlertOut",
    "AlertCreateRequest",
    # Camera
    "CameraOut",
    "CameraStatusRequest",
    "LatestRecognitionResponse",
    # Vehicle
    "VehiclePositionData",
    "VehiclePositionResponse",
    "VehiclePositionUpdateRequest",
    "MapDataContent",
    "MapDataResponse",
    "Waypoint",
    "Building",
    "SensorInfo",
    "SensorStatusData",
    "SensorStatusResponse",
    "SensorStatusUpdateRequest",
    # Commands
    "BoxCountCommandRequest",
    "BoxCountCommandData",
    "BoxCountCommandResponse",
    "VehicleCommandRequest",
    "VehicleCommandResponse",
]

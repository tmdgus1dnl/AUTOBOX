"""API Routers."""

from app.routers.waybills import router as waybills_router
from app.routers.regions import router as regions_router
from app.routers.system import router as system_router
from app.routers.alerts import router as alerts_router
from app.routers.stats import router as stats_router
from app.routers.recognition import router as recognition_router
from app.routers.cameras import router as cameras_router
from app.routers.websocket import router as websocket_router
from app.routers.vehicle import router as vehicle_router
from app.routers.ocr import router as ocr_router

__all__ = [
    "waybills_router",
    "regions_router",
    "system_router",
    "alerts_router",
    "stats_router",
    "recognition_router",
    "cameras_router",
    "websocket_router",
    "vehicle_router",
    "ocr_router",
]

"""AutoBox FastAPI Application."""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.database import engine, Base
from app.routers import (
    waybills_router,
    regions_router,
    system_router,
    alerts_router,
    stats_router,
    recognition_router,
    cameras_router,
    vehicle_router,
    ocr_router,
)
from app.routers.websocket import router as websocket_router
from app.routers.frontend_compat import router as frontend_compat_router
from app.services.mqtt import mqtt_service, register_default_handlers
from app.services.ocr_service import ocr_service

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup: Create tables if they don't exist
    # Note: In production, use Alembic migrations instead
    # Base.metadata.create_all(bind=engine)
    
    # Startup: Connect to MQTT broker
    if settings.MQTT_ENABLED:
        register_default_handlers()
        mqtt_service.connect()
    
    # Startup: Start OCR file watcher service
    if settings.OCR_ENABLED:
        ocr_service.start()
    
    yield
    
    # Shutdown: Stop OCR file watcher
    if settings.OCR_ENABLED:
        ocr_service.stop()
    
    # Shutdown: Disconnect from MQTT broker
    if settings.MQTT_ENABLED:
        mqtt_service.disconnect()


app = FastAPI(
    title="AutoBox API",
    description="스마트 물류 자동 분류 시스템 API",
    version="1.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware - 환경변수에서 허용 도메인 로드
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Requested-With"],
)


# Global exception handler for HTTPException-style errors
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions."""
    # 에러 응답에도 CORS 헤더 포함 (요청 Origin 확인)
    origin = request.headers.get("origin", "")
    allowed_origin = origin if origin in settings.cors_origins_list else ""
    
    headers = {
        "Access-Control-Allow-Origin": allowed_origin,
        "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
        "Access-Control-Allow-Headers": "Authorization, Content-Type, X-Requested-With",
    }
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "data": None,
            "error": {
                "code": "INTERNAL_ERROR",
                "message": str(exc) if settings.DEBUG else "내부 서버 오류가 발생했습니다"
            }
        },
        headers=headers
    )


# Include routers with API version prefix
API_PREFIX = "/api/v1"

app.include_router(waybills_router, prefix=API_PREFIX)
app.include_router(regions_router, prefix=API_PREFIX)
app.include_router(system_router, prefix=API_PREFIX)
app.include_router(alerts_router, prefix=API_PREFIX)
app.include_router(stats_router, prefix=API_PREFIX)
app.include_router(recognition_router, prefix=API_PREFIX)
app.include_router(cameras_router, prefix=API_PREFIX)
app.include_router(vehicle_router, prefix=API_PREFIX)
app.include_router(ocr_router, prefix=API_PREFIX)

# WebSocket router (no API prefix)
app.include_router(websocket_router)

# Frontend compatibility router (/api prefix for legacy frontend support)
app.include_router(frontend_compat_router, prefix="/api")


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "success": True,
        "data": {
            "name": "AutoBox API",
            "version": "1.1.0",
            "docs": "/docs"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "success": True,
        "data": {
            "status": "healthy"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )

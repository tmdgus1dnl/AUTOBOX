"""Recognition API routes."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.database import get_db
from app.models.waybill import ScanLog
from app.schemas.camera import LatestScanLogData, LatestRecognitionData

router = APIRouter(prefix="/recognition", tags=["인식"])


@router.get("/latest", response_model=dict)
async def get_latest_recognition(db: Session = Depends(get_db)):
    """CAM-001: 최신 인식 정보 조회."""
    latest_scan = db.query(ScanLog).order_by(desc(ScanLog.scanned_at)).first()
    
    if not latest_scan:
        return {
            "success": True,
            "data": LatestRecognitionData(scan_log=None)
        }
    
    return {
        "success": True,
        "data": LatestRecognitionData(
            scan_log=LatestScanLogData(
                tracking_number=latest_scan.tracking_number,
                camera_id=latest_scan.camera_id,
                detected_destination=latest_scan.detected_destination,
                confidence_score=latest_scan.confidence_score,
                scanned_at=latest_scan.scanned_at
            )
        )
    }

"""Waybill API routes."""

from datetime import datetime, date
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from app.database import get_db
from app.models.waybill import LogisticsItem, ScanLog, WaybillMap, LogisticsStatus
from app.models.alert import Alert, AlertSeverity
from app.schemas.waybill import (
    WaybillScanRequest,
    WaybillScanData,
    RecognitionRequest,
    RecognitionData,
    StartSortingData,
    CompleteData,
    ErrorRequest,
    ErrorStatusData,
    WaybillListItem,
    WaybillListData,
    WaybillDetailItem,
    WaybillDetailData,
    ScanLogOut,
)
from app.services.websocket import manager

router = APIRouter(prefix="/waybills", tags=["운송장"])


@router.get("/{tracking_number}/image")
async def get_waybill_image(tracking_number: str, db: Session = Depends(get_db)):
    """운송장의 OCR 원본 이미지(base64) 반환."""
    import json, os

    item = db.query(LogisticsItem).filter(
        LogisticsItem.tracking_number == tracking_number
    ).first()

    if not item or not item.image_file:
        raise HTTPException(status_code=404, detail="이미지를 찾을 수 없습니다.")

    # Try data directory (Docker: /app/data, local: ./data)
    file_path = os.path.join("./data", item.image_file)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="이미지 파일이 존재하지 않습니다.")

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        image_base64 = data.get("dest", "")
        if not image_base64:
            raise HTTPException(status_code=404, detail="이미지 데이터가 비어있습니다.")
        return {"success": True, "data": {"image_base64": image_base64}}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"이미지 로드 오류: {str(e)}")


@router.delete("/reset", response_model=dict)
async def reset_all_waybills(db: Session = Depends(get_db)):
    """모든 운송장 데이터 삭제 (물류 초기화).
    
    LogisticsItem 삭제 시 CASCADE로 ScanLog, WaybillMap도 함께 삭제됩니다.
    """
    deleted_count = db.query(LogisticsItem).count()
    db.query(LogisticsItem).delete()
    db.commit()
    
    # Broadcast via WebSocket
    await manager.broadcast({
        "type": "waybill_reset",
        "data": {"deleted_count": deleted_count}
    })
    
    return {
        "success": True,
        "message": f"{deleted_count}개의 운송장 데이터가 삭제되었습니다.",
        "deleted_count": deleted_count
    }


def generate_tracking_number() -> str:
    """Generate a unique tracking number."""
    now = datetime.now()
    timestamp = now.strftime("%Y%m%d%H%M%S%f")[:17]
    return f"TRK-{timestamp}"


def get_waybill_by_id(db: Session, waybill_id: int) -> tuple[LogisticsItem, WaybillMap]:
    """Get waybill by internal ID."""
    waybill_map = db.query(WaybillMap).filter(WaybillMap.waybill_id == waybill_id).first()
    if not waybill_map:
        raise HTTPException(status_code=404, detail={
            "code": "WAYBILL_NOT_FOUND",
            "message": "운송장을 찾을 수 없습니다"
        })
    
    logistics_item = db.query(LogisticsItem).filter(
        LogisticsItem.tracking_number == waybill_map.tracking_number
    ).first()
    
    return logistics_item, waybill_map


@router.post("/scan", response_model=dict)
async def scan_waybill(request: WaybillScanRequest, db: Session = Depends(get_db)):
    """WB-001: 운송장 스캔 시작 - 새로운 운송장 레코드 생성."""
    tracking_number = generate_tracking_number()
    
    # Create logistics item
    logistics_item = LogisticsItem(
        tracking_number=tracking_number,
        status=LogisticsStatus.READY,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    db.add(logistics_item)
    db.flush()
    
    # Create waybill map
    waybill_map = WaybillMap(tracking_number=tracking_number)
    db.add(waybill_map)
    db.commit()
    db.refresh(waybill_map)
    
    # Broadcast via WebSocket
    await manager.broadcast({
        "type": "waybill_update",
        "data": {
            "waybill_id": waybill_map.waybill_id,
            "tracking_number": tracking_number,
            "status": logistics_item.status.value,
            "destination": None
        }
    })
    
    return {
        "success": True,
        "data": WaybillScanData(
            waybill_id=waybill_map.waybill_id,
            tracking_number=tracking_number,
            status=logistics_item.status,
            created_at=logistics_item.created_at
        )
    }


@router.put("/{waybill_id}/recognition", response_model=dict)
async def save_recognition(
    waybill_id: int,
    request: RecognitionRequest,
    db: Session = Depends(get_db)
):
    """WB-002: OCR 인식 결과 저장."""
    logistics_item, waybill_map = get_waybill_by_id(db, waybill_id)
    
    # Create scan log
    scan_log = ScanLog(
        tracking_number=logistics_item.tracking_number,
        camera_id=request.camera_id,
        detected_destination=request.destination,
        confidence_score=request.confidence_score,
        scanned_at=datetime.now()
    )
    db.add(scan_log)
    
    # Update logistics item
    logistics_item.destination = request.destination
    logistics_item.updated_at = datetime.now()
    
    # Auto error if confidence is too low
    if request.confidence_score < 60:
        logistics_item.status = LogisticsStatus.ERROR
    
    db.commit()
    db.refresh(scan_log)
    
    # Broadcast via WebSocket
    await manager.broadcast({
        "type": "waybill_update",
        "data": {
            "waybill_id": waybill_id,
            "tracking_number": logistics_item.tracking_number,
            "status": logistics_item.status.value,
            "destination": logistics_item.destination
        }
    })
    
    return {
        "success": True,
        "data": RecognitionData(
            waybill_id=waybill_id,
            tracking_number=logistics_item.tracking_number,
            status=logistics_item.status,
            destination=request.destination,
            confidence_score=request.confidence_score,
            scanned_at=scan_log.scanned_at
        )
    }


@router.put("/{waybill_id}/start-sorting", response_model=dict)
async def start_sorting(waybill_id: int, db: Session = Depends(get_db)):
    """WB-003: 분류 시작 - 차량이 박스를 적재하고 이동 시작."""
    logistics_item, waybill_map = get_waybill_by_id(db, waybill_id)
    
    if logistics_item.status != LogisticsStatus.READY:
        raise HTTPException(status_code=400, detail={
            "code": "INVALID_STATUS",
            "message": f"현재 상태({logistics_item.status.value})에서는 분류를 시작할 수 없습니다"
        })
    
    logistics_item.status = LogisticsStatus.MOVING
    logistics_item.updated_at = datetime.now()
    db.commit()
    
    # Broadcast via WebSocket
    await manager.broadcast({
        "type": "waybill_update",
        "data": {
            "waybill_id": waybill_id,
            "tracking_number": logistics_item.tracking_number,
            "status": logistics_item.status.value,
            "destination": logistics_item.destination
        }
    })
    
    return {
        "success": True,
        "data": StartSortingData(
            waybill_id=waybill_id,
            tracking_number=logistics_item.tracking_number,
            status=logistics_item.status,
            updated_at=logistics_item.updated_at
        )
    }


@router.put("/{waybill_id}/complete", response_model=dict)
async def complete_sorting(waybill_id: int, db: Session = Depends(get_db)):
    """WB-004: 분류 완료 - 목적지 도착 후 하역 완료 처리."""
    logistics_item, waybill_map = get_waybill_by_id(db, waybill_id)
    
    if logistics_item.status != LogisticsStatus.MOVING:
        raise HTTPException(status_code=400, detail={
            "code": "INVALID_STATUS",
            "message": f"현재 상태({logistics_item.status.value})에서는 완료 처리할 수 없습니다"
        })
    
    now = datetime.now()
    logistics_item.status = LogisticsStatus.COMPLETED
    logistics_item.completed_at = now
    logistics_item.updated_at = now
    db.commit()
    
    # Calculate process time
    process_time_sec = int((logistics_item.completed_at - logistics_item.created_at).total_seconds())
    
    # Broadcast via WebSocket
    await manager.broadcast({
        "type": "waybill_update",
        "data": {
            "waybill_id": waybill_id,
            "tracking_number": logistics_item.tracking_number,
            "status": logistics_item.status.value,
            "destination": logistics_item.destination
        }
    })
    
    return {
        "success": True,
        "data": CompleteData(
            waybill_id=waybill_id,
            tracking_number=logistics_item.tracking_number,
            status=logistics_item.status,
            completed_at=logistics_item.completed_at,
            process_time_sec=process_time_sec
        )
    }


@router.put("/{waybill_id}/error", response_model=dict)
async def set_error(
    waybill_id: int,
    request: ErrorRequest,
    db: Session = Depends(get_db)
):
    """WB-005: 오류 처리 - 인식 실패 시 오류 상태로 전환."""
    logistics_item, waybill_map = get_waybill_by_id(db, waybill_id)
    
    logistics_item.status = LogisticsStatus.ERROR
    logistics_item.updated_at = datetime.now()
    
    # Create alert
    alert = Alert(
        alert_type="ocr_error",
        severity=AlertSeverity.WARNING,
        title="운송장 인식 오류",
        message=request.error_reason,
        source_type="waybill",
        source_id=str(waybill_id),
        is_resolved=False,
        created_at=datetime.now()
    )
    db.add(alert)
    db.commit()
    db.refresh(alert)
    
    # Broadcast via WebSocket
    await manager.broadcast({
        "type": "waybill_update",
        "data": {
            "waybill_id": waybill_id,
            "tracking_number": logistics_item.tracking_number,
            "status": logistics_item.status.value,
            "destination": logistics_item.destination
        }
    })
    
    return {
        "success": True,
        "data": ErrorStatusData(
            waybill_id=waybill_id,
            tracking_number=logistics_item.tracking_number,
            status=logistics_item.status,
            alert_id=alert.alert_id,
            updated_at=logistics_item.updated_at
        )
    }


@router.get("", response_model=dict)
async def list_waybills(
    date: Optional[str] = Query(None, description="조회 날짜 (YYYY-MM-DD)"),
    status: Optional[LogisticsStatus] = Query(None, description="상태 필터"),
    region: Optional[str] = Query(None, description="구역 필터"),
    page: int = Query(1, ge=1, description="페이지 번호"),
    size: int = Query(20, ge=1, le=100, description="페이지 크기"),
    db: Session = Depends(get_db)
):
    """WB-006: 운송장 목록 조회."""
    query = db.query(LogisticsItem, WaybillMap).join(
        WaybillMap, LogisticsItem.tracking_number == WaybillMap.tracking_number
    )
    
    # Apply filters
    if date:
        try:
            target_date = datetime.strptime(date, "%Y-%m-%d").date()
            start_dt = datetime.combine(target_date, datetime.min.time())
            end_dt = datetime.combine(target_date, datetime.max.time())
            query = query.filter(LogisticsItem.created_at >= start_dt, LogisticsItem.created_at <= end_dt)
        except ValueError:
            raise HTTPException(status_code=400, detail={
                "code": "INVALID_DATE",
                "message": "날짜 형식이 올바르지 않습니다 (YYYY-MM-DD)"
            })
    
    if status:
        query = query.filter(LogisticsItem.status == status)
    
    if region:
        query = query.filter(LogisticsItem.destination == region)
    
    # Get total count
    total = query.count()
    total_pages = (total + size - 1) // size
    
    # Apply pagination and ordering
    offset = (page - 1) * size
    results = query.order_by(desc(LogisticsItem.created_at)).offset(offset).limit(size).all()
    
    items = []
    for logistics_item, waybill_map in results:
        process_time_sec = None
        if logistics_item.completed_at and logistics_item.created_at:
            process_time_sec = int((logistics_item.completed_at - logistics_item.created_at).total_seconds())
        
        items.append(WaybillListItem(
            waybill_id=waybill_map.waybill_id,
            tracking_number=logistics_item.tracking_number,
            destination=logistics_item.destination,
            status=logistics_item.status,
            created_at=logistics_item.created_at,
            completed_at=logistics_item.completed_at,
            process_time_sec=process_time_sec
        ))
    
    return {
        "success": True,
        "data": WaybillListData(
            items=items,
            total=total,
            page=page,
            size=size,
            total_pages=total_pages
        )
    }


@router.get("/{waybill_id}", response_model=dict)
async def get_waybill_detail(waybill_id: int, db: Session = Depends(get_db)):
    """WB-007: 운송장 상세 조회."""
    logistics_item, waybill_map = get_waybill_by_id(db, waybill_id)
    
    # Get scan logs
    scan_logs = db.query(ScanLog).filter(
        ScanLog.tracking_number == logistics_item.tracking_number
    ).order_by(desc(ScanLog.scanned_at)).all()
    
    scan_logs_out = [
        ScanLogOut(
            camera_id=log.camera_id,
            detected_destination=log.detected_destination,
            confidence_score=log.confidence_score,
            scanned_at=log.scanned_at
        )
        for log in scan_logs
    ]
    
    return {
        "success": True,
        "data": WaybillDetailData(
            item=WaybillDetailItem(
                waybill_id=waybill_map.waybill_id,
                tracking_number=logistics_item.tracking_number,
                destination=logistics_item.destination,
                status=logistics_item.status,
                created_at=logistics_item.created_at,
                completed_at=logistics_item.completed_at
            ),
            scan_logs=scan_logs_out
        )
    }

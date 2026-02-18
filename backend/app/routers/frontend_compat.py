"""Frontend compatibility API routes.

This module provides API endpoints that match the frontend's expected format.
These endpoints wrap the existing v1 API responses to maintain frontend compatibility.
"""

from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, case

from app.database import get_db
from app.models.waybill import LogisticsItem, LogisticsStatus
from app.models.device import DeviceStatus
from app.models.region import Region

router = APIRouter(tags=["Frontend Compatibility"])


@router.get("/logistics/stats")
async def get_logistics_stats(
    date: Optional[str] = Query(None, description="Date filter (YYYY-MM-DD)"),
    db: Session = Depends(get_db)
):
    """
    Get logistics statistics for dashboard.
    
    Returns data in the format expected by the frontend:
    {
        "summary": {
            "Seoul": {"done": 10, "left": 5},
            "Busan": {"done": 8, "left": 3},
            ...
        },
        "logs": [
            {"id": "TRK-xxx", "target": "Seoul", "status": "complete", "dateTime": "..."},
            ...
        ]
    }
    """
    # Build query for statistics
    query = db.query(
        LogisticsItem.destination,
        func.count(LogisticsItem.tracking_number).label("total"),
        func.sum(case((LogisticsItem.status == LogisticsStatus.COMPLETED, 1), else_=0)).label("completed"),
        func.sum(case((LogisticsItem.status != LogisticsStatus.COMPLETED, 1), else_=0)).label("pending")
    )
    
    # Apply date filter
    if date:
        try:
            filter_date = datetime.strptime(date, "%Y-%m-%d").date()
            query = query.filter(func.date(LogisticsItem.created_at) == filter_date)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    
    # Get region statistics
    query = query.filter(LogisticsItem.destination.isnot(None))
    results = query.group_by(LogisticsItem.destination).all()
    
    # Map region names (Korean)
    region_name_map = {
        "SEOUL": "서울",
        "BUSAN": "부산",
        "GWANGJU": "광주",
        "DAEJEON": "대전",
        "DAEGU": "대구",
    }
    
    # Build summary
    summary = {}
    for row in results:
        # Try to map region name, or use as-is
        region_name = region_name_map.get(row.destination.upper(), row.destination) if row.destination else "Unknown"
        summary[region_name] = {
            "done": row.completed or 0,
            "left": row.pending or 0
        }
    
    # Get recent logs
    logs_query = db.query(LogisticsItem)
    if date:
        logs_query = logs_query.filter(func.date(LogisticsItem.created_at) == filter_date)
    
    logs_result = logs_query.order_by(LogisticsItem.created_at.desc()).limit(100).all()
    
    # Map status to frontend format
    status_map = {
        LogisticsStatus.READY: "대기 중",
        LogisticsStatus.MOVING: "이동 중",
        LogisticsStatus.COMPLETED: "완료",
        LogisticsStatus.ERROR: "오류"
    }
    
    logs = []
    for item in logs_result:
        region_name = region_name_map.get(item.destination.upper(), item.destination) if item.destination else "-"
        logs.append({
            "id": item.tracking_number,
            "target": region_name,
            "status": status_map.get(item.status, str(item.status.value) if item.status else "-"),
            "dateTime": item.completed_at.strftime("%Y-%m-%d %H:%M:%S") if item.completed_at else (
                item.created_at.strftime("%Y-%m-%d %H:%M:%S") if item.created_at else ""
            )
        })
    
    return {
        "summary": summary,
        "logs": logs
    }


@router.get("/device/status/{device_id}")
async def get_device_status(
    device_id: str,
    db: Session = Depends(get_db)
):
    """
    Get device status by device ID.
    
    Returns data in the format expected by the frontend:
    {
        "battery_level": 85,
        "is_connected": true,
        "operation_status": "RUNNING"
    }
    """
    device = db.query(DeviceStatus).filter(DeviceStatus.device_id == device_id).first()
    
    if not device:
        # Return default values if device not found
        return {
            "device_id": device_id,
            "battery_level": 0,
            "is_connected": False,
            "operation_status": "OFFLINE",
            "last_heartbeat": None
        }
    
    return {
        "device_id": device.device_id,
        "battery_level": device.battery_level,
        "is_connected": device.is_connected,
        "operation_status": device.operation_status.value if device.operation_status else "UNKNOWN",
        "last_heartbeat": device.last_heartbeat.isoformat() if device.last_heartbeat else None
    }

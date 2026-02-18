"""Alert API routes."""

from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.database import get_db
from app.models.alert import Alert, AlertSeverity
from app.schemas.alert import AlertOut, AlertCreateRequest

router = APIRouter(prefix="/alerts", tags=["알림"])


@router.post("", response_model=dict)
async def create_alert(request: AlertCreateRequest, db: Session = Depends(get_db)):
    """ALT-001: 알림 생성."""
    alert = Alert(
        alert_type=request.alert_type,
        severity=request.severity,
        title=request.title,
        message=request.message,
        source_type=request.source_type,
        source_id=request.source_id,
        is_resolved=False,
        created_at=datetime.now()
    )
    db.add(alert)
    db.commit()
    db.refresh(alert)
    
    return {
        "success": True,
        "data": AlertOut(
            alert_id=alert.alert_id,
            alert_type=alert.alert_type,
            severity=alert.severity,
            title=alert.title,
            message=alert.message,
            source_type=alert.source_type,
            source_id=alert.source_id,
            is_resolved=alert.is_resolved,
            created_at=alert.created_at,
            resolved_at=alert.resolved_at
        )
    }


@router.get("", response_model=dict)
async def list_alerts(
    resolved: Optional[bool] = Query(None, description="해결 여부 필터"),
    severity: Optional[AlertSeverity] = Query(None, description="심각도 필터"),
    db: Session = Depends(get_db)
):
    """ALT-002: 알림 목록 조회."""
    query = db.query(Alert)
    
    if resolved is not None:
        query = query.filter(Alert.is_resolved == resolved)
    
    if severity:
        query = query.filter(Alert.severity == severity)
    
    alerts = query.order_by(desc(Alert.created_at)).all()
    
    return {
        "success": True,
        "data": [
            AlertOut(
                alert_id=a.alert_id,
                alert_type=a.alert_type,
                severity=a.severity,
                title=a.title,
                message=a.message,
                source_type=a.source_type,
                source_id=a.source_id,
                is_resolved=a.is_resolved,
                created_at=a.created_at,
                resolved_at=a.resolved_at
            )
            for a in alerts
        ]
    }


@router.patch("/{alert_id}/resolve", response_model=dict)
async def resolve_alert(alert_id: int, db: Session = Depends(get_db)):
    """ALT-003: 알림 해결 처리."""
    alert = db.query(Alert).filter(Alert.alert_id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail={
            "code": "ALERT_NOT_FOUND",
            "message": "알림을 찾을 수 없습니다"
        })
    
    alert.is_resolved = True
    alert.resolved_at = datetime.now()
    db.commit()
    
    return {
        "success": True,
        "data": AlertOut(
            alert_id=alert.alert_id,
            alert_type=alert.alert_type,
            severity=alert.severity,
            title=alert.title,
            message=alert.message,
            source_type=alert.source_type,
            source_id=alert.source_id,
            is_resolved=alert.is_resolved,
            created_at=alert.created_at,
            resolved_at=alert.resolved_at
        )
    }

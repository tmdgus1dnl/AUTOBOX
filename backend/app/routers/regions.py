"""Region API routes."""

from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models.region import Region
from app.schemas.region import RegionOut, RegionCreateRequest, RegionStatusRequest

router = APIRouter(prefix="/regions", tags=["구역"])


@router.get("", response_model=dict)
async def list_regions(db: Session = Depends(get_db)):
    """RG-001: 구역 목록 조회."""
    regions = db.query(Region).filter(Region.is_active == True).order_by(Region.display_order).all()
    
    return {
        "success": True,
        "data": [
            RegionOut(
                region_id=r.region_id,
                region_name=r.region_name,
                region_detail=r.region_detail,
                display_order=r.display_order,
                is_active=r.is_active
            )
            for r in regions
        ]
    }


@router.post("", response_model=dict)
async def create_region(request: RegionCreateRequest, db: Session = Depends(get_db)):
    """RG-002: 구역 등록."""
    # Check if region already exists
    existing = db.query(Region).filter(Region.region_id == request.region_id).first()
    if existing:
        raise HTTPException(status_code=400, detail={
            "code": "DUPLICATE_REGION",
            "message": "이미 존재하는 구역 ID입니다"
        })
    
    region = Region(
        region_id=request.region_id,
        region_name=request.region_name,
        region_detail=request.region_detail,
        display_order=request.display_order,
        is_active=request.is_active,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    db.add(region)
    db.commit()
    db.refresh(region)
    
    return {
        "success": True,
        "data": RegionOut(
            region_id=region.region_id,
            region_name=region.region_name,
            region_detail=region.region_detail,
            display_order=region.display_order,
            is_active=region.is_active
        )
    }


@router.patch("/{region_id}/status", response_model=dict)
async def update_region_status(
    region_id: str,
    request: RegionStatusRequest,
    db: Session = Depends(get_db)
):
    """RG-003: 구역 활성화/비활성화."""
    region = db.query(Region).filter(Region.region_id == region_id).first()
    if not region:
        raise HTTPException(status_code=404, detail={
            "code": "REGION_NOT_FOUND",
            "message": "구역을 찾을 수 없습니다"
        })
    
    region.is_active = request.is_active
    region.updated_at = datetime.now()
    db.commit()
    
    return {
        "success": True,
        "data": RegionOut(
            region_id=region.region_id,
            region_name=region.region_name,
            region_detail=region.region_detail,
            display_order=region.display_order,
            is_active=region.is_active
        )
    }

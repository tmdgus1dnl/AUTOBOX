"""OCR Results API Router."""

from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any, Optional

from app.services.ocr_service import ocr_service

router = APIRouter(prefix="/ocr", tags=["OCR"])


@router.get("/results")
async def get_ocr_results(limit: int = 20) -> Dict[str, Any]:
    """Get recent OCR processing results."""
    results = ocr_service.get_results(limit=limit)
    return {
        "success": True,
        "data": {
            "items": results,
            "total": len(results)
        }
    }


@router.get("/results/{result_id}")
async def get_ocr_result(result_id: str) -> Dict[str, Any]:
    """Get a specific OCR result by ID."""
    result = ocr_service.get_result(result_id)
    
    if not result:
        raise HTTPException(status_code=404, detail="OCR result not found")
    
    return {
        "success": True,
        "data": result
    }


@router.get("/status")
async def get_ocr_status() -> Dict[str, Any]:
    """Get OCR service status."""
    return {
        "success": True,
        "data": {
            "enabled": ocr_service.enabled,
            "watch_directory": ocr_service.watch_directory,
            "api_url": ocr_service.api_url,
            "results_count": len(ocr_service._results)
        }
    }

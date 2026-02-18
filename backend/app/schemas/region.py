"""Region schemas."""

from typing import Optional
from pydantic import BaseModel


class RegionOut(BaseModel):
    """Region output schema."""
    region_id: str
    region_name: str
    region_detail: Optional[str] = None
    display_order: int
    is_active: bool

    class Config:
        from_attributes = True


class RegionCreateRequest(BaseModel):
    """Request schema for creating region."""
    region_id: str
    region_name: str
    region_detail: Optional[str] = None
    display_order: int = 0
    is_active: bool = True


class RegionStatusRequest(BaseModel):
    """Request schema for updating region status."""
    is_active: bool

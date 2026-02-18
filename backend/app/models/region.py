"""Region model."""

from datetime import datetime
from sqlalchemy import Column, String, DateTime, Integer, Boolean, Index
from app.database import Base


class Region(Base):
    """Region (delivery zone) table."""
    
    __tablename__ = "region"
    
    region_id = Column(String(20), primary_key=True, comment="구역 ID")
    region_name = Column(String(50), nullable=False, comment="구역 이름")
    region_detail = Column(String(50), nullable=True, comment="상세")
    display_order = Column(Integer, nullable=False, default=0, comment="표시 순서")
    is_active = Column(Boolean, nullable=False, default=True, comment="활성 여부")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        Index("idx_region_active_order", "is_active", "display_order"),
    )

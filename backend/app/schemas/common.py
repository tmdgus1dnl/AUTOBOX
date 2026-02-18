"""Common response schemas."""

from typing import Any, Optional, Generic, TypeVar
from pydantic import BaseModel

T = TypeVar("T")


class ErrorDetail(BaseModel):
    """Error detail schema."""
    code: str
    message: str


class SuccessResponse(BaseModel, Generic[T]):
    """Standard success response schema."""
    success: bool = True
    data: T
    message: str = "처리 완료"


class ErrorResponse(BaseModel):
    """Standard error response schema."""
    success: bool = False
    data: None = None
    error: ErrorDetail

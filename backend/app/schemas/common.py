"""Common Pydantic schemas used across all Saathi API endpoints."""
from pydantic import BaseModel
from typing import Any, Optional


class SuccessResponse(BaseModel):
    """Contract §12.7 — Standard success envelope."""
    success: bool = True
    data: Any = None


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: Optional[Any] = None


class ErrorResponse(BaseModel):
    """Contract §12.8 — Standard error envelope."""
    success: bool = False
    error: ErrorDetail

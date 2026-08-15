"""Standard API response envelopes."""

from typing import Any, Generic, Optional, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class ErrorBody(BaseModel):
    code: str
    message: str
    details: dict[str, Any] | None = None


class APIResponse(BaseModel, Generic[T]):
    success: bool = True
    data: Optional[T] = None
    meta: dict[str, Any] | None = None


class APIErrorResponse(BaseModel):
    success: bool = False
    error: ErrorBody

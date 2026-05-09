"""
Common response schemas shared across all routers.

Implements the unified error response format defined in API_SPEC.md §2.
"""

from __future__ import annotations

from typing import Any, Generic, List, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


# ── Error schemas ──────────────────────────────────────────────────────────────

class ErrorDetail(BaseModel):
    """Inner object of every error response."""

    code: str = Field(..., examples=["ITEM_NOT_FOUND"])
    message: str = Field(..., examples=["Bucket list item not found."])
    details: Any = Field(default=None)


class ErrorResponse(BaseModel):
    """
    Top-level unified error envelope.

    Example::

        {
            "error": {
                "code": "ITEM_NOT_FOUND",
                "message": "Bucket list item not found.",
                "details": null
            }
        }
    """

    error: ErrorDetail


# ── Pagination schema ──────────────────────────────────────────────────────────

class PaginationMeta(BaseModel):
    """Pagination metadata returned with every list endpoint."""

    page: int = Field(..., ge=1)
    limit: int = Field(..., ge=1, le=50)
    total: int = Field(..., ge=0)
    has_next: bool


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated list envelope."""

    data: List[T]
    pagination: PaginationMeta


# ── Helper factories ───────────────────────────────────────────────────────────

def make_error(code: str, message: str, details: Any = None) -> ErrorResponse:
    """Convenience factory for building ErrorResponse objects."""
    return ErrorResponse(error=ErrorDetail(code=code, message=message, details=details))


def make_pagination(page: int, limit: int, total: int) -> PaginationMeta:
    """Calculate pagination metadata from offset-based parameters."""
    return PaginationMeta(
        page=page,
        limit=limit,
        total=total,
        has_next=(page * limit) < total,
    )

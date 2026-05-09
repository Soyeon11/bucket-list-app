"""
Pydantic v2 schemas for bucket list item request/response payloads.

Mirrors the field constraints documented in API_SPEC.md §4.2.
"""

from __future__ import annotations

import re
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, model_validator


# ── Enum literals ──────────────────────────────────────────────────────────────

CATEGORY_VALUES = ("travel", "food", "hobby", "fitness", "culture", "etc")
PRIORITY_VALUES = ("high", "medium", "low")
STATUS_VALUES = ("active", "completed")


# ── Request schemas ────────────────────────────────────────────────────────────

class BucketItemCreate(BaseModel):
    """POST /items request body."""

    title: str = Field(..., min_length=1, max_length=100)
    category: str = Field(..., examples=["travel"])
    priority: str = Field(default="medium", examples=["high"])
    description: Optional[str] = Field(default=None, max_length=500)
    tags: List[str] = Field(default_factory=list)

    @field_validator("category")
    @classmethod
    def validate_category(cls, v: str) -> str:
        if v not in CATEGORY_VALUES:
            raise ValueError(f"category must be one of: {', '.join(CATEGORY_VALUES)}")
        return v

    @field_validator("priority")
    @classmethod
    def validate_priority(cls, v: str) -> str:
        if v not in PRIORITY_VALUES:
            raise ValueError(f"priority must be one of: {', '.join(PRIORITY_VALUES)}")
        return v

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, v: List[str]) -> List[str]:
        if len(v) > 10:
            raise ValueError("tags may contain at most 10 items")
        for tag in v:
            if len(tag) > 20:
                raise ValueError(f"each tag must be 20 characters or fewer (got '{tag}')")
            if not tag:
                raise ValueError("tags must not contain empty strings")
        return [t.lower() for t in v]


class BucketItemUpdate(BaseModel):
    """PATCH /items/{item_id} request body — all fields optional."""

    title: Optional[str] = Field(default=None, min_length=1, max_length=100)
    category: Optional[str] = Field(default=None)
    priority: Optional[str] = Field(default=None)
    description: Optional[str] = Field(default=None, max_length=500)
    tags: Optional[List[str]] = Field(default=None)

    @field_validator("category")
    @classmethod
    def validate_category(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in CATEGORY_VALUES:
            raise ValueError(f"category must be one of: {', '.join(CATEGORY_VALUES)}")
        return v

    @field_validator("priority")
    @classmethod
    def validate_priority(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in PRIORITY_VALUES:
            raise ValueError(f"priority must be one of: {', '.join(PRIORITY_VALUES)}")
        return v

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        if v is None:
            return v
        if len(v) > 10:
            raise ValueError("tags may contain at most 10 items")
        for tag in v:
            if len(tag) > 20:
                raise ValueError(f"each tag must be 20 characters or fewer (got '{tag}')")
            if not tag:
                raise ValueError("tags must not contain empty strings")
        return [t.lower() for t in v]

    @model_validator(mode="after")
    def at_least_one_field(self) -> "BucketItemUpdate":
        if all(v is None for v in self.model_dump().values()):
            raise ValueError("At least one field must be provided for update")
        return self


# ── Response schemas ───────────────────────────────────────────────────────────

class BucketItemResponse(BaseModel):
    """Single item in GET /items list response."""

    id: UUID
    title: str
    category: str
    priority: str
    description: Optional[str]
    tags: List[str]
    status: str
    last_recommended_at: Optional[datetime]
    completed_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class BucketItemDetailResponse(BucketItemResponse):
    """GET /items/{item_id} — adds logs_count."""

    logs_count: int = 0


class BucketItemCompleteResponse(BaseModel):
    """PATCH /items/{item_id}/complete response."""

    id: UUID
    status: str
    completed_at: datetime

    model_config = {"from_attributes": True}


# ── Query parameter schema ─────────────────────────────────────────────────────

class BucketItemListParams(BaseModel):
    """Validated query parameters for GET /items."""

    category: Optional[str] = Field(default=None)
    status: str = Field(default="active")
    priority: Optional[str] = Field(default=None)
    q: Optional[str] = Field(default=None, description="Title search keyword")
    page: int = Field(default=1, ge=1)
    limit: int = Field(default=20, ge=1, le=50)

    @field_validator("category")
    @classmethod
    def validate_category(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in CATEGORY_VALUES:
            raise ValueError(f"category must be one of: {', '.join(CATEGORY_VALUES)}")
        return v

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        if v not in ("active", "completed", "all"):
            raise ValueError("status must be one of: active, completed, all")
        return v

    @field_validator("priority")
    @classmethod
    def validate_priority(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in PRIORITY_VALUES:
            raise ValueError(f"priority must be one of: {', '.join(PRIORITY_VALUES)}")
        return v

"""
Pydantic v2 schemas for activity log request/response payloads.

Covers media upload flow (signed URLs, confirmation) and activity log
CRUD shapes used by the logs router.
"""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from schemas.common import PaginationMeta


# ── Media upload request/response schemas ──────────────────────────────────────

class UploadFileSpec(BaseModel):
    filename: str
    mime_type: str  # "image/jpeg", "image/png", "video/mp4", etc.
    size_bytes: int
    order: int = Field(ge=1)


class MediaUploadRequest(BaseModel):
    files: List[UploadFileSpec] = Field(min_length=1, max_length=10)


class SignedUploadUrl(BaseModel):
    storage_path: str
    signed_url: str
    order: int
    filename: str


class MediaUploadResponse(BaseModel):
    urls: List[SignedUploadUrl]


class MediaConfirmRequest(BaseModel):
    storage_paths: List[str] = Field(min_length=1)


# ── Media item read schema ─────────────────────────────────────────────────────

class MediaItem(BaseModel):
    id: str
    type: str  # "image" | "video"
    storage_path: str
    mime_type: Optional[str] = None
    size_bytes: Optional[int] = None
    order: int
    upload_status: str  # "pending" | "uploaded" | "failed"
    signed_url: Optional[str] = None  # populated on read


# ── Activity log request/response schemas ─────────────────────────────────────

class ActivityLogCreate(BaseModel):
    note: Optional[str] = Field(default=None, max_length=1000)
    logged_at: Optional[datetime] = None  # defaults to now server-side


class ActivityLogResponse(BaseModel):
    id: str
    item_id: str
    user_id: str
    note: Optional[str] = None
    logged_at: str
    created_at: str
    media: List[MediaItem] = []


class ActivityLogListResponse(BaseModel):
    data: List[ActivityLogResponse]
    pagination: PaginationMeta

"""
Activity log endpoints — Phase 3 implementation.

Endpoints (all require Supabase JWT authentication):
    POST   /items/{item_id}/logs                      — create a new log entry
    GET    /items/{item_id}/logs                      — list logs (paginated)
    GET    /items/{item_id}/logs/{log_id}             — get single log with media
    DELETE /items/{item_id}/logs/{log_id}             — delete log and its media
    POST   /items/{item_id}/logs/{log_id}/upload-urls — get signed upload URLs
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, HTTPException, Path, Query, status
from fastapi.responses import Response

from config import get_settings
from database import CurrentUserID, SupabaseClient
from schemas.common import PaginationMeta, make_error
from schemas.log import (
    ActivityLogCreate,
    ActivityLogListResponse,
    ActivityLogResponse,
    MediaItem,
    MediaUploadRequest,
    MediaUploadResponse,
)
from services.storage import StorageService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/items/{item_id}/logs", tags=["Activity Logs"])


def _get_log_with_media(db, log_id: str, user_id: str) -> dict | None:
    """Fetch a log row and attach its media files as ActivityLogResponse dict."""
    log_res = (
        db.table("activity_logs")
        .select("*")
        .eq("id", log_id)
        .eq("user_id", user_id)
        .limit(1)
        .execute()
    )
    if not log_res.data:
        return None
    log = log_res.data[0]

    media_res = (
        db.table("media_files")
        .select("*")
        .eq("log_id", log_id)
        .order("order", desc=False)
        .execute()
    )
    media_rows = media_res.data or []

    # Attach signed view URLs
    storage = StorageService(db)
    media_items = []
    for m in media_rows:
        signed_url = ""
        if m.get("upload_status") == "uploaded":
            try:
                signed_url = storage.get_signed_view_url(m["storage_path"])
            except Exception:
                pass
        media_items.append({**m, "signed_url": signed_url})

    log["media"] = media_items
    return log


# ── POST /items/{item_id}/logs ────────────────────────────────────────────────

@router.post(
    "",
    response_model=ActivityLogResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new activity log",
)
async def create_log(
    item_id: Annotated[UUID, Path(...)],
    user_id: CurrentUserID,
    db: SupabaseClient,
    payload: ActivityLogCreate,
) -> ActivityLogResponse:
    # Verify the bucket item belongs to this user
    item_res = (
        db.table("bucket_items")
        .select("id")
        .eq("id", str(item_id))
        .eq("user_id", str(user_id))
        .limit(1)
        .execute()
    )
    if not item_res.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=make_error("ITEM_NOT_FOUND", "Bucket item not found.").model_dump(),
        )

    now = datetime.now(timezone.utc).isoformat()
    logged_at = payload.logged_at.isoformat() if payload.logged_at else now

    row = {
        "user_id": str(user_id),
        "item_id": str(item_id),
        "note": payload.note,
        "logged_at": logged_at,
        "created_at": now,
    }
    result = db.table("activity_logs").insert(row).execute()
    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=make_error("CREATE_FAILED", "Failed to create activity log.").model_dump(),
        )
    log = result.data[0]
    log["media"] = []
    return ActivityLogResponse(**log)


# ── GET /items/{item_id}/logs ─────────────────────────────────────────────────

@router.get(
    "",
    response_model=ActivityLogListResponse,
    summary="List activity logs for an item",
)
async def list_logs(
    item_id: Annotated[UUID, Path(...)],
    user_id: CurrentUserID,
    db: SupabaseClient,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=50),
) -> ActivityLogListResponse:
    offset = (page - 1) * limit

    result = (
        db.table("activity_logs")
        .select("*", count="exact")
        .eq("item_id", str(item_id))
        .eq("user_id", str(user_id))
        .order("logged_at", desc=True)
        .range(offset, offset + limit - 1)
        .execute()
    )
    rows = result.data or []
    total = result.count or 0

    # Attach media for each log
    hydrated = []
    for row in rows:
        enriched = _get_log_with_media(db, row["id"], str(user_id))
        if enriched:
            hydrated.append(ActivityLogResponse(**enriched))

    return ActivityLogListResponse(
        data=hydrated,
        pagination=PaginationMeta(
            page=page,
            limit=limit,
            total=total,
            has_next=(page * limit) < total,
        ),
    )


# ── GET /items/{item_id}/logs/{log_id} ────────────────────────────────────────

@router.get(
    "/{log_id}",
    response_model=ActivityLogResponse,
    summary="Get a single activity log with media",
)
async def get_log(
    item_id: Annotated[UUID, Path(...)],
    log_id: Annotated[UUID, Path(...)],
    user_id: CurrentUserID,
    db: SupabaseClient,
) -> ActivityLogResponse:
    log = _get_log_with_media(db, str(log_id), str(user_id))
    if log is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=make_error("LOG_NOT_FOUND", "Activity log not found.").model_dump(),
        )
    return ActivityLogResponse(**log)


# ── DELETE /items/{item_id}/logs/{log_id} ─────────────────────────────────────

@router.delete(
    "/{log_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    summary="Delete an activity log and its media",
)
async def delete_log(
    item_id: Annotated[UUID, Path(...)],
    log_id: Annotated[UUID, Path(...)],
    user_id: CurrentUserID,
    db: SupabaseClient,
) -> Response:
    # Fetch media files to delete from storage
    media_res = (
        db.table("media_files")
        .select("storage_path")
        .eq("log_id", str(log_id))
        .execute()
    )
    storage = StorageService(db)
    for m in media_res.data or []:
        storage.delete_file(m["storage_path"])

    # Delete the log row (media_files cascade via FK)
    result = (
        db.table("activity_logs")
        .delete()
        .eq("id", str(log_id))
        .eq("user_id", str(user_id))
        .execute()
    )
    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=make_error("LOG_NOT_FOUND", "Activity log not found.").model_dump(),
        )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ── POST /items/{item_id}/logs/{log_id}/upload-urls ───────────────────────────

@router.post(
    "/{log_id}/upload-urls",
    response_model=MediaUploadResponse,
    summary="Get signed upload URLs for media files",
)
async def get_upload_urls(
    item_id: Annotated[UUID, Path(...)],
    log_id: Annotated[UUID, Path(...)],
    user_id: CurrentUserID,
    db: SupabaseClient,
    payload: MediaUploadRequest,
) -> MediaUploadResponse:
    # Verify log belongs to user
    log_res = (
        db.table("activity_logs")
        .select("id")
        .eq("id", str(log_id))
        .eq("user_id", str(user_id))
        .limit(1)
        .execute()
    )
    if not log_res.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=make_error("LOG_NOT_FOUND", "Activity log not found.").model_dump(),
        )

    storage = StorageService(db)
    signed_urls = storage.create_signed_upload_urls(
        user_id=user_id,
        item_id=item_id,
        log_id=UUID(str(log_id)),
        file_specs=payload.files,
    )

    # Pre-insert media_files rows with status=pending
    now = datetime.now(timezone.utc).isoformat()
    for spec, url_info in zip(payload.files, signed_urls):
        file_type = "image" if spec.mime_type.startswith("image/") else "video"
        db.table("media_files").insert({
            "log_id": str(log_id),
            "user_id": str(user_id),
            "type": file_type,
            "storage_path": url_info.storage_path,
            "mime_type": spec.mime_type,
            "size_bytes": spec.size_bytes,
            "order": spec.order,
            "upload_status": "pending",
            "created_at": now,
        }).execute()

    return MediaUploadResponse(urls=signed_urls)

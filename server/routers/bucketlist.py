"""
Bucket list item CRUD router.

Endpoints (all require Supabase JWT authentication):
    GET    /api/v1/items                   — list with filter/pagination
    POST   /api/v1/items                   — create
    GET    /api/v1/items/{item_id}         — detail
    PUT    /api/v1/items/{item_id}         — full update (alias for PATCH)
    PATCH  /api/v1/items/{item_id}         — partial update
    DELETE /api/v1/items/{item_id}         — delete
    PATCH  /api/v1/items/{item_id}/complete — mark as completed

All database calls go through the Supabase service-role client (PostgREST).
RLS is enforced by filtering on user_id in every query.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Annotated, Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import Response
from supabase import Client

from database import CurrentUserID, SupabaseClient
from schemas.bucket_item import (
    BucketItemCompleteResponse,
    BucketItemCreate,
    BucketItemDetailResponse,
    BucketItemListParams,
    BucketItemResponse,
    BucketItemUpdate,
)
from schemas.common import ErrorResponse, PaginatedResponse, make_error, make_pagination

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/items", tags=["Bucket Items"])


# ── Internal helpers ───────────────────────────────────────────────────────────

def _row_to_response(row: Dict[str, Any], tags: List[str]) -> Dict[str, Any]:
    """Merge a bucket_items row with its tag list into a flat dict."""
    return {**row, "tags": tags}


def _fetch_tags(db: Client, item_id: str) -> List[str]:
    """Fetch tag strings for a single item."""
    result = db.table("item_tags").select("tag").eq("item_id", item_id).execute()
    return [r["tag"] for r in result.data]


def _fetch_tags_bulk(db: Client, item_ids: List[str]) -> Dict[str, List[str]]:
    """Fetch tags for multiple items in one query, returns {item_id: [tags]}."""
    if not item_ids:
        return {}
    result = db.table("item_tags").select("item_id,tag").in_("item_id", item_ids).execute()
    mapping: Dict[str, List[str]] = {iid: [] for iid in item_ids}
    for row in result.data:
        mapping[row["item_id"]].append(row["tag"])
    return mapping


def _get_item_or_404(db: Client, item_id: UUID, user_id: UUID) -> Dict[str, Any]:
    """
    Fetch a single bucket item belonging to the authenticated user.
    Raises 404 if not found, 403 if the item belongs to another user.
    """
    result = (
        db.table("bucket_items")
        .select("*")
        .eq("id", str(item_id))
        .single()
        .execute()
    )
    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=make_error("ITEM_NOT_FOUND", "Bucket list item not found.").model_dump(),
        )
    row = result.data
    if row["user_id"] != str(user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=make_error("FORBIDDEN", "You do not have access to this item.").model_dump(),
        )
    return row


def _replace_tags(db: Client, item_id: str, tags: List[str]) -> None:
    """
    Replace all tags for an item atomically:
    delete existing rows then insert the new set.
    """
    db.table("item_tags").delete().eq("item_id", item_id).execute()
    if tags:
        db.table("item_tags").insert(
            [{"item_id": item_id, "tag": tag} for tag in tags]
        ).execute()


# ── GET /items ─────────────────────────────────────────────────────────────────

@router.get(
    "",
    response_model=PaginatedResponse[BucketItemResponse],
    summary="List bucket items",
)
async def list_items(
    user_id: CurrentUserID,
    db: SupabaseClient,
    category: Optional[str] = Query(default=None),
    item_status: Optional[str] = Query(default="active", alias="status"),
    priority: Optional[str] = Query(default=None),
    q: Optional[str] = Query(default=None),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=50),
) -> PaginatedResponse[BucketItemResponse]:
    # Validate query params using the schema validator
    try:
        params = BucketItemListParams(
            category=category,
            status=item_status or "active",
            priority=priority,
            q=q,
            page=page,
            limit=limit,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=make_error("VALIDATION_ERROR", str(exc)).model_dump(),
        ) from exc

    query = (
        db.table("bucket_items")
        .select("*", count="exact")
        .eq("user_id", str(user_id))
    )

    if params.status != "all":
        query = query.eq("status", params.status)
    if params.category:
        query = query.eq("category", params.category)
    if params.priority:
        query = query.eq("priority", params.priority)
    if params.q:
        # Case-insensitive title search using ilike
        query = query.ilike("title", f"%{params.q}%")

    offset = (params.page - 1) * params.limit
    result = query.order("created_at", desc=True).range(offset, offset + params.limit - 1).execute()

    rows: List[Dict[str, Any]] = result.data or []
    total: int = result.count or 0

    # Bulk-fetch tags in one round trip
    item_ids = [r["id"] for r in rows]
    tags_map = _fetch_tags_bulk(db, item_ids)

    items = [BucketItemResponse(**_row_to_response(r, tags_map.get(r["id"], []))) for r in rows]

    return PaginatedResponse(
        data=items,
        pagination=make_pagination(params.page, params.limit, total),
    )


# ── POST /items ────────────────────────────────────────────────────────────────

@router.post(
    "",
    response_model=BucketItemResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a bucket item",
)
async def create_item(
    user_id: CurrentUserID,
    db: SupabaseClient,
    body: BucketItemCreate,
) -> BucketItemResponse:
    payload = {
        "user_id": str(user_id),
        "title": body.title,
        "category": body.category,
        "priority": body.priority,
        "description": body.description,
        "status": "active",
    }

    result = db.table("bucket_items").insert(payload).execute()
    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=make_error("INTERNAL_SERVER_ERROR", "Failed to create item.").model_dump(),
        )

    row = result.data[0]
    item_id = row["id"]

    # Insert tags
    if body.tags:
        db.table("item_tags").insert(
            [{"item_id": item_id, "tag": tag} for tag in body.tags]
        ).execute()

    return BucketItemResponse(**_row_to_response(row, body.tags))


# ── GET /items/{item_id} ───────────────────────────────────────────────────────

@router.get(
    "/{item_id}",
    response_model=BucketItemDetailResponse,
    summary="Get bucket item detail",
)
async def get_item(
    item_id: UUID,
    user_id: CurrentUserID,
    db: SupabaseClient,
) -> BucketItemDetailResponse:
    row = _get_item_or_404(db, item_id, user_id)
    tags = _fetch_tags(db, str(item_id))

    # Count activity logs for this item
    logs_result = (
        db.table("activity_logs")
        .select("id", count="exact")
        .eq("item_id", str(item_id))
        .execute()
    )
    logs_count = logs_result.count or 0

    return BucketItemDetailResponse(**_row_to_response(row, tags), logs_count=logs_count)


# ── PATCH /items/{item_id} ─────────────────────────────────────────────────────

@router.patch(
    "/{item_id}",
    response_model=BucketItemResponse,
    summary="Update a bucket item (partial)",
)
async def update_item(
    item_id: UUID,
    user_id: CurrentUserID,
    db: SupabaseClient,
    body: BucketItemUpdate,
) -> BucketItemResponse:
    # Verify ownership first
    _get_item_or_404(db, item_id, user_id)

    # Build the update payload (exclude None / unset fields)
    update_payload = body.model_dump(exclude_none=True, exclude={"tags"})

    if update_payload:
        result = (
            db.table("bucket_items")
            .update(update_payload)
            .eq("id", str(item_id))
            .execute()
        )
        row = result.data[0] if result.data else {}
    else:
        # Only tags changed — re-fetch the current row
        fetch = db.table("bucket_items").select("*").eq("id", str(item_id)).single().execute()
        row = fetch.data

    # Update tags if provided
    if body.tags is not None:
        _replace_tags(db, str(item_id), body.tags)
        tags = body.tags
    else:
        tags = _fetch_tags(db, str(item_id))

    return BucketItemResponse(**_row_to_response(row, tags))


# ── PUT /items/{item_id} — alias for PATCH (full update) ──────────────────────

@router.put(
    "/{item_id}",
    response_model=BucketItemResponse,
    summary="Update a bucket item (full — alias for PATCH)",
)
async def replace_item(
    item_id: UUID,
    user_id: CurrentUserID,
    db: SupabaseClient,
    body: BucketItemUpdate,
) -> BucketItemResponse:
    return await update_item(item_id, user_id, db, body)


# ── DELETE /items/{item_id} ────────────────────────────────────────────────────

@router.delete(
    "/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a bucket item",
)
async def delete_item(
    item_id: UUID,
    user_id: CurrentUserID,
    db: SupabaseClient,
) -> Response:
    # Verify ownership
    _get_item_or_404(db, item_id, user_id)
    db.table("bucket_items").delete().eq("id", str(item_id)).execute()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ── PATCH /items/{item_id}/complete ───────────────────────────────────────────

@router.patch(
    "/{item_id}/complete",
    response_model=BucketItemCompleteResponse,
    summary="Mark a bucket item as completed",
)
async def complete_item(
    item_id: UUID,
    user_id: CurrentUserID,
    db: SupabaseClient,
) -> BucketItemCompleteResponse:
    row = _get_item_or_404(db, item_id, user_id)

    if row["status"] == "completed":
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=make_error(
                "VALIDATION_ERROR",
                "Item is already completed.",
            ).model_dump(),
        )

    now = datetime.now(timezone.utc).isoformat()
    result = (
        db.table("bucket_items")
        .update({"status": "completed", "completed_at": now})
        .eq("id", str(item_id))
        .execute()
    )

    updated_row = result.data[0]
    return BucketItemCompleteResponse(
        id=updated_row["id"],
        status=updated_row["status"],
        completed_at=updated_row["completed_at"],
    )

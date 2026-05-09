"""
Weekly recommendation endpoints — Phase 2 implementation.

Endpoints (all require Supabase JWT authentication):
    GET  /recommendations/current          — get or create this week's recommendation
    GET  /recommendations/history          — paginated history
    POST /recommendations/generate-now    — force regenerate (dev helper)
    POST /recommendations/{rec_id}/accept — accept a recommendation
    POST /recommendations/{rec_id}/skip   — skip a recommendation
"""

from __future__ import annotations

import logging
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, HTTPException, Path, Query, status

from config import get_settings
from database import CurrentUserID, SupabaseClient
from schemas.common import make_error
from schemas.recommendation import (
    AcceptSkipResponse,
    RecommendationHistoryResponse,
    RecommendationResponse,
)
from services.recommender import RecommenderService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/recommendations", tags=["Recommendations"])


# ── GET /recommendations/current ──────────────────────────────────────────────

@router.get(
    "/current",
    response_model=RecommendationResponse,
    summary="Get or create this week's recommendation",
)
async def get_current_recommendation(
    user_id: CurrentUserID,
    db: SupabaseClient,
) -> RecommendationResponse:
    settings = get_settings()
    service = RecommenderService(supabase_client=db, settings=settings)
    result = await service.get_or_create_current_recommendation(user_id)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=make_error(
                "RECOMMENDATION_NOT_FOUND",
                "No recommendation found for the current week.",
            ).model_dump(),
        )
    return RecommendationResponse(**result)


# ── GET /recommendations/history ──────────────────────────────────────────────

@router.get(
    "/history",
    response_model=RecommendationHistoryResponse,
    summary="Get paginated recommendation history",
)
async def get_recommendation_history(
    user_id: CurrentUserID,
    db: SupabaseClient,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=10, ge=1, le=50),
) -> RecommendationHistoryResponse:
    settings = get_settings()
    service = RecommenderService(supabase_client=db, settings=settings)
    result = await service.get_history(user_id, page, limit)
    return RecommendationHistoryResponse(**result)


# ── POST /recommendations/generate-now ────────────────────────────────────────
# NOTE: Must be declared BEFORE /{rec_id}/... routes to avoid path conflict.

@router.post(
    "/generate-now",
    response_model=RecommendationResponse,
    summary="Force-regenerate this week's recommendation (dev helper)",
)
async def generate_recommendation_now(
    user_id: CurrentUserID,
    db: SupabaseClient,
) -> RecommendationResponse:
    """
    Delete the existing recommendation for the current week (if any) and
    immediately generate a new one.  Intended for development/testing only.
    """
    from datetime import date, timedelta

    # Determine this week's Monday
    today = date.today()
    week_start = today - timedelta(days=today.weekday())

    # Delete any existing recommendation for this week
    db.table("weekly_recommendations").delete().eq(
        "user_id", str(user_id)
    ).eq("week_start", week_start.isoformat()).execute()

    settings = get_settings()
    service = RecommenderService(supabase_client=db, settings=settings)
    result = await service.get_or_create_current_recommendation(user_id)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=make_error(
                "RECOMMENDATION_NOT_FOUND",
                "No active bucket items found to generate a recommendation.",
            ).model_dump(),
        )
    return RecommendationResponse(**result)


# ── POST /recommendations/{rec_id}/accept ─────────────────────────────────────

@router.post(
    "/{rec_id}/accept",
    response_model=AcceptSkipResponse,
    summary="Accept a recommendation",
)
async def accept_recommendation(
    rec_id: Annotated[UUID, Path(...)],
    user_id: CurrentUserID,
    db: SupabaseClient,
) -> AcceptSkipResponse:
    settings = get_settings()
    service = RecommenderService(supabase_client=db, settings=settings)
    result = await service.accept_recommendation(rec_id, user_id)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=make_error(
                "RECOMMENDATION_NOT_FOUND",
                "No recommendation found with the given ID.",
            ).model_dump(),
        )
    return AcceptSkipResponse(**result)


# ── POST /recommendations/{rec_id}/skip ───────────────────────────────────────

@router.post(
    "/{rec_id}/skip",
    response_model=AcceptSkipResponse,
    summary="Skip a recommendation",
)
async def skip_recommendation(
    rec_id: Annotated[UUID, Path(...)],
    user_id: CurrentUserID,
    db: SupabaseClient,
) -> AcceptSkipResponse:
    settings = get_settings()
    service = RecommenderService(supabase_client=db, settings=settings)
    result = await service.skip_recommendation(rec_id, user_id)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=make_error(
                "RECOMMENDATION_NOT_FOUND",
                "No recommendation found with the given ID.",
            ).model_dump(),
        )
    return AcceptSkipResponse(**result)

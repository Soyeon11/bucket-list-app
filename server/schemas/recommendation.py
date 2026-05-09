"""
Pydantic v2 schemas for the weekly recommendation endpoints.

Covers the recommendation response, history, and accept/skip action responses
as defined in API_SPEC.md Phase 2.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import List, Literal, Optional
from uuid import UUID

from pydantic import BaseModel, Field


# ── Shared configuration ───────────────────────────────────────────────────────

_cfg = {"from_attributes": True}


# ── Sub-schemas ────────────────────────────────────────────────────────────────

class RecommendationItemRef(BaseModel):
    """Compact reference to the bucket item embedded in a recommendation."""

    model_config = _cfg

    id: UUID
    title: str
    category: str
    priority: str


class ScoreBreakdown(BaseModel):
    """Breakdown of the individual scoring components."""

    model_config = _cfg

    priority_score: float
    recency_bonus: float
    season_score: float
    weather_score: float


# ── Primary response schemas ───────────────────────────────────────────────────

class RecommendationResponse(BaseModel):
    """Full recommendation record returned by GET /recommendations/current."""

    model_config = _cfg

    id: UUID
    week_start: date
    item: RecommendationItemRef
    reason: Optional[str] = None
    score_breakdown: Optional[ScoreBreakdown] = None
    status: Literal["pending", "accepted", "skipped"]
    accepted_at: Optional[datetime] = None
    skipped_at: Optional[datetime] = None
    created_at: datetime


class RecommendationHistoryItem(BaseModel):
    """Condensed recommendation row used in the history list."""

    model_config = _cfg

    id: UUID
    week_start: date
    item: RecommendationItemRef
    status: Literal["pending", "accepted", "skipped"]
    accepted_at: Optional[datetime] = None


class RecommendationHistoryResponse(BaseModel):
    """Paginated list of past recommendations."""

    model_config = _cfg

    data: List[RecommendationHistoryItem]
    pagination: dict


class AcceptSkipResponse(BaseModel):
    """Minimal response returned after accepting or skipping a recommendation."""

    model_config = _cfg

    id: UUID
    status: str
    accepted_at: Optional[datetime] = None
    skipped_at: Optional[datetime] = None

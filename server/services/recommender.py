"""
Weekly recommendation service.

RecommenderService implements the full scoring pipeline:
  1. Priority score     — item priority tier mapped to fixed points
  2. Recency bonus      — weeks since last recommendation (capped)
  3. Season score       — category weight for current season (KST)
  4. Weather score      — category weight for current weather condition

The service interacts with Supabase via the service-role client and is
designed to be used as a FastAPI dependency-injected singleton.
"""

from __future__ import annotations

import logging
from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID

from services.season import SEASON_MAP, WEATHER_MAP, get_current_season

logger = logging.getLogger(__name__)

# KST offset used for week-boundary calculations
_KST = timezone(timedelta(hours=9))

# Priority tier → fixed points
_PRIORITY_SCORE: dict[str, float] = {
    "high": 40.0,
    "medium": 25.0,
    "low": 10.0,
}


# ── Reason text builder ───────────────────────────────────────────────────────

def _build_reason(season: str, weather: str, priority: str) -> str:
    season_kr = {"spring": "봄", "summer": "여름", "fall": "가을", "winter": "겨울"}
    weather_kr = {
        "clear": "맑은 날씨",
        "clouds": "흐린 날씨",
        "rain": "비 오는 날씨",
        "snow": "눈 오는 날씨",
        "extreme": "날씨",
        "neutral": "날씨",
    }
    priority_kr = {"high": "높은 우선순위", "medium": "보통 우선순위", "low": "낮은 우선순위"}
    return (
        f"이번 {season_kr[season]} 계절과 {weather_kr[weather]}, "
        f"그리고 {priority_kr[priority]}를 고려해 선정했어요."
    )


# ── Service class ─────────────────────────────────────────────────────────────

class RecommenderService:
    """Scoring and persistence layer for weekly bucket-list recommendations."""

    def __init__(self, supabase_client: Any, settings: Any) -> None:
        self._db = supabase_client
        self._settings = settings

    # ── Public API ─────────────────────────────────────────────────────────────

    async def get_or_create_current_recommendation(
        self, user_id: UUID
    ) -> Optional[Dict[str, Any]]:
        """
        Return the recommendation for the current ISO week, creating one if needed.

        Returns None when the user has no active bucket items.
        """
        week_start = await self._get_week_start()

        # 1. Check for an existing record this week
        existing = await self._fetch_recommendation(user_id, week_start)
        if existing:
            return await self._hydrate_recommendation(existing)

        # 2. Score all active items and pick the best
        items = await self._fetch_active_items(user_id)
        if not items:
            return None

        season = get_current_season()
        weather_condition = await self._get_weather(user_id)

        scored = [
            (item, self._calculate_score(item, season, weather_condition))
            for item in items
        ]
        scored.sort(key=lambda t: t[1], reverse=True)
        best_item, _ = scored[0]

        score_breakdown = self._build_score_breakdown(best_item, season, weather_condition)
        reason = _build_reason(season, weather_condition, best_item.get("priority", "medium"))

        rec = await self._create_recommendation(
            user_id=user_id,
            item_id=UUID(best_item["id"]),
            score_breakdown=score_breakdown,
            reason=reason,
            week_start=week_start,
        )
        return await self._hydrate_recommendation(rec)

    async def accept_recommendation(
        self, rec_id: UUID, user_id: UUID
    ) -> Optional[Dict[str, Any]]:
        """Set status to 'accepted' and stamp accepted_at."""
        now = datetime.now(timezone.utc).isoformat()
        result = (
            self._db.table("weekly_recommendations")
            .update({"status": "accepted", "accepted_at": now})
            .eq("id", str(rec_id))
            .eq("user_id", str(user_id))
            .execute()
        )
        if not result.data:
            return None
        return result.data[0]

    async def skip_recommendation(
        self, rec_id: UUID, user_id: UUID
    ) -> Optional[Dict[str, Any]]:
        """Set status to 'skipped' and stamp skipped_at."""
        now = datetime.now(timezone.utc).isoformat()
        result = (
            self._db.table("weekly_recommendations")
            .update({"status": "skipped", "skipped_at": now})
            .eq("id", str(rec_id))
            .eq("user_id", str(user_id))
            .execute()
        )
        if not result.data:
            return None
        return result.data[0]

    async def get_history(
        self, user_id: UUID, page: int, limit: int
    ) -> Dict[str, Any]:
        """Return paginated recommendation history with embedded item details."""
        offset = (page - 1) * limit

        result = (
            self._db.table("weekly_recommendations")
            .select("*, bucket_items(id, title, category, priority)", count="exact")
            .eq("user_id", str(user_id))
            .order("week_start", desc=True)
            .range(offset, offset + limit - 1)
            .execute()
        )

        rows: List[Dict[str, Any]] = result.data or []
        total: int = result.count or 0

        hydrated = [self._flatten_item_join(r) for r in rows]

        return {
            "data": hydrated,
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total,
                "has_next": (page * limit) < total,
            },
        }

    # ── Private helpers ────────────────────────────────────────────────────────

    async def _get_week_start(self) -> date:
        """Return the Monday of the current week in KST."""
        today = datetime.now(_KST).date()
        # weekday(): Monday=0 … Sunday=6
        return today - timedelta(days=today.weekday())

    async def _fetch_active_items(self, user_id: UUID) -> List[Dict[str, Any]]:
        """Fetch all active bucket items for the given user."""
        result = (
            self._db.table("bucket_items")
            .select("*")
            .eq("user_id", str(user_id))
            .eq("status", "active")
            .execute()
        )
        return result.data or []

    async def _fetch_recommendation(
        self, user_id: UUID, week_start: date
    ) -> Optional[Dict[str, Any]]:
        """Return an existing recommendation row for user + week, or None."""
        result = (
            self._db.table("weekly_recommendations")
            .select("*")
            .eq("user_id", str(user_id))
            .eq("week_start", str(week_start))
            .maybe_single()
            .execute()
        )
        return result.data or None

    async def _create_recommendation(
        self,
        user_id: UUID,
        item_id: UUID,
        score_breakdown: Dict[str, float],
        reason: str,
        week_start: date,
    ) -> Dict[str, Any]:
        """Insert a new weekly_recommendations row and update last_recommended_at."""
        now = datetime.now(timezone.utc).isoformat()

        payload = {
            "user_id": str(user_id),
            "item_id": str(item_id),
            "week_start": str(week_start),
            "status": "pending",
            "reason": reason,
            "score_breakdown": score_breakdown,
            "created_at": now,
        }

        result = self._db.table("weekly_recommendations").insert(payload).execute()
        rec = result.data[0]

        # Update last_recommended_at on the bucket item
        self._db.table("bucket_items").update(
            {"last_recommended_at": now}
        ).eq("id", str(item_id)).execute()

        return rec

    def _calculate_score(
        self, item: Dict[str, Any], season: str, weather_condition: str
    ) -> float:
        """Compute total recommendation score for an item."""
        breakdown = self._build_score_breakdown(item, season, weather_condition)
        return sum(breakdown.values())

    def _build_score_breakdown(
        self, item: Dict[str, Any], season: str, weather_condition: str
    ) -> Dict[str, float]:
        """Build the four-component score breakdown dict."""
        category: str = item.get("category", "etc")
        priority: str = item.get("priority", "medium")
        last_recommended_at: Optional[str] = item.get("last_recommended_at")

        # Priority component
        priority_score = _PRIORITY_SCORE.get(priority, 25.0)

        # Recency bonus: min(weeks_since * 4, 20); never recommended → 20
        if last_recommended_at is None:
            recency_bonus = 20.0
        else:
            try:
                last_dt = datetime.fromisoformat(last_recommended_at)
                if last_dt.tzinfo is None:
                    last_dt = last_dt.replace(tzinfo=timezone.utc)
                weeks_since = (datetime.now(timezone.utc) - last_dt).days // 7
                recency_bonus = min(weeks_since * 4.0, 20.0)
            except (ValueError, TypeError):
                recency_bonus = 20.0

        # Season component
        season_weights = SEASON_MAP.get(season, {})
        season_score = float(season_weights.get(category, 10))

        # Weather component
        if weather_condition == "neutral":
            weather_score = 10.0
        else:
            weather_weights = WEATHER_MAP.get(weather_condition, {})
            weather_score = float(weather_weights.get(category, 10))

        return {
            "priority_score": priority_score,
            "recency_bonus": recency_bonus,
            "season_score": season_score,
            "weather_score": weather_score,
        }

    async def _get_weather(self, user_id: UUID) -> str:
        """
        Attempt to fetch weather for the user's location.

        Falls back to "neutral" when no location data is available or the
        API key is not configured.
        """
        # Seoul default coordinates when user location is unavailable
        default_lat, default_lon = 37.5665, 126.9780

        api_key: str = getattr(self._settings, "openweather_api_key", "")
        if not api_key:
            return "neutral"

        try:
            from services.weather import get_weather_condition
            return await get_weather_condition(default_lat, default_lon, api_key)
        except Exception as exc:
            logger.warning("Weather fetch failed: %s", exc)
            return "neutral"

    async def _hydrate_recommendation(
        self, rec: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Enrich a recommendation row with its associated bucket item fields.

        Fetches the bucket item and embeds it as the 'item' key so the
        response matches RecommendationResponse schema expectations.
        """
        item_id = rec.get("item_id")
        if item_id:
            item_result = (
                self._db.table("bucket_items")
                .select("id, title, category, priority")
                .eq("id", str(item_id))
                .maybe_single()
                .execute()
            )
            rec = {**rec, "item": item_result.data or {}}
        return rec

    @staticmethod
    def _flatten_item_join(row: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalise a row that includes a PostgREST nested join under 'bucket_items'
        into the expected 'item' key used by the schema.
        """
        joined = row.pop("bucket_items", None)
        if joined:
            row["item"] = joined
        return row

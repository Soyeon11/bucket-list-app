"""
Season and weather scoring maps used by the recommendation algorithm.

get_current_season() returns the Korean Standard Time (KST) season string.
SEASON_MAP and WEATHER_MAP provide per-category score weights.
"""

from __future__ import annotations

from datetime import datetime, timezone, timedelta
from typing import Literal

# KST is UTC+9
_KST = timezone(timedelta(hours=9))

SeasonStr = Literal["spring", "summer", "fall", "winter"]

# ── Season scoring weights by category ────────────────────────────────────────

SEASON_MAP: dict[str, dict[str, int]] = {
    "spring": {"travel": 18, "outdoor": 20, "food": 12, "fitness": 16, "culture": 14, "hobby": 12, "etc": 12},
    "summer": {"travel": 20, "outdoor": 18, "food": 14, "fitness": 14, "culture": 10, "hobby": 12, "etc": 10},
    "fall":   {"travel": 16, "outdoor": 14, "food": 18, "fitness": 14, "culture": 18, "hobby": 16, "etc": 14},
    "winter": {"travel": 10, "outdoor":  8, "food": 20, "fitness": 12, "culture": 20, "hobby": 18, "etc": 16},
}

# ── Weather scoring weights by category ───────────────────────────────────────

WEATHER_MAP: dict[str, dict[str, int]] = {
    "clear":   {"outdoor": 20, "travel": 18, "fitness": 18, "food": 10, "culture": 10, "hobby": 10, "etc": 10},
    "clouds":  {"outdoor": 12, "travel": 12, "fitness": 12, "food": 14, "culture": 16, "hobby": 16, "etc": 14},
    "rain":    {"outdoor":  2, "travel":  4, "fitness":  4, "food": 18, "culture": 20, "hobby": 18, "etc": 16},
    "snow":    {"outdoor": 16, "travel": 14, "fitness": 10, "food": 16, "culture": 14, "hobby": 14, "etc": 12},
    "extreme": {"outdoor":  0, "travel":  0, "fitness":  0, "food": 10, "culture": 10, "hobby": 10, "etc": 10},
}


# ── Season helper ─────────────────────────────────────────────────────────────

def get_current_season() -> SeasonStr:
    """Return the current season name based on KST month."""
    month = datetime.now(_KST).month
    if 3 <= month <= 5:
        return "spring"
    if 6 <= month <= 8:
        return "summer"
    if 9 <= month <= 11:
        return "fall"
    return "winter"  # December, January, February

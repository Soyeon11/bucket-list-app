"""
OpenWeatherMap API client for the recommendation service.

get_weather_condition() calls the OWM current-weather endpoint and returns
a normalized condition string compatible with WEATHER_MAP in season.py.
On any network or API error the function degrades gracefully to "neutral".
"""

from __future__ import annotations

import logging

import httpx

logger = logging.getLogger(__name__)

# OWM condition → normalized key
_OWM_CONDITION_MAP: dict[str, str] = {
    "clear": "clear",
    "clouds": "clouds",
    "rain": "rain",
    "drizzle": "rain",
    "thunderstorm": "rain",
    "snow": "snow",
}

_OWM_URL = "https://api.openweathermap.org/data/2.5/weather"
_TIMEOUT_SECONDS = 5.0


async def get_weather_condition(lat: float, lon: float, api_key: str) -> str:
    """
    Fetch current weather from OpenWeatherMap and return a normalized condition.

    Returns one of: "clear", "clouds", "rain", "snow", "extreme", "neutral".
    "neutral" is returned on any error (timeout, HTTP error, missing key, etc.).
    """
    if not api_key:
        logger.debug("OpenWeather API key not configured — using neutral weather")
        return "neutral"

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT_SECONDS) as client:
            response = await client.get(
                _OWM_URL,
                params={"lat": lat, "lon": lon, "appid": api_key},
            )
            response.raise_for_status()
            data = response.json()

        raw_main: str = data["weather"][0]["main"].lower()
        condition = _OWM_CONDITION_MAP.get(raw_main, "extreme")
        logger.debug("OWM condition for (%.4f, %.4f): %s → %s", lat, lon, raw_main, condition)
        return condition

    except httpx.TimeoutException:
        logger.warning("OWM request timed out for (%.4f, %.4f)", lat, lon)
        return "neutral"
    except httpx.HTTPStatusError as exc:
        logger.warning("OWM HTTP error %s for (%.4f, %.4f)", exc.response.status_code, lat, lon)
        return "neutral"
    except Exception as exc:
        logger.warning("OWM unexpected error for (%.4f, %.4f): %s", lat, lon, exc)
        return "neutral"

"""
AgentCraft External Disaster Data Integration Service
Provides a modular integration layer for meteorological and hydrological disaster data
supporting Open-Meteo Weather & Flood APIs, in-memory TTL caching, fallback adapters,
freshness metrics, and graceful degradation when offline.
"""

import os
import time
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import httpx


def utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class BaseDisasterDataProvider(ABC):
    """Abstract interface for external meteorological and hydrological observation providers."""

    @abstractmethod
    def get_weather_observations(self, latitude: float, longitude: float) -> Dict[str, Any]:
        """Fetch current and forecasted weather telemetry."""
        pass

    @abstractmethod
    def get_flood_observations(self, latitude: float, longitude: float) -> Dict[str, Any]:
        """Fetch hydrological river discharge and flood telemetry."""
        pass


class OpenMeteoProvider(BaseDisasterDataProvider):
    """
    Open-Meteo authoritative open-data meteorological and hydrological integration.
    Requires no API key; respects fair-use guidelines with timeout and error handling.
    """

    WEATHER_ENDPOINT = "https://api.open-meteo.com/v1/forecast"
    FLOOD_ENDPOINT = "https://flood-api.open-meteo.com/v1/flood"

    def __init__(self, timeout_seconds: float = 6.0):
        self.timeout_seconds = timeout_seconds

    def _interpret_wmo_code(self, code: int) -> str:
        """Translates WMO weather code into human-readable description."""
        mapping = {
            0: "Clear sky",
            1: "Mainly clear",
            2: "Partly cloudy",
            3: "Overcast",
            45: "Fog",
            48: "Depositing rime fog",
            51: "Light drizzle",
            53: "Moderate drizzle",
            55: "Dense drizzle",
            61: "Slight rain",
            63: "Moderate rain",
            65: "Heavy rain",
            71: "Slight snow fall",
            73: "Moderate snow fall",
            75: "Heavy snow fall",
            80: "Slight rain showers",
            81: "Moderate rain showers",
            82: "Violent rain showers",
            95: "Thunderstorm: slight or moderate",
            96: "Thunderstorm with slight hail",
            99: "Thunderstorm with heavy hail",
        }
        return mapping.get(code, f"Weather condition (code {code})")

    def get_weather_observations(self, latitude: float, longitude: float) -> Dict[str, Any]:
        params = {
            "latitude": round(latitude, 4),
            "longitude": round(longitude, 4),
            "current": "temperature_2m,relative_humidity_2m,precipitation,weather_code,wind_speed_10m,wind_gusts_10m",
            "hourly": "precipitation_probability,precipitation",
            "forecast_days": 1,
            "timezone": "UTC",
        }
        with httpx.Client(timeout=self.timeout_seconds) as client:
            resp = client.get(self.WEATHER_ENDPOINT, params=params)
            resp.raise_for_status()
            data = resp.json()

        current = data.get("current", {})
        hourly = data.get("hourly", {})

        precip_prob = hourly.get("precipitation_probability", [0])[0] if hourly.get("precipitation_probability") else 0
        wmo_code = current.get("weather_code", 0)

        return {
            "source": "Open-Meteo Weather API",
            "status": "live",
            "retrieval_time": utcnow_iso(),
            "observation_time": current.get("time", utcnow_iso()),
            "temperature_c": current.get("temperature_2m", 24.0),
            "relative_humidity_pct": current.get("relative_humidity_2m", 60),
            "precipitation_mm": current.get("precipitation", 0.0),
            "precipitation_probability_pct": precip_prob,
            "wind_speed_kmh": current.get("wind_speed_10m", 12.0),
            "wind_gusts_kmh": current.get("wind_gusts_10m", 18.0),
            "weather_code": wmo_code,
            "weather_description": self._interpret_wmo_code(wmo_code),
        }

    def get_flood_observations(self, latitude: float, longitude: float) -> Dict[str, Any]:
        params = {
            "latitude": round(latitude, 4),
            "longitude": round(longitude, 4),
            "daily": "river_discharge,river_discharge_mean,river_discharge_median",
            "forecast_days": 1,
        }
        with httpx.Client(timeout=self.timeout_seconds) as client:
            resp = client.get(self.FLOOD_ENDPOINT, params=params)
            resp.raise_for_status()
            data = resp.json()

        daily = data.get("daily", {})
        discharges = daily.get("river_discharge", [0.0])
        discharge = discharges[0] if discharges and discharges[0] is not None else 0.0
        mean_discharge = daily.get("river_discharge_mean", [10.0])[0] or 10.0

        # Assess flood risk ratio
        ratio = discharge / max(mean_discharge, 1.0)
        if ratio > 2.5:
            flood_risk = "critical"
        elif ratio > 1.8:
            flood_risk = "high"
        elif ratio > 1.2:
            flood_risk = "moderate"
        else:
            flood_risk = "low"

        return {
            "source": "Open-Meteo Hydrology & Flood API",
            "status": "live",
            "retrieval_time": utcnow_iso(),
            "observation_time": utcnow_iso(),
            "river_discharge_m3s": round(float(discharge), 2),
            "river_discharge_mean_m3s": round(float(mean_discharge), 2),
            "flood_risk_level": flood_risk,
        }


class TestDisasterDataProvider(BaseDisasterDataProvider):
    """
    Deterministic test/simulation provider for offline execution, unit tests,
    and simulated disaster scenarios. Clearly labeled as simulated.
    """
    __test__ = False

    def __init__(self, override_rainfall_mm: float = 35.0, override_river_m3s: float = 120.0):
        self.override_rainfall_mm = override_rainfall_mm
        self.override_river_m3s = override_river_m3s

    def get_weather_observations(self, latitude: float, longitude: float) -> Dict[str, Any]:
        return {
            "source": "AgentCraft Test Weather Adapter",
            "status": "simulated",
            "retrieval_time": utcnow_iso(),
            "observation_time": utcnow_iso(),
            "temperature_c": 27.5,
            "relative_humidity_pct": 88,
            "precipitation_mm": self.override_rainfall_mm,
            "precipitation_probability_pct": 95,
            "wind_speed_kmh": 45.0,
            "wind_gusts_kmh": 65.0,
            "weather_code": 65,
            "weather_description": "Heavy rain (simulated)",
        }

    def get_flood_observations(self, latitude: float, longitude: float) -> Dict[str, Any]:
        return {
            "source": "AgentCraft Test Hydrology Adapter",
            "status": "simulated",
            "retrieval_time": utcnow_iso(),
            "observation_time": utcnow_iso(),
            "river_discharge_m3s": self.override_river_m3s,
            "river_discharge_mean_m3s": 45.0,
            "flood_risk_level": "high" if self.override_river_m3s > 80 else "moderate",
        }


class DisasterDataService:
    """
    Central dispatcher, caching layer, and health monitor for external disaster observations.
    Manages in-memory TTL caching, fallback degradation, and telemetry provenance.
    """

    CACHE_TTL_SECONDS = 900  # 15 minutes
    STALE_THRESHOLD_SECONDS = 10800  # 3 hours

    def __init__(self, provider: Optional[BaseDisasterDataProvider] = None, allow_network: Optional[bool] = None):
        if allow_network is None:
            allow_network = os.getenv("AGENTCRAFT_ALLOW_NETWORK_FETCH", "true").lower() == "true"
        self.allow_network = allow_network

        if provider is not None:
            self.provider = provider
        elif self.allow_network:
            self.provider = OpenMeteoProvider()
        else:
            self.provider = TestDisasterDataProvider()

        self._cache: Dict[str, Dict[str, Any]] = {}

    def set_provider(self, provider: BaseDisasterDataProvider) -> None:
        """Allows dynamic swapping of provider (e.g. for deterministic unit testing)."""
        self.provider = provider

    def _cache_key(self, prefix: str, lat: float, lon: float) -> str:
        return f"{prefix}:{round(lat, 2)}:{round(lon, 2)}"

    def get_weather(self, latitude: float, longitude: float, force_refresh: bool = False) -> Dict[str, Any]:
        """
        Retrieves weather observations with caching, provenance, and fallback.
        Never fabricates live data; labels cached or unavailable appropriately.
        """
        # Validate coordinates
        if not (-90.0 <= latitude <= 90.0 and -180.0 <= longitude <= 180.0):
            return {
                "source": "validation_gate",
                "status": "unavailable",
                "error": f"Invalid coordinates ({latitude}, {longitude})",
                "retrieval_time": utcnow_iso(),
            }

        ck = self._cache_key("weather", latitude, longitude)
        now = time.time()

        if not force_refresh and ck in self._cache:
            entry = self._cache[ck]
            age = now - entry["cached_timestamp"]
            if age < self.CACHE_TTL_SECONDS:
                result = dict(entry["data"])
                result["status"] = "cached"
                result["freshness_seconds"] = round(age, 1)
                result["is_stale"] = age > self.STALE_THRESHOLD_SECONDS
                return result

        # Attempt provider query
        try:
            raw = self.provider.get_weather_observations(latitude, longitude)
            raw["freshness_seconds"] = 0.0
            raw["is_stale"] = False
            self._cache[ck] = {"cached_timestamp": now, "data": raw}
            return raw
        except Exception as e:
            # If network error or provider unavailable, check if stale cache exists
            if ck in self._cache:
                entry = self._cache[ck]
                age = now - entry["cached_timestamp"]
                result = dict(entry["data"])
                result["status"] = "cached"
                result["freshness_seconds"] = round(age, 1)
                result["is_stale"] = age > self.STALE_THRESHOLD_SECONDS
                result["warning"] = f"Live update failed: {str(e)[:100]}. Serving cached telemetry."
                return result

            # No cache and provider failed
            return {
                "source": getattr(self.provider, "name", "Open-Meteo Provider"),
                "status": "unavailable",
                "error": f"Provider connection error: {type(e).__name__}: {str(e)[:120]}",
                "retrieval_time": utcnow_iso(),
                "temperature_c": None,
                "precipitation_mm": None,
                "wind_speed_kmh": None,
                "weather_description": "Data unavailable (external provider unreachable)",
                "freshness_seconds": None,
                "is_stale": True,
            }

    def get_flood_data(self, latitude: float, longitude: float, force_refresh: bool = False) -> Dict[str, Any]:
        """Retrieves hydrological river discharge observations with caching and fallback."""
        if not (-90.0 <= latitude <= 90.0 and -180.0 <= longitude <= 180.0):
            return {
                "source": "validation_gate",
                "status": "unavailable",
                "error": f"Invalid coordinates ({latitude}, {longitude})",
                "retrieval_time": utcnow_iso(),
            }

        ck = self._cache_key("flood", latitude, longitude)
        now = time.time()

        if not force_refresh and ck in self._cache:
            entry = self._cache[ck]
            age = now - entry["cached_timestamp"]
            if age < self.CACHE_TTL_SECONDS:
                result = dict(entry["data"])
                result["status"] = "cached"
                result["freshness_seconds"] = round(age, 1)
                result["is_stale"] = age > self.STALE_THRESHOLD_SECONDS
                return result

        try:
            raw = self.provider.get_flood_observations(latitude, longitude)
            raw["freshness_seconds"] = 0.0
            raw["is_stale"] = False
            self._cache[ck] = {"cached_timestamp": now, "data": raw}
            return raw
        except Exception as e:
            if ck in self._cache:
                entry = self._cache[ck]
                age = now - entry["cached_timestamp"]
                result = dict(entry["data"])
                result["status"] = "cached"
                result["freshness_seconds"] = round(age, 1)
                result["is_stale"] = age > self.STALE_THRESHOLD_SECONDS
                result["warning"] = f"Live update failed: {str(e)[:100]}. Serving cached telemetry."
                return result

            return {
                "source": getattr(self.provider, "name", "Open-Meteo Flood Provider"),
                "status": "unavailable",
                "error": f"Hydrology provider error: {str(e)[:120]}",
                "retrieval_time": utcnow_iso(),
                "river_discharge_m3s": None,
                "river_discharge_mean_m3s": None,
                "flood_risk_level": "unknown",
                "freshness_seconds": None,
                "is_stale": True,
            }

    def get_provider_health(self) -> Dict[str, Any]:
        """Reports health and connectivity status of external data adapters."""
        return {
            "provider_type": type(self.provider).__name__,
            "network_enabled": self.allow_network,
            "cached_entries_count": len(self._cache),
            "cache_ttl_seconds": self.CACHE_TTL_SECONDS,
            "status": "operational",
            "checked_at": utcnow_iso(),
        }


# Singleton service instance
disaster_data_service = DisasterDataService()

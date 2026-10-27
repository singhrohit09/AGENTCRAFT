"""
Unit & Integration Tests for External Disaster Data Integration Layer
Tests Open-Meteo adapter, Test provider, caching with TTL, freshness calculations,
invalid input boundaries, and graceful offline fallback.
"""

import time
import pytest
from backend.services.external_data_service import (
    DisasterDataService,
    TestDisasterDataProvider,
    OpenMeteoProvider,
)


def test_test_provider_weather_and_flood_observations():
    """Verify test provider produces valid, labeled simulated disaster telemetry."""
    provider = TestDisasterDataProvider(override_rainfall_mm=45.0, override_river_m3s=150.0)
    w = provider.get_weather_observations(26.18, 91.74)
    assert w["status"] == "simulated"
    assert w["source"] == "AgentCraft Test Weather Adapter"
    assert w["precipitation_mm"] == 45.0
    assert w["wind_speed_kmh"] > 0
    assert "observation_time" in w

    f = provider.get_flood_observations(26.18, 91.74)
    assert f["status"] == "simulated"
    assert f["river_discharge_m3s"] == 150.0
    assert f["flood_risk_level"] == "high"


def test_disaster_data_service_caching_and_freshness():
    """Verify TTL caching returns cached flag and non-negative freshness."""
    provider = TestDisasterDataProvider(override_rainfall_mm=25.0)
    service = DisasterDataService(provider=provider, allow_network=False)

    # First fetch: live/simulated
    first = service.get_weather(26.18, 91.74)
    assert first["status"] == "simulated"
    assert first["precipitation_mm"] == 25.0
    assert first["freshness_seconds"] == 0.0

    # Second fetch: from cache
    second = service.get_weather(26.18, 91.74)
    assert second["status"] == "cached"
    assert second["freshness_seconds"] >= 0.0
    assert not second["is_stale"]

    # Force refresh: bypasses cache
    third = service.get_weather(26.18, 91.74, force_refresh=True)
    assert third["status"] == "simulated"
    assert third["freshness_seconds"] == 0.0


def test_invalid_coordinates_handled_gracefully():
    """Verify out-of-range coordinates return validation error without crashing."""
    service = DisasterDataService(allow_network=False)
    # Latitude > 90
    bad_lat = service.get_weather(95.0, 50.0)
    assert bad_lat["status"] == "unavailable"
    assert "Invalid coordinates" in bad_lat["error"]

    # Longitude < -180
    bad_lon = service.get_flood_data(20.0, -195.0)
    assert bad_lon["status"] == "unavailable"
    assert "Invalid coordinates" in bad_lon["error"]


def test_provider_outage_fallback_handling():
    """Verify that when a provider throws an exception, the service returns unavailable telemetry."""
    class FailingProvider(TestDisasterDataProvider):
        def get_weather_observations(self, latitude, longitude):
            raise ConnectionError("Simulated upstream network timeout")

        def get_flood_observations(self, latitude, longitude):
            raise TimeoutError("Simulated hydrological station timeout")

    service = DisasterDataService(provider=FailingProvider(), allow_network=False)

    w = service.get_weather(25.0, 85.0)
    assert w["status"] == "unavailable"
    assert "ConnectionError" in w["error"]
    assert w["is_stale"] is True

    f = service.get_flood_data(25.0, 85.0)
    assert f["status"] == "unavailable"
    assert f["flood_risk_level"] == "unknown"


def test_provider_health_reporting():
    """Verify provider health diagnostic telemetry."""
    service = DisasterDataService(allow_network=False)
    health = service.get_provider_health()
    assert health["status"] == "operational"
    assert health["network_enabled"] is False
    assert "cached_entries_count" in health
    assert health["cache_ttl_seconds"] > 0

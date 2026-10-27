"""
Unit & Integration Tests for Explainable Disaster Risk Assessment Engine
Tests normalization boundaries, category thresholds, missing coordinates,
uncertainty penalties, status modifiers, and transparent factor provenance.
"""

import uuid
import pytest
from backend.rakshagrid.models import Incident
from backend.services.risk_engine import DisasterRiskEngine, disaster_risk_engine


def test_score_to_category_thresholds():
    """Verify exact score mapping to documented risk categories: Low 0-24, Moderate 25-49, High 50-74, Critical 75-100."""
    assert DisasterRiskEngine.score_to_category(0.0) == "Low"
    assert DisasterRiskEngine.score_to_category(24.0) == "Low"
    assert DisasterRiskEngine.score_to_category(24.9) == "Low"
    assert DisasterRiskEngine.score_to_category(25.0) == "Moderate"
    assert DisasterRiskEngine.score_to_category(49.0) == "Moderate"
    assert DisasterRiskEngine.score_to_category(49.9) == "Moderate"
    assert DisasterRiskEngine.score_to_category(50.0) == "High"
    assert DisasterRiskEngine.score_to_category(74.0) == "High"
    assert DisasterRiskEngine.score_to_category(74.9) == "High"
    assert DisasterRiskEngine.score_to_category(75.0) == "Critical"
    assert DisasterRiskEngine.score_to_category(100.0) == "Critical"


def test_critical_flood_incident_assessment():
    """Verify compound high-risk flood incident scoring and explainability."""
    inc = Incident(
        id=uuid.uuid4(),
        incident_code="TEST-FL-001",
        title="Critical Flood Breach",
        category="flood",
        severity="critical",
        status="response_active",
        latitude=26.18,
        longitude=91.74,
        location_description="Sector 4 River Embankment",
        affected_population=6000,
        verification_status="verified",
    )

    mock_weather = {
        "source": "Mock Telemetry",
        "status": "simulated",
        "precipitation_mm": 65.0,
        "wind_speed_kmh": 40.0,
        "freshness_seconds": 12.0,
        "is_stale": False,
    }
    mock_flood = {
        "source": "Mock Hydrology",
        "status": "simulated",
        "flood_risk_level": "critical",
        "freshness_seconds": 12.0,
        "is_stale": False,
    }

    result = disaster_risk_engine.assess_incident(
        inc,
        weather_data=mock_weather,
        flood_data=mock_flood,
        persist=False,
    )

    # Assertions
    assert 0.0 <= result["calculated_risk_score"] <= 100.0
    assert result["risk_level"] == "Critical"
    assert result["reported_severity"] == "critical"
    assert result["confidence_score"] >= 0.8
    assert len(result["scoring_breakdown"]) >= 5
    assert len(result["recommended_interventions"]) >= 2
    assert "scientific_limitation_disclaimer" in result


def test_missing_coordinates_penalty_and_data_gap():
    """Verify that missing coordinates apply uncertainty buffer and identify data gaps."""
    inc = Incident(
        id=uuid.uuid4(),
        incident_code="TEST-NO-COORD",
        title="Unlocated Wildfire Smoke",
        category="wildfire",
        severity="medium",
        status="reported",
        latitude=None,
        longitude=None,
        affected_population=50,
        verification_status="unverified",
    )

    result = disaster_risk_engine.assess_incident(inc, persist=False)
    assert 0.0 <= result["calculated_risk_score"] <= 100.0
    assert result["uncertainty_points"] > 0
    assert any("coordinates missing" in gap.lower() for gap in result["data_gaps"])
    assert any("not been verified" in gap.lower() for gap in result["data_gaps"])


def test_status_transition_decreases_calculated_risk():
    """Verify that containment and resolution substantially reduce the environmental risk score."""
    inc_active = Incident(
        id=uuid.uuid4(),
        incident_code="TEST-ACTIVE",
        title="Urban Flood Inundation",
        category="flood",
        severity="high",
        status="response_active",
        latitude=25.0,
        longitude=85.0,
        affected_population=1200,
        verification_status="verified",
    )
    res_active = disaster_risk_engine.assess_incident(inc_active, persist=False)

    inc_contained = Incident(
        id=uuid.uuid4(),
        incident_code="TEST-CONTAINED",
        title="Urban Flood Inundation",
        category="flood",
        severity="high",
        status="contained",
        latitude=25.0,
        longitude=85.0,
        affected_population=1200,
        verification_status="verified",
    )
    res_contained = disaster_risk_engine.assess_incident(inc_contained, persist=False)

    inc_resolved = Incident(
        id=uuid.uuid4(),
        incident_code="TEST-RESOLVED",
        title="Urban Flood Inundation",
        category="flood",
        severity="high",
        status="resolved",
        latitude=25.0,
        longitude=85.0,
        affected_population=1200,
        verification_status="verified",
    )
    res_resolved = disaster_risk_engine.assess_incident(inc_resolved, persist=False)

    assert res_active["calculated_risk_score"] > res_contained["calculated_risk_score"]
    assert res_contained["calculated_risk_score"] > res_resolved["calculated_risk_score"]

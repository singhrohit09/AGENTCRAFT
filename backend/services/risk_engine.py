"""
AgentCraft Explainable Disaster Risk Assessment Engine
Provides a deterministic, testable risk calculation engine that evaluates incident
attributes, reported severity, operational status, hydro-meteorological telemetry,
population exposure, and data quality indicators.

Produces normalized scores (0-100), transparent contributing factor breakdowns,
uncertainty metrics, and persists historical assessments into the risk_assessments table.
Operates completely deterministically without requiring an external AI API key.
"""

import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from backend.rakshagrid.models import Incident, RiskAssessment
from backend.services.external_data_service import disaster_data_service


def utcnow():
    return datetime.now(timezone.utc)


class DisasterRiskEngine:
    """
    Deterministic Disaster Risk Assessment Engine.
    Evaluates compound risk across multiple dimensions with explainable weights.
    """

    # Hazard base severity weights (0 - 25)
    CATEGORY_BASE_WEIGHTS = {
        "earthquake": 25.0,
        "landslide": 24.0,
        "flood": 22.0,
        "wildfire": 22.0,
        "severe_weather": 20.0,
        "industrial_accident": 20.0,
        "other": 10.0,
    }

    # Reported incident severity points (0 - 30)
    SEVERITY_POINTS = {
        "critical": 30.0,
        "high": 22.0,
        "medium": 12.0,
        "low": 5.0,
    }

    # Status modifiers (-20 to +10)
    STATUS_MODIFIERS = {
        "reported": 5.0,
        "under_assessment": 7.0,
        "confirmed": 8.0,
        "response_active": 10.0,
        "contained": -10.0,
        "resolved": -20.0,
        "closed": -25.0,
    }

    @classmethod
    def score_to_category(cls, score: float) -> str:
        """
        Maps 0-100 score to documented risk category:
        0.0 - 24.99: Low (0–24)
        25.0 - 49.99: Moderate (25–49)
        50.0 - 74.99: High (50–74)
        75.0 - 100.0: Critical (75–100)
        """
        if score < 25.0:
            return "Low"
        elif score < 50.0:
            return "Moderate"
        elif score < 75.0:
            return "High"
        else:
            return "Critical"

    def assess_incident(
        self,
        incident: Incident,
        weather_data: Optional[Dict[str, Any]] = None,
        flood_data: Optional[Dict[str, Any]] = None,
        db: Optional[Session] = None,
        persist: bool = True,
    ) -> Dict[str, Any]:
        """
        Calculates explainable risk score for a single incident record,
        compiling contributing factors, uncertainty gaps, and interventions.
        """
        breakdown: List[Dict[str, Any]] = []
        data_gaps: List[str] = []
        data_sources: List[Dict[str, Any]] = []
        uncertainty_points = 0.0

        # 1. Base Hazard Category
        cat = (incident.category or "other").lower()
        base_cat_score = self.CATEGORY_BASE_WEIGHTS.get(cat, 10.0)
        breakdown.append({
            "factor": "Hazard Category",
            "contribution": base_cat_score,
            "max_possible": 25.0,
            "description": f"Base hazard potential for category '{cat}'",
            "impact": "baseline",
        })

        # 2. Reported Severity (distinct from environmental calculation)
        sev = (incident.severity or "medium").lower()
        sev_score = self.SEVERITY_POINTS.get(sev, 12.0)
        breakdown.append({
            "factor": "Reported Severity",
            "contribution": sev_score,
            "max_possible": 30.0,
            "description": f"Initial field reported severity '{sev}'",
            "impact": "operator_assessment",
        })

        # 3. Operational Lifecycle Status
        stat = (incident.status or "reported").lower()
        stat_score = self.STATUS_MODIFIERS.get(stat, 0.0)
        breakdown.append({
            "factor": "Operational Status",
            "contribution": stat_score,
            "max_possible": 10.0,
            "description": f"Operational containment status: '{stat}'",
            "impact": "containment_modifier",
        })

        # 4. Hydro-Meteorological Telemetry
        has_coords = incident.latitude is not None and incident.longitude is not None
        env_score = 0.0

        if has_coords:
            if weather_data is None:
                weather_data = disaster_data_service.get_weather(incident.latitude, incident.longitude)
            if flood_data is None:
                flood_data = disaster_data_service.get_flood_data(incident.latitude, incident.longitude)

            data_sources.append({
                "source": weather_data.get("source", "Open-Meteo Weather"),
                "status": weather_data.get("status", "unknown"),
                "retrieval_time": weather_data.get("retrieval_time"),
                "freshness_seconds": weather_data.get("freshness_seconds"),
            })
            data_sources.append({
                "source": flood_data.get("source", "Open-Meteo Flood"),
                "status": flood_data.get("status", "unknown"),
                "retrieval_time": flood_data.get("retrieval_time"),
                "freshness_seconds": flood_data.get("freshness_seconds"),
            })

            # Check weather data freshness
            if weather_data.get("is_stale", False) or weather_data.get("status") == "unavailable":
                data_gaps.append("Weather telemetry unavailable or stale (>3 hours old)")
                uncertainty_points += 3.0

            # Precipitation scoring (0 - 15)
            precip = weather_data.get("precipitation_mm") or 0.0
            if precip >= 50.0:
                env_score += 15.0
            elif precip >= 20.0:
                env_score += 10.0
            elif precip >= 5.0:
                env_score += 5.0

            # Wind speed scoring (0 - 5)
            wind = weather_data.get("wind_speed_kmh") or 0.0
            if wind >= 60.0:
                env_score += 5.0
            elif wind >= 35.0:
                env_score += 2.0

            # River flood discharge scoring (0 - 10)
            frisk = flood_data.get("flood_risk_level", "low")
            if frisk == "critical":
                env_score += 10.0
            elif frisk == "high":
                env_score += 6.0
            elif frisk == "moderate":
                env_score += 3.0

            env_score = min(25.0, env_score)
            breakdown.append({
                "factor": "Hydro-Meteorological Telemetry",
                "contribution": env_score,
                "max_possible": 25.0,
                "description": f"Precipitation: {precip}mm, Wind: {wind}km/h, Flood risk: {frisk}",
                "impact": "environmental_conditions",
            })
        else:
            data_gaps.append("Geographic coordinates missing; cannot retrieve meteorological observations")
            uncertainty_points += 4.0
            breakdown.append({
                "factor": "Hydro-Meteorological Telemetry",
                "contribution": 0.0,
                "max_possible": 25.0,
                "description": "Skipped due to missing incident coordinates",
                "impact": "missing_data",
            })

        # 5. Population Exposure Impact (0 - 15)
        pop = incident.affected_population or 0
        if pop > 5000:
            pop_score = 15.0
        elif pop > 1000:
            pop_score = 10.0
        elif pop > 200:
            pop_score = 6.0
        elif pop > 0:
            pop_score = 3.0
        else:
            pop_score = 0.0

        breakdown.append({
            "factor": "Population Exposure",
            "contribution": pop_score,
            "max_possible": 15.0,
            "description": f"Estimated affected population: {pop:,} residents",
            "impact": "vulnerability",
        })

        # 6. Verification Status & Uncertainty
        v_stat = (incident.verification_status or "unverified").lower()
        if v_stat == "unverified":
            data_gaps.append("Incident report has not been verified by on-scene field commander")
            uncertainty_points += 3.0

        if uncertainty_points > 0:
            breakdown.append({
                "factor": "Data Uncertainty Penalty",
                "contribution": uncertainty_points,
                "max_possible": 10.0,
                "description": f"Uncertainty buffer added due to {len(data_gaps)} identified data gaps",
                "impact": "uncertainty_adjustment",
            })

        # Sum total score and normalize to 0.0 - 100.0
        total_raw = sum(f["contribution"] for f in breakdown)
        normalized_score = round(max(0.0, min(100.0, total_raw)), 1)
        risk_level = self.score_to_category(normalized_score)

        # Tactical recommendations derived from risk level and category
        interventions = self._generate_interventions(cat, risk_level, normalized_score, pop)

        result_payload = {
            "incident_id": str(incident.id) if incident.id else None,
            "incident_code": incident.incident_code,
            "title": incident.title,
            "target_area": incident.location_description or "General Incident Operational Area",
            "hazard_type": cat,
            "reported_severity": sev,
            "operational_status": stat,
            "calculated_risk_score": normalized_score,
            "risk_level": risk_level,
            "scoring_breakdown": breakdown,
            "data_sources": data_sources,
            "data_gaps": data_gaps,
            "uncertainty_points": uncertainty_points,
            "confidence_score": round(max(0.2, 1.0 - (uncertainty_points * 0.08)), 2),
            "recommended_interventions": interventions,
            "scientific_limitation_disclaimer": (
                "Deterministic operational heuristic score for emergency prioritization only. "
                "Not a scientifically calibrated hydrological or probabilistic loss forecast."
            ),
            "assessed_at": utcnow().isoformat(),
        }

        # Persist to database if session provided
        if persist and db is not None and incident.id is not None:
            db_assessment = RiskAssessment(
                incident_id=incident.id,
                target_area=result_payload["target_area"],
                hazard_type=cat,
                calculated_risk_score=normalized_score,
                risk_level=risk_level,
                simulated_factors=json.dumps(breakdown),
                recommended_interventions=json.dumps(interventions),
                data_sources=json.dumps(data_sources),
                confidence_score=result_payload["confidence_score"],
                assessed_at=utcnow(),
            )
            db.add(db_assessment)
            db.commit()
            result_payload["assessment_id"] = str(db_assessment.id)

        return result_payload

    def _generate_interventions(
        self, hazard: str, risk_level: str, score: float, population: int
    ) -> List[str]:
        """Generates appropriate tactical actions based on hazard and calculated risk."""
        actions: List[str] = []

        if risk_level == "Critical":
            actions.append("Issue high-urgency operational warning and alert field command")
            actions.append("Designate nearest high-capacity evacuation shelters for immediate reception")
            if hazard == "flood":
                actions.append("Pre-deploy NDRF motorized water rescue craft and sandbagging units")
            elif hazard == "wildfire":
                actions.append("Establish 25m containment firebreaks and stage water-drop tankers")
            elif hazard == "landslide":
                actions.append("Close downstream transport corridors and dispatch drone geological survey")
            else:
                actions.append("Mobilize specialized multi-hazard emergency task force")
        elif risk_level == "High":
            actions.append("Stage response teams at perimeter staging areas")
            actions.append("Verify shelter supply stockpiles (water, emergency medical rations)")
            if population > 500:
                actions.append("Issue voluntary relocation advisory for vulnerable demographics")
        elif risk_level == "Moderate":
            actions.append("Maintain active telemetry monitoring on local sensor gauges")
            actions.append("Brief on-duty response teams and confirm VHF radio frequencies")
        else:  # Low
            actions.append("Routine monitoring; maintain standard readiness state")

        return actions


# Singleton risk engine instance
disaster_risk_engine = DisasterRiskEngine()

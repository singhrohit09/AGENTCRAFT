"""
AgentCraft Disaster Scenario Simulation Engine
Implements interactive, reproducible emergency scenario simulations.
Supports heavy rainfall surge, multi-incident concurrency, team unavailability,
shelter capacity saturation, and supply shortages.
Guarantees complete state isolation: simulations NEVER mutate live operational database records.
"""

import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from backend.rakshagrid.models import (
    Incident,
    ResponseTeam,
    Shelter,
    Resource,
    DisasterSimulation,
)
from backend.services.risk_engine import disaster_risk_engine


def utcnow():
    return datetime.now(timezone.utc)


class SimulationEngine:
    """
    Deterministic Disaster Scenario Simulator.
    Models hypothetical emergency stress tests and computes capacity bottlenecks.
    """

    def run_simulation(
        self,
        db: Session,
        scenario_type: str,
        scenario_name: str,
        parameters: Dict[str, Any],
        operator_name: str = "operator",
    ) -> Dict[str, Any]:
        """
        Executes a hypothetical disaster simulation.
        Reads live database snapshot but NEVER modifies operational state.
        """
        stype = scenario_type.lower()
        if stype == "heavy_rainfall":
            results = self._simulate_heavy_rainfall(db, parameters)
        elif stype == "multi_incident":
            results = self._simulate_multi_incident(db, parameters)
        elif stype == "team_unavailability":
            results = self._simulate_team_unavailability(db, parameters)
        elif stype == "shelter_surge":
            results = self._simulate_shelter_surge(db, parameters)
        elif stype == "supply_shortage":
            results = self._simulate_supply_shortage(db, parameters)
        elif stype == "cascade_compound":
            results = self._simulate_cascade_compound(db, parameters)
        else:
            raise ValueError(
                f"Unknown scenario_type '{scenario_type}'. Supported: "
                "heavy_rainfall, multi_incident, team_unavailability, shelter_surge, supply_shortage, cascade_compound"
            )

        # Build complete simulation report
        simulation_record = {
            "scenario_name": scenario_name or f"Simulated {stype.replace('_', ' ').title()}",
            "scenario_type": stype,
            "parameters": parameters,
            "is_simulation": True,
            "simulated_at": utcnow().isoformat(),
            "operator": operator_name,
            "assumptions": [
                "Baseline calculations use live snapshot of response teams, shelters, and supplies.",
                "Deterministic propagation models are applied without mutating persistent operational state.",
                "No live emergency tasks or team dispatch orders were generated during this run.",
            ],
            "limitations_disclaimer": (
                "DISASTER SIMULATION MODEL — HYPOTHETICAL STRESS-TEST ONLY. "
                "This engine evaluates operational resource elasticity under simulated stress conditions. "
                "It does not predict real-world disaster occurrences with scientific certainty."
            ),
            "projected_impact": results,
        }

        # Persist simulation run in audit table
        db_sim = DisasterSimulation(
            scenario_name=simulation_record["scenario_name"],
            scenario_type=stype,
            input_parameters=json.dumps(parameters),
            results_summary=json.dumps(results),
            created_by=operator_name,
            created_at=utcnow(),
        )
        db.add(db_sim)
        db.commit()
        db.refresh(db_sim)

        simulation_record["simulation_id"] = str(db_sim.id)
        return simulation_record

    def _simulate_heavy_rainfall(self, db: Session, params: Dict[str, Any]) -> Dict[str, Any]:
        """Simulates extreme rainfall intensity and compound flood inundation risks."""
        rainfall_mm = float(params.get("rainfall_mm", 80.0))
        duration_hours = int(params.get("duration_hours", 6))
        target_incident_id = params.get("target_incident_id")

        incidents_query = db.query(Incident).filter(Incident.status.notin_(["resolved", "closed"]))
        if target_incident_id:
            try:
                iid = UUID(str(target_incident_id))
                incidents_query = incidents_query.filter(Incident.id == iid)
            except ValueError:
                incidents_query = incidents_query.filter(Incident.incident_code == str(target_incident_id))

        incidents = incidents_query.all()
        impacted_incidents = []

        total_displaced_surge = 0
        for inc in incidents:
            base_assessment = disaster_risk_engine.assess_incident(inc, db=db, persist=False)
            base_score = base_assessment["calculated_risk_score"]

            # Rainfall surge impact model
            rain_surge_score = min(25.0, (rainfall_mm / 100.0) * 20.0 + (duration_hours * 0.8))
            projected_score = min(100.0, round(base_score + rain_surge_score, 1))
            new_level = disaster_risk_engine.score_to_category(projected_score)

            displaced = int((inc.affected_population or 500) * (projected_score / 150.0))
            total_displaced_surge += displaced

            impacted_incidents.append({
                "incident_code": inc.incident_code,
                "title": inc.title,
                "baseline_risk_score": base_score,
                "projected_risk_score": projected_score,
                "projected_risk_level": new_level,
                "risk_delta": round(projected_score - base_score, 1),
                "projected_evacuation_demand": displaced,
            })

        # Calculate shelter capacity strain
        shelters = db.query(Shelter).filter(Shelter.status == "open").all()
        total_remaining_capacity = sum(s.remaining_capacity for s in shelters)
        deficit = max(0, total_displaced_surge - total_remaining_capacity)

        return {
            "rainfall_tested_mm": rainfall_mm,
            "duration_hours": duration_hours,
            "incidents_stressed": len(impacted_incidents),
            "projected_total_evacuation_surge": total_displaced_surge,
            "available_shelter_capacity": total_remaining_capacity,
            "shelter_capacity_deficit": deficit,
            "bottlenecks": [
                f"Rainfall surge of {rainfall_mm}mm over {duration_hours}h increases flood risk across {len(impacted_incidents)} sectors.",
                f"Projected {total_displaced_surge:,} evacuees exceed available shelter capacity by {deficit:,} slots." if deficit > 0
                else f"Available shelter capacity ({total_remaining_capacity:,}) is sufficient for projected surge.",
            ],
            "impacted_sectors": impacted_incidents,
        }

    def _simulate_multi_incident(self, db: Session, params: Dict[str, Any]) -> Dict[str, Any]:
        """Simulates simultaneous concurrent disasters stressing response teams."""
        concurrent_count = int(params.get("concurrent_incidents_count", 4))
        severity = params.get("severity", "critical")

        available_teams = db.query(ResponseTeam).filter(ResponseTeam.current_status == "available").all()
        total_teams = db.query(ResponseTeam).count()

        required_teams_per_incident = 2 if severity == "critical" else 1
        teams_required = concurrent_count * required_teams_per_incident
        shortfall = max(0, teams_required - len(available_teams))

        return {
            "hypothetical_concurrent_incidents": concurrent_count,
            "incident_severity_profile": severity,
            "available_teams_count": len(available_teams),
            "total_teams_count": total_teams,
            "teams_required": teams_required,
            "teams_shortfall": shortfall,
            "bottlenecks": [
                f"Simultaneous occurrence of {concurrent_count} {severity} incidents requires {teams_required} response teams.",
                f"Operational deficit: {shortfall} teams shortfall. Mutual aid agreements from adjacent districts required." if shortfall > 0
                else "Current ready roster is adequate to service simultaneous incident surge.",
            ],
            "recommended_strategy": (
                "Prioritize life-saving water rescue and medical triage units. "
                "Place logistical and drone reconnaissance teams on stand-by."
            ),
        }

    def _simulate_team_unavailability(self, db: Session, params: Dict[str, Any]) -> Dict[str, Any]:
        """Simulates response teams being rendered offline or stranded."""
        withdrawn_count = int(params.get("withdrawn_teams_count", 2))
        unit_type_filter = params.get("unit_type", "")

        query = db.query(ResponseTeam).filter(ResponseTeam.current_status == "available")
        if unit_type_filter:
            query = query.filter(ResponseTeam.unit_type.ilike(f"%{unit_type_filter}%"))
        matching_teams = query.all()

        remaining_count = max(0, len(matching_teams) - withdrawn_count)

        return {
            "teams_withdrawn_count": withdrawn_count,
            "target_unit_type": unit_type_filter or "all_units",
            "initial_ready_count": len(matching_teams),
            "projected_ready_count": remaining_count,
            "capacity_loss_pct": round((min(withdrawn_count, len(matching_teams)) / max(len(matching_teams), 1)) * 100, 1),
            "bottlenecks": [
                f"Withdrawal of {withdrawn_count} teams reduces readiness in '{unit_type_filter or 'general'}' units to {remaining_count}.",
            ],
            "contingency_recommendations": [
                "Re-route perimeter medical assets to backfill frontline search teams.",
                "Activate local civil defense volunteers for logistical support.",
            ],
        }

    def _simulate_shelter_surge(self, db: Session, params: Dict[str, Any]) -> Dict[str, Any]:
        """Simulates sudden mass displacement surging local shelter facilities."""
        incoming_evacuees = int(params.get("incoming_evacuees", 1500))

        shelters = db.query(Shelter).filter(Shelter.status == "open").all()
        projections = []
        remaining_intake = incoming_evacuees

        for s in shelters:
            free_slots = s.remaining_capacity
            intake = min(free_slots, remaining_intake)
            remaining_intake -= intake
            projected_occ = s.current_occupancy + intake
            projected_pct = round((projected_occ / max(s.capacity, 1)) * 100, 1)

            projections.append({
                "shelter_name": s.name,
                "nominal_capacity": s.capacity,
                "current_occupancy": s.current_occupancy,
                "projected_occupancy": projected_occ,
                "projected_occupancy_pct": projected_pct,
                "status": "at_capacity" if projected_pct >= 100.0 else "absorptive",
            })

        return {
            "incoming_evacuees_simulated": incoming_evacuees,
            "total_shelters_evaluated": len(shelters),
            "unaccommodated_evacuees": max(0, remaining_intake),
            "shelter_breakdown": projections,
            "bottlenecks": [
                f"Surge of {incoming_evacuees:,} evacuees leaves {max(0, remaining_intake):,} displaced individuals unhoused." if remaining_intake > 0
                else f"All {incoming_evacuees:,} evacuees absorbed within regional shelter capacity.",
            ],
        }

    def _simulate_supply_shortage(self, db: Session, params: Dict[str, Any]) -> Dict[str, Any]:
        """Simulates rapid exhaustion or blockade of critical relief supplies."""
        burn_rate_multiplier = float(params.get("burn_rate_multiplier", 2.5))
        duration_days = int(params.get("duration_days", 3))

        resources = db.query(Resource).all()
        stress_projections = []

        for r in resources:
            daily_nominal_use = max(1.0, r.quantity_total * 0.1)
            projected_use = daily_nominal_use * burn_rate_multiplier * duration_days
            projected_remaining = max(0.0, r.quantity_available - projected_use)
            stockout_day = (r.quantity_available / (daily_nominal_use * burn_rate_multiplier)) if (daily_nominal_use * burn_rate_multiplier) > 0 else 99

            stress_projections.append({
                "resource_name": r.name,
                "category": r.category,
                "current_available": r.quantity_available,
                "projected_remaining": round(projected_remaining, 1),
                "stockout_within_days": round(stockout_day, 1) if stockout_day < duration_days else None,
                "is_exhausted": projected_remaining <= 0.0,
            })

        exhausted_items = [p["resource_name"] for p in stress_projections if p["is_exhausted"]]

        return {
            "burn_rate_multiplier": burn_rate_multiplier,
            "duration_days": duration_days,
            "resources_evaluated": len(resources),
            "exhausted_supplies_count": len(exhausted_items),
            "exhausted_items": exhausted_items,
            "projections": stress_projections,
            "bottlenecks": [
                f"{len(exhausted_items)} critical supply stockpiles exhausted within {duration_days} days under {burn_rate_multiplier}x burn rate.",
            ],
        }

    def _simulate_cascade_compound(self, db: Session, params: Dict[str, Any]) -> Dict[str, Any]:
        """Compound multi-hazard scenario combining rain, team deficit, and shelter surge."""
        rain_res = self._simulate_heavy_rainfall(db, params)
        teams_res = self._simulate_multi_incident(db, params)
        shelter_res = self._simulate_shelter_surge(db, {"incoming_evacuees": rain_res["projected_total_evacuation_surge"]})

        compound_bottlenecks = rain_res["bottlenecks"] + teams_res["bottlenecks"] + shelter_res["bottlenecks"]

        return {
            "scenario": "compound_cascade_disaster",
            "compound_bottlenecks": compound_bottlenecks,
            "rain_flood_projection": rain_res,
            "team_stress_projection": teams_res,
            "shelter_stress_projection": shelter_res,
        }

    def list_simulations(self, db: Session, limit: int = 20) -> List[Dict[str, Any]]:
        """Retrieves history of previous simulation runs."""
        sims = db.query(DisasterSimulation).order_by(DisasterSimulation.created_at.desc()).limit(limit).all()
        return [
            {
                "id": str(s.id),
                "scenario_name": s.scenario_name,
                "scenario_type": s.scenario_type,
                "created_by": s.created_by,
                "created_at": s.created_at.isoformat(),
                "parameters": json.loads(s.input_parameters) if s.input_parameters else {},
                "results_summary": json.loads(s.results_summary) if s.results_summary else {},
            }
            for s in sims
        ]


# Singleton simulation engine
simulation_engine = SimulationEngine()

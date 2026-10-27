"""
AgentCraft Disaster Intelligence Agent Tools
Implements validated, database-backed tools for incident inspection, risk analysis,
weather telemetry, team availability, task monitoring, shelter capacity,
resource inventory, and human-in-the-loop response planning.
All tools strictly inherit from BaseTool (ai.tools.base).
"""

import json
from typing import Any, Dict, List, Optional
from uuid import UUID

from ai.tools.base import BaseTool, ToolParameter
from backend.database.session import transactional_session
from backend.rakshagrid.models import (
    Incident,
    ResponseTeam,
    ResponseTask,
    Shelter,
    Resource,
    AIAnalysisRecord,
)
from backend.services.external_data_service import disaster_data_service
from backend.services.risk_engine import disaster_risk_engine


def find_incident(db, incident_id_or_code: str) -> Optional[Incident]:
    """Helper to locate an incident by either UUID or human-readable incident_code."""
    inc = None
    try:
        val_uuid = UUID(str(incident_id_or_code))
        inc = db.query(Incident).filter(Incident.id == val_uuid).first()
    except (ValueError, TypeError):
        pass

    if not inc:
        inc = db.query(Incident).filter(Incident.incident_code == str(incident_id_or_code)).first()
    return inc


class GetIncidentDetailsTool(BaseTool):
    """Retrieves verified details, location, status, and timeline updates for an incident."""

    def __init__(self):
        super().__init__(
            name="get_incident_details",
            description="Retrieves persistent operational details, coordinates, severity, and timeline for an incident.",
            parameters=[
                ToolParameter(
                    name="incident_id",
                    type="string",
                    description="UUID or incident_code (e.g. 'INC-2026-001') of the target incident.",
                    required=True,
                )
            ],
        )

    def execute(self, incident_id: str) -> Dict[str, Any]:
        with transactional_session() as db:
            inc = find_incident(db, incident_id)
            if not inc:
                raise ValueError(f"Incident with ID or code '{incident_id}' not found.")

            return {
                "id": str(inc.id),
                "incident_code": inc.incident_code,
                "title": inc.title,
                "description": inc.description,
                "category": inc.category,
                "severity": inc.severity,
                "status": inc.status,
                "latitude": inc.latitude,
                "longitude": inc.longitude,
                "location_description": inc.location_description,
                "affected_population": inc.affected_population,
                "verification_status": inc.verification_status,
                "assigned_commander": inc.assigned_commander,
                "updates_count": len(inc.updates) if inc.updates else 0,
                "reported_at": inc.reported_at.isoformat() if inc.reported_at else None,
            }


class GetIncidentRiskTool(BaseTool):
    """Calculates or retrieves explainable risk assessment for an incident."""

    def __init__(self):
        super().__init__(
            name="get_incident_risk",
            description="Calculates deterministic, explainable risk score (0-100) and factors for an incident.",
            parameters=[
                ToolParameter(
                    name="incident_id",
                    type="string",
                    description="UUID or incident_code of the incident to assess.",
                    required=True,
                )
            ],
        )

    def execute(self, incident_id: str) -> Dict[str, Any]:
        with transactional_session() as db:
            inc = find_incident(db, incident_id)
            if not inc:
                raise ValueError(f"Incident '{incident_id}' not found for risk assessment.")

            assessment = disaster_risk_engine.assess_incident(inc, db=db, persist=True)
            return assessment


class GetWeatherObservationsTool(BaseTool):
    """Queries external meteorological and hydrological telemetry for given geographic coordinates."""

    def __init__(self):
        super().__init__(
            name="get_weather_observations",
            description="Fetches current weather telemetry, rainfall, wind, and river flood risk for coordinates.",
            parameters=[
                ToolParameter(
                    name="latitude",
                    type="number",
                    description="Latitude coordinate between -90.0 and 90.0.",
                    required=True,
                ),
                ToolParameter(
                    name="longitude",
                    type="number",
                    description="Longitude coordinate between -180.0 and 180.0.",
                    required=True,
                ),
            ],
        )

    def execute(self, latitude: float, longitude: float) -> Dict[str, Any]:
        w = disaster_data_service.get_weather(float(latitude), float(longitude))
        f = disaster_data_service.get_flood_data(float(latitude), float(longitude))
        return {
            "latitude": latitude,
            "longitude": longitude,
            "weather": w,
            "flood": f,
            "overall_freshness_seconds": w.get("freshness_seconds"),
            "is_stale": w.get("is_stale", False) or f.get("is_stale", False),
        }


class GetAvailableTeamsTool(BaseTool):
    """Inspects response team readiness, unit types, and deployment status."""

    def __init__(self):
        super().__init__(
            name="get_available_teams",
            description="Queries response team roster, filtering by status (available, assigned, busy) or unit type.",
            parameters=[
                ToolParameter(
                    name="status",
                    type="string",
                    description="Filter by team status (e.g. 'available', 'assigned', 'all').",
                    required=False,
                    default="available",
                ),
                ToolParameter(
                    name="unit_type",
                    type="string",
                    description="Filter by unit type (e.g. 'NDRF', 'Medical', 'HAZMAT', 'Drone Recon').",
                    required=False,
                    default="",
                ),
            ],
        )

    def execute(self, status: str = "available", unit_type: str = "") -> Dict[str, Any]:
        with transactional_session() as db:
            query = db.query(ResponseTeam)
            if status and status.lower() != "all":
                query = query.filter(ResponseTeam.current_status == status.lower())
            if unit_type:
                query = query.filter(ResponseTeam.unit_type.ilike(f"%{unit_type}%"))

            teams = query.all()
            return {
                "count": len(teams),
                "filter_status": status,
                "teams": [
                    {
                        "id": str(t.id),
                        "callsign": t.team_callsign,
                        "unit_type": t.unit_type,
                        "personnel_count": t.personnel_count,
                        "commander_name": t.commander_name,
                        "contact_channel": t.contact_channel,
                        "current_status": t.current_status,
                        "base_location": t.base_location,
                        "assigned_incident_id": str(t.assigned_incident_id) if t.assigned_incident_id else None,
                    }
                    for t in teams
                ],
            }


class GetActiveTasksTool(BaseTool):
    """Inspects ongoing, pending, or prioritized emergency tasks."""

    def __init__(self):
        super().__init__(
            name="get_active_tasks",
            description="Queries dispatched or pending operational tasks for an incident or overall response.",
            parameters=[
                ToolParameter(
                    name="incident_id",
                    type="string",
                    description="Optional incident UUID or code to scope task query.",
                    required=False,
                    default="",
                ),
                ToolParameter(
                    name="priority",
                    type="string",
                    description="Filter by priority ('low', 'medium', 'high', 'critical', 'all').",
                    required=False,
                    default="all",
                ),
            ],
        )

    def execute(self, incident_id: str = "", priority: str = "all") -> Dict[str, Any]:
        with transactional_session() as db:
            query = db.query(ResponseTask).filter(ResponseTask.status != "completed")
            if incident_id:
                inc = find_incident(db, incident_id)
                if inc:
                    query = query.filter(ResponseTask.incident_id == inc.id)
            if priority and priority.lower() != "all":
                query = query.filter(ResponseTask.priority == priority.lower())

            tasks = query.all()
            return {
                "active_tasks_count": len(tasks),
                "tasks": [
                    {
                        "id": str(tk.id),
                        "incident_id": str(tk.incident_id),
                        "title": tk.title,
                        "description": tk.description,
                        "priority": tk.priority,
                        "status": tk.status,
                        "assigned_team_id": str(tk.assigned_team_id) if tk.assigned_team_id else None,
                    }
                    for tk in tasks
                ],
            }


class GetShelterCapacityTool(BaseTool):
    """Inspects evacuation shelters, current occupancy, and remaining intake capacity."""

    def __init__(self):
        super().__init__(
            name="get_shelter_capacity",
            description="Checks shelter availability, occupancy rates, and critical supply status.",
            parameters=[
                ToolParameter(
                    name="status",
                    type="string",
                    description="Filter by shelter status (default 'open', or 'all').",
                    required=False,
                    default="open",
                )
            ],
        )

    def execute(self, status: str = "open") -> Dict[str, Any]:
        with transactional_session() as db:
            query = db.query(Shelter)
            if status and status.lower() != "all":
                query = query.filter(Shelter.status == status.lower())

            shelters = query.all()
            total_cap = sum(s.capacity for s in shelters)
            total_occ = sum(s.current_occupancy for s in shelters)

            return {
                "shelters_count": len(shelters),
                "total_capacity": total_cap,
                "total_occupancy": total_occ,
                "overall_occupancy_pct": round((total_occ / max(total_cap, 1)) * 100, 1),
                "shelters": [
                    {
                        "id": str(s.id),
                        "name": s.name,
                        "shelter_type": s.shelter_type,
                        "capacity": s.capacity,
                        "current_occupancy": s.current_occupancy,
                        "remaining_capacity": s.remaining_capacity,
                        "occupancy_pct": round((s.current_occupancy / max(s.capacity, 1)) * 100, 1),
                        "address": s.address,
                        "supplies_status": s.supplies_status,
                        "power_backup": s.power_backup,
                        "medical_station": s.medical_station,
                        "status": s.status,
                    }
                    for s in shelters
                ],
            }


class GetResourceInventoryTool(BaseTool):
    """Inspects emergency supplies, rescue gear, rations, and stockpile shortages."""

    def __init__(self):
        super().__init__(
            name="get_resource_inventory",
            description="Queries relief stockpile inventory, quantities available, and low-stock alerts.",
            parameters=[
                ToolParameter(
                    name="category",
                    type="string",
                    description="Filter by resource category (e.g. 'medical', 'food_water', 'rescue_gear').",
                    required=False,
                    default="",
                ),
                ToolParameter(
                    name="low_stock_only",
                    type="boolean",
                    description="If true, returns only resources below 25% availability.",
                    required=False,
                    default=False,
                ),
            ],
        )

    def execute(self, category: str = "", low_stock_only: bool = False) -> Dict[str, Any]:
        with transactional_session() as db:
            query = db.query(Resource)
            if category:
                query = query.filter(Resource.category.ilike(f"%{category}%"))

            items = query.all()
            results = []
            shortages = []

            for r in items:
                pct = round((r.quantity_available / max(r.quantity_total, 1.0)) * 100, 1)
                is_low = pct <= 25.0
                if low_stock_only and not is_low:
                    continue

                item_dict = {
                    "id": str(r.id),
                    "resource_code": r.resource_code,
                    "name": r.name,
                    "category": r.category,
                    "quantity_available": r.quantity_available,
                    "quantity_total": r.quantity_total,
                    "unit": r.unit,
                    "availability_pct": pct,
                    "status": r.status,
                    "storage_location": r.storage_location,
                }
                results.append(item_dict)
                if is_low:
                    shortages.append(f"{r.name}: only {r.quantity_available} {r.unit} remaining ({pct}%)")

            return {
                "items_count": len(results),
                "shortages_count": len(shortages),
                "shortages_summary": shortages,
                "inventory": results,
            }


class ProposeResponsePlanTool(BaseTool):
    """
    Synthesizes an actionable disaster response plan.
    Enforces the Human-in-the-Loop decision gate: recommendations require explicit human approval.
    """

    def __init__(self):
        super().__init__(
            name="propose_response_plan",
            description="Synthesizes a response plan with recommended teams, tasks, and shelter assignments. Requires human approval.",
            parameters=[
                ToolParameter(
                    name="incident_id",
                    type="string",
                    description="Target incident UUID or code.",
                    required=True,
                ),
                ToolParameter(
                    name="rationale",
                    type="string",
                    description="Evidence-based explanation of why these interventions are recommended.",
                    required=True,
                ),
                ToolParameter(
                    name="recommended_teams",
                    type="array",
                    description="List of team callsigns or roles recommended for dispatch.",
                    required=False,
                    default=[],
                ),
                ToolParameter(
                    name="recommended_tasks",
                    type="array",
                    description="List of operational tasks to dispatch.",
                    required=False,
                    default=[],
                ),
                ToolParameter(
                    name="shelter_actions",
                    type="array",
                    description="List of shelter preparation or evacuation reception directives.",
                    required=False,
                    default=[],
                ),
            ],
        )

    def execute(
        self,
        incident_id: str,
        rationale: str,
        recommended_teams: Optional[List[str]] = None,
        recommended_tasks: Optional[List[Dict[str, Any]]] = None,
        shelter_actions: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        recommended_teams = recommended_teams or []
        recommended_tasks = recommended_tasks or []
        shelter_actions = shelter_actions or []

        with transactional_session() as db:
            inc = find_incident(db, incident_id)
            if not inc:
                raise ValueError(f"Target incident '{incident_id}' not found.")

            # Record recommendation in AI analysis records for traceable auditability
            record = AIAnalysisRecord(
                incident_id=inc.id,
                query_type="response_plan_proposal",
                provider="agentcraft_disaster_agent",
                model_name="deterministic_cognitive_synthesizer",
                prompt_summary=f"Plan synthesis for incident {inc.incident_code} ({inc.title})",
                response_content=rationale,
                structured_payload=json.dumps({
                    "recommended_teams": recommended_teams,
                    "recommended_tasks": recommended_tasks,
                    "shelter_actions": shelter_actions,
                }),
                tools_used=json.dumps(["get_incident_details", "get_available_teams", "get_shelter_capacity"]),
                requires_human_approval=True,
                approval_status="pending",
            )
            db.add(record)
            db.commit()

            return {
                "proposal_id": str(record.id),
                "incident_id": str(inc.id),
                "incident_code": inc.incident_code,
                "is_recommendation": True,
                "requires_human_approval": True,
                "approval_status": "pending",
                "recommended_teams": recommended_teams,
                "recommended_tasks": recommended_tasks,
                "shelter_actions": shelter_actions,
                "rationale": rationale,
                "consequential_action_disclaimer": (
                    "OPERATIONAL DECISION GATE: This is an AI-assisted recommendation. "
                    "In compliance with AGENTCRAFT 2026 directives, teams, tasks, and alerts "
                    "are NOT committed without explicit human authorization."
                ),
            }

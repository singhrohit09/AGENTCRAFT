"""
RakshaGrid Service Layer
Coordinates disaster intelligence queries, diagnostic subsystem health checks,
and provides structured demonstration telemetry for Phase 1.
"""

import time
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional
from backend.rakshagrid.config import rakshagrid_settings
from backend.database.session import check_db_connectivity


def utcnow():
    return datetime.now(timezone.utc)


class RakshaGridService:
    """Core service for RakshaGrid disaster intelligence operations."""

    def __init__(self):
        self._start_time = time.time()
        self._demo_incidents = self._init_demo_incidents()
        self._demo_alerts = self._init_demo_alerts()
        self._demo_teams = self._init_demo_teams()
        self._demo_shelters = self._init_demo_shelters()
        self._demo_activity = self._init_demo_activity()

    def get_uptime_seconds(self) -> float:
        return round(time.time() - self._start_time, 2)

    def get_health_status(self) -> Dict[str, Any]:
        """Evaluates health across all RakshaGrid subsystems."""
        db_check = check_db_connectivity()

        subsystems = {
            "database": {
                "status": db_check["status"],
                "details": db_check["detail"] or "PostgreSQL service status",
                "latency_ms": db_check["latency_ms"],
            },
            "incident_engine": {
                "status": "operational",
                "details": "In-memory incident pipeline active; 11 relational schemas registered",
                "latency_ms": 0.4,
            },
            "alert_broadcaster": {
                "status": "operational",
                "details": "Common Alerting Protocol (CAP v1.2) formatted dispatch queue ready",
                "latency_ms": 0.2,
            },
            "geospatial_indexer": {
                "status": "operational",
                "details": "Cartesian spatial bounding coordinates active (Phase 1 preview)",
                "latency_ms": 0.5,
            },
            "resource_allocator": {
                "status": "operational",
                "details": "Stockpile movement log active",
                "latency_ms": 0.3,
            },
        }

        # Overall status
        if db_check["status"] == "connected":
            overall_status = "operational"
        elif db_check["status"] in ("service_unavailable", "disconnected"):
            overall_status = "operational_demo_fallback"
        else:
            overall_status = "degraded"

        return {
            "status": overall_status,
            "project": rakshagrid_settings.RAKSHAGRID_APP_NAME,
            "subtitle": rakshagrid_settings.RAKSHAGRID_SUBTITLE,
            "version": rakshagrid_settings.RAKSHAGRID_VERSION,
            "environment": rakshagrid_settings.RAKSHAGRID_ENV,
            "demo_mode_active": rakshagrid_settings.RAKSHAGRID_DEMO_MODE,
            "defcon_level": rakshagrid_settings.RAKSHAGRID_DEFCON_LEVEL,
            "uptime_seconds": self.get_uptime_seconds(),
            "subsystems": subsystems,
            "timestamp": utcnow(),
        }

    def get_database_status(self) -> Dict[str, Any]:
        """Returns PostgreSQL connection telemetry and migration status."""
        check = check_db_connectivity()
        return {
            "configured": check["configured"],
            "host": check["host"],
            "port": check["port"],
            "database": check["database"],
            "status": check["status"],
            "connection": check["connection"],
            "latency_ms": check["latency_ms"],
            "detail": check["detail"] or "Database status verified",
            "active_migration_version": "0001_initial",
            "models_registered_count": 11,
        }

    def get_overview_data(self) -> Dict[str, Any]:
        """Compiles high-level tactical statistics for the command dashboard."""
        active_incidents = [i for i in self._demo_incidents if i["status"] in ("active", "assessing")]
        critical_count = sum(1 for i in active_incidents if i["severity"] == "critical")
        deployed_teams = sum(1 for t in self._demo_teams if t["current_status"] in ("deployed", "en_route"))
        active_alerts = [a for a in self._demo_alerts if a["broadcast_status"] == "active"]

        total_capacity = sum(s["capacity"] for s in self._demo_shelters)
        total_occupancy = sum(s["current_occupancy"] for s in self._demo_shelters)
        occupancy_pct = round((total_occupancy / total_capacity * 100), 1) if total_capacity else 0.0

        db_stat = self.get_database_status()["status"]

        threat_map = {
            1: "DEFCON 1 — Catastrophic Disaster Emergency Declared",
            2: "DEFCON 2 — High Severity Multi-Hazard Escalation",
            3: "DEFCON 3 — Moderate Hazard Monitoring & Pre-Deployment",
            4: "DEFCON 4 — Localized Hazard Advisory",
            5: "DEFCON 5 — Routine Standby & Preparedness",
        }

        stats = {
            "defcon_level": rakshagrid_settings.RAKSHAGRID_DEFCON_LEVEL,
            "threat_description": threat_map.get(rakshagrid_settings.RAKSHAGRID_DEFCON_LEVEL, "Elevated Disaster Watch"),
            "active_incidents_count": len(active_incidents),
            "critical_incidents_count": critical_count,
            "deployed_teams_count": deployed_teams,
            "active_alerts_count": len(active_alerts),
            "shelters_open_count": sum(1 for s in self._demo_shelters if s["status"] == "open"),
            "total_sheltered_population": total_occupancy,
            "total_shelter_capacity": total_capacity,
            "overall_shelter_occupancy_pct": occupancy_pct,
            "resource_readiness_pct": 87.4,
            "database_status": db_stat,
            "demo_mode_active": rakshagrid_settings.RAKSHAGRID_DEMO_MODE,
        }

        return {
            "stats": stats,
            "active_incidents": self._demo_incidents[:5],
            "high_priority_alerts": active_alerts[:4],
            "recent_activity": self._demo_activity[:8],
            "disclaimer": "[FICTIONAL DEMO DATA - PHASE 1 FOUNDATION] Real-time sensors and live GPS tracking are scheduled for Phase 2.",
        }

    def list_incidents(
        self,
        disaster_type: Optional[str] = None,
        severity: Optional[str] = None,
        status: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Filters and retrieves disaster incidents."""
        results = self._demo_incidents
        if disaster_type:
            results = [i for i in results if i["disaster_type"].lower() == disaster_type.lower()]
        if severity:
            results = [i for i in results if i["severity"].lower() == severity.lower()]
        if status:
            results = [i for i in results if i["status"].lower() == status.lower()]
        return results

    def list_alerts(self, severity: Optional[str] = None, active_only: bool = True) -> List[Dict[str, Any]]:
        """Filters and retrieves public emergency alerts."""
        results = self._demo_alerts
        if active_only:
            results = [a for a in results if a["broadcast_status"] == "active"]
        if severity:
            results = [a for a in results if a["severity"].lower() == severity.lower()]
        return results

    def list_teams(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """Retrieves emergency response teams."""
        if status:
            return [t for t in self._demo_teams if t["current_status"].lower() == status.lower()]
        return self._demo_teams

    def list_shelters(self) -> List[Dict[str, Any]]:
        """Retrieves evacuation shelters with calculated occupancy ratios."""
        return self._demo_shelters

    # --------------------------------------------------------------------------
    # Fictional Demonstration Data Initializers (Phase 1 Foundation)
    # --------------------------------------------------------------------------
    def _init_demo_incidents(self) -> List[Dict[str, Any]]:
        now = utcnow()
        return [
            {
                "id": "e3a8904b-7411-4ec4-94c3-1d0b04320101",
                "incident_code": "RG-2026-FL-001",
                "title": "Brahmaputra Basin Flash Flood & Embankment Breach",
                "disaster_type": "flood",
                "severity": "critical",
                "status": "active",
                "latitude": 26.185,
                "longitude": 91.748,
                "location_name": "Guwahati Sector 4, Kamrup Metropolitan",
                "affected_region": "Assam Valley",
                "affected_population_estimate": 48200,
                "casualty_count_estimate": 4,
                "description": "Embankment breach along Sector 4 resulting in inundation across 12 low-lying villages. Water levels rising at 8 cm/hr.",
                "reported_at": now - timedelta(hours=6),
                "updated_at": now - timedelta(minutes=14),
                "is_demo": True,
            },
            {
                "id": "e3a8904b-7411-4ec4-94c3-1d0b04320102",
                "incident_code": "RG-2026-CY-002",
                "title": "Severe Cyclonic Storm 'Sagar' Coastal Landfall Watch",
                "disaster_type": "cyclone",
                "severity": "severe",
                "status": "active",
                "latitude": 19.813,
                "longitude": 85.831,
                "location_name": "Puri Coastal Zone, Odisha",
                "affected_region": "Odisha Coastal Belt",
                "affected_population_estimate": 125000,
                "casualty_count_estimate": 0,
                "description": "Category 3 cyclonic system tracking Northwest at 18 km/h. Sustained wind speeds 130 km/h with projected storm surge of 2.8 meters.",
                "reported_at": now - timedelta(hours=14),
                "updated_at": now - timedelta(minutes=32),
                "is_demo": True,
            },
            {
                "id": "e3a8904b-7411-4ec4-94c3-1d0b04320103",
                "incident_code": "RG-2026-LS-003",
                "title": "National Highway 58 Debris Flow & Landslide",
                "disaster_type": "landslide",
                "severity": "severe",
                "status": "assessing",
                "latitude": 30.146,
                "longitude": 78.784,
                "location_name": "Rudraprayag Ridge Km 44, Uttarakhand",
                "affected_region": "Garhwal Himalayas",
                "affected_population_estimate": 3200,
                "casualty_count_estimate": 2,
                "description": "Heavy monsoon rains triggered major slope failure blocking NH-58. Over 140 transit vehicles stranded; debris removal crews dispatched.",
                "reported_at": now - timedelta(hours=3),
                "updated_at": now - timedelta(minutes=45),
                "is_demo": True,
            },
            {
                "id": "e3a8904b-7411-4ec4-94c3-1d0b04320104",
                "incident_code": "RG-2026-EQ-004",
                "title": "Magnitude 5.8 Tremor & Structural Masonry Hazard",
                "disaster_type": "earthquake",
                "severity": "moderate",
                "status": "contained",
                "latitude": 32.219,
                "longitude": 76.323,
                "location_name": "Kangra Foothills, Himachal Pradesh",
                "affected_region": "Himachal Foothills",
                "affected_population_estimate": 18000,
                "casualty_count_estimate": 0,
                "description": "Shallow focus seismic event at 10km depth. No major bridge collapses reported; masonry cracks in old residential structures.",
                "reported_at": now - timedelta(hours=22),
                "updated_at": now - timedelta(hours=4),
                "is_demo": True,
            },
            {
                "id": "e3a8904b-7411-4ec4-94c3-1d0b04320105",
                "incident_code": "RG-2026-WF-005",
                "title": "Simlipal Tiger Reserve Buffer Zone Wildfire",
                "disaster_type": "wildfire",
                "severity": "moderate",
                "status": "active",
                "latitude": 21.642,
                "longitude": 86.345,
                "location_name": "Baripada Sector West, Mayurbhanj",
                "affected_region": "Eastern Highlands",
                "affected_population_estimate": 1400,
                "casualty_count_estimate": 0,
                "description": "Dry canopy forest fire spreading across 40 hectares. Aerial water drops coordinated with local forest guard units.",
                "reported_at": now - timedelta(hours=8),
                "updated_at": now - timedelta(minutes=55),
                "is_demo": True,
            },
        ]

    def _init_demo_alerts(self) -> List[Dict[str, Any]]:
        now = utcnow()
        return [
            {
                "id": "a1b2c3d4-0001-4ec4-94c3-1d0b04320201",
                "alert_code": "ALT-2026-0091",
                "headline": "RED WARNING: Immediate Evacuation Order for Kamrup Flood Plains",
                "urgency": "immediate",
                "severity": "extreme",
                "certainty": "observed",
                "target_region": "Kamrup Metropolitan & Darrang Low-Lying Sectors",
                "evacuation_recommended": True,
                "instructions": "Move immediately to designated concrete multi-purpose shelters. Do not attempt to drive through flooded roads. Keep emergency battery radios tuned to Channel 4.",
                "broadcast_status": "active",
                "issued_at": now - timedelta(hours=2),
                "expires_at": now + timedelta(hours=22),
                "is_demo": True,
            },
            {
                "id": "a1b2c3d4-0002-4ec4-94c3-1d0b04320202",
                "alert_code": "ALT-2026-0092",
                "headline": "CYCLONE ALERT: Coastal Evacuation & Fishing Prohibition",
                "urgency": "expected",
                "severity": "severe",
                "certainty": "likely",
                "target_region": "Puri, Jagatsinghpur, Kendrapara Coastal Belt",
                "evacuation_recommended": True,
                "instructions": "Total ban on maritime activities. Coastal settlements within 3km of shoreline must relocate to cyclone relief centers by 18:00 UTC.",
                "broadcast_status": "active",
                "issued_at": now - timedelta(hours=5),
                "expires_at": now + timedelta(hours=36),
                "is_demo": True,
            },
            {
                "id": "a1b2c3d4-0003-4ec4-94c3-1d0b04320203",
                "alert_code": "ALT-2026-0093",
                "headline": "TRAFFIC ADVISORY: NH-58 Closure Due to Slope Failure",
                "urgency": "immediate",
                "severity": "moderate",
                "certainty": "observed",
                "target_region": "Rudraprayag Highway Corridor",
                "evacuation_recommended": False,
                "instructions": "NH-58 closed indefinitely at Km 44. Divert all non-emergency traffic via Tehri bypass.",
                "broadcast_status": "active",
                "issued_at": now - timedelta(hours=3),
                "expires_at": now + timedelta(hours=12),
                "is_demo": True,
            },
        ]

    def _init_demo_teams(self) -> List[Dict[str, Any]]:
        return [
            {
                "id": "t1-0001",
                "team_callsign": "NDRF-BRAVO-12",
                "unit_type": "ndrf",
                "personnel_count": 45,
                "commander_name": "Assistant Commandant R. K. Sharma",
                "contact_channel": "VHF-CH-09 / SAT-901",
                "current_status": "deployed",
                "base_location": "Guwahati Sector 4 Staging Ground",
                "current_latitude": 26.182,
                "current_longitude": 91.751,
                "is_demo": True,
            },
            {
                "id": "t1-0002",
                "team_callsign": "SDRF-ODISHA-04",
                "unit_type": "sdrf",
                "personnel_count": 32,
                "commander_name": "Inspector Pradeep Mohanty",
                "contact_channel": "VHF-CH-14",
                "current_status": "deployed",
                "base_location": "Puri District Headquarters",
                "current_latitude": 19.815,
                "current_longitude": 85.835,
                "is_demo": True,
            },
            {
                "id": "t1-0003",
                "team_callsign": "MED-TRIAGE-ALPHA",
                "unit_type": "medical_triage",
                "personnel_count": 18,
                "commander_name": "Dr. Ananya Sen (Chief Trauma Officer)",
                "contact_channel": "SAT-MED-02",
                "current_status": "deployed",
                "base_location": "Assam State Relief Center #2",
                "current_latitude": 26.189,
                "current_longitude": 91.742,
                "is_demo": True,
            },
            {
                "id": "t1-0004",
                "team_callsign": "AERO-DRONE-RECON-7",
                "unit_type": "aerial_drone",
                "personnel_count": 8,
                "commander_name": "Flight Lt. Vikram Joshi (Retd.)",
                "contact_channel": "DATA-LINK-UAV-7",
                "current_status": "en_route",
                "base_location": "Rudraprayag Helipad Staging",
                "current_latitude": 30.150,
                "current_longitude": 78.780,
                "is_demo": True,
            },
            {
                "id": "t1-0005",
                "team_callsign": "HAZMAT-CONTAINMENT-02",
                "unit_type": "hazmat",
                "personnel_count": 14,
                "commander_name": "Capt. Meera Nair",
                "contact_channel": "VHF-HAZ-01",
                "current_status": "standby",
                "base_location": "Kolkata Central Depot",
                "current_latitude": 22.572,
                "current_longitude": 88.363,
                "is_demo": True,
            },
        ]

    def _init_demo_shelters(self) -> List[Dict[str, Any]]:
        return [
            {
                "id": "s1-0001",
                "name": "Kamrup Multi-Purpose Relief Center #1",
                "shelter_type": "community_center",
                "capacity": 2500,
                "current_occupancy": 1840,
                "occupancy_percent": 73.6,
                "location_name": "Guwahati Sector 2 High Grounds",
                "supplies_status": "adequate",
                "power_backup": True,
                "medical_station": True,
                "status": "open",
                "is_demo": True,
            },
            {
                "id": "s1-0002",
                "name": "Puri Coastal Cyclone Shelter Alpha",
                "shelter_type": "stadium",
                "capacity": 4000,
                "current_occupancy": 2980,
                "occupancy_percent": 74.5,
                "location_name": "Puri Municipal Sports Complex",
                "supplies_status": "adequate",
                "power_backup": True,
                "medical_station": True,
                "status": "open",
                "is_demo": True,
            },
            {
                "id": "s1-0003",
                "name": "Rudraprayag Transit Camp Delta",
                "shelter_type": "temporary_tent",
                "capacity": 800,
                "current_occupancy": 620,
                "occupancy_percent": 77.5,
                "location_name": "Upper Ridge Terrace, Rudraprayag",
                "supplies_status": "low",
                "power_backup": True,
                "medical_station": True,
                "status": "open",
                "is_demo": True,
            },
            {
                "id": "s1-0004",
                "name": "Brahmaputra Valley Emergency Camp 3",
                "shelter_type": "school",
                "capacity": 1500,
                "current_occupancy": 1500,
                "occupancy_percent": 100.0,
                "location_name": "Sector 6 Government High School",
                "supplies_status": "critical",
                "power_backup": False,
                "medical_station": True,
                "status": "full",
                "is_demo": True,
            },
        ]

    def _init_demo_activity(self) -> List[Dict[str, Any]]:
        now = utcnow()
        return [
            {
                "timestamp": now - timedelta(minutes=4),
                "actor": "Disaster Intelligence Bot",
                "action": "TELEMETRY_REFRESH",
                "description": "Brahmaputra hydro-gauge sensor at Station #Assam-04 registered +12cm surge.",
                "level": "warning",
            },
            {
                "timestamp": now - timedelta(minutes=14),
                "actor": "Commander R. K. Sharma",
                "action": "TEAM_DEPLOYMENT",
                "description": "NDRF-BRAVO-12 mobilized 6 inflatable rescue boats to Kamrup low-lying cluster.",
                "level": "info",
            },
            {
                "timestamp": now - timedelta(minutes=28),
                "actor": "State Emergency Operations Center",
                "action": "BROADCAST_ALERT",
                "description": "Red Warning ALT-2026-0091 escalated across coastal cellular cell-towers.",
                "level": "critical",
            },
            {
                "timestamp": now - timedelta(minutes=42),
                "actor": "Logistics Dispatcher",
                "action": "SUPPLY_TRANSFER",
                "description": "Airlift dispatch of 500 emergency water purification units to Camp Delta.",
                "level": "info",
            },
        ]


# Global service instance
rakshagrid_service = RakshaGridService()

"""
RakshaGrid Deterministic Development Seeding Script
Populates fictional, simulation-tagged disaster incidents, response teams,
tasks, shelters, and relief resources for local development and testing.
"""

import argparse
import json
import logging
import sys
import uuid
from datetime import datetime, timezone, timedelta
from pathlib import Path
from sqlalchemy.orm import Session

# Ensure project root is in sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from backend.database.session import Base, get_session_factory
from backend.rakshagrid.config import rakshagrid_settings
from backend.rakshagrid.models import (
    Incident,
    IncidentUpdate,
    ResponseTeam,
    ResponseTask,
    Shelter,
    Resource,
    ResourceMovement,
)

logger = logging.getLogger("rakshagrid.seeder")


def utcnow():
    return datetime.now(timezone.utc)


DEV_SEED_INCIDENTS = [
    {
        "id": uuid.UUID("f47ac10b-58cc-4372-a567-0e02b2c3d401"),
        "incident_code": "SIM-2026-FL-0001",
        "title": "[SIMULATION] Brahmaputra Basin Inundation & Embankment Surge",
        "description": "Simulated seasonal monsoonal inundation across Sector 4 low-lying village clusters. Breach simulation active for multi-agency table-top exercise.",
        "category": "flood",
        "severity": "critical",
        "status": "response_active",
        "latitude": 26.185,
        "longitude": 91.748,
        "location_description": "Guwahati Sector 4, Kamrup Metropolitan",
        "source_type": "simulation",
        "verification_status": "verified",
        "assigned_commander": "Cmdr. R. K. Sharma (NDRF)",
        "affected_population": 48200,
        "created_by": "dev-seed-engine",
    },
    {
        "id": uuid.UUID("f47ac10b-58cc-4372-a567-0e02b2c3d402"),
        "incident_code": "SIM-2026-SW-0002",
        "title": "[SIMULATION] Severe Cyclonic Storm 'Sagar' Coastal Tracking",
        "description": "Synthetic Category 3 cyclonic system tracking Northwest across Bay of Bengal. Used for coastal shelter evacuation buffer testing.",
        "category": "severe_weather",
        "severity": "high",
        "status": "confirmed",
        "latitude": 19.813,
        "longitude": 85.831,
        "location_description": "Puri Coastal Zone, Odisha",
        "source_type": "simulation",
        "verification_status": "verified",
        "assigned_commander": "Insp. Pradeep Mohanty (SDRF)",
        "affected_population": 125000,
        "created_by": "dev-seed-engine",
    },
    {
        "id": uuid.UUID("f47ac10b-58cc-4372-a567-0e02b2c3d403"),
        "incident_code": "SIM-2026-LS-0003",
        "title": "[SIMULATION] National Highway 58 Slope Debris Flow",
        "description": "Simulated slope failure blocking NH-58 at Km 44. Testing automated drone reconnaissance mobilization and traffic diversion protocols.",
        "category": "landslide",
        "severity": "high",
        "status": "under_assessment",
        "latitude": 30.146,
        "longitude": 78.784,
        "location_description": "Rudraprayag Ridge Km 44, Uttarakhand",
        "source_type": "simulation",
        "verification_status": "under_review",
        "assigned_commander": "Flight Lt. Vikram Joshi",
        "affected_population": 3200,
        "created_by": "dev-seed-engine",
    },
    {
        "id": uuid.UUID("f47ac10b-58cc-4372-a567-0e02b2c3d404"),
        "incident_code": "SIM-2026-EQ-0004",
        "title": "[SIMULATION] Foothills Seismic Event Magnitude 5.8",
        "description": "Simulated shallow focus seismic tremor testing masonry acoustic sensors and structural triage inspections across rural clinic facilities.",
        "category": "earthquake",
        "severity": "medium",
        "status": "contained",
        "latitude": 32.219,
        "longitude": 76.323,
        "location_description": "Kangra Foothills, Himachal Pradesh",
        "source_type": "simulation",
        "verification_status": "verified",
        "assigned_commander": "Dr. Ananya Sen (Medical Triage)",
        "affected_population": 18000,
        "created_by": "dev-seed-engine",
    },
    {
        "id": uuid.UUID("f47ac10b-58cc-4372-a567-0e02b2c3d405"),
        "incident_code": "SIM-2026-WF-0005",
        "title": "[SIMULATION] Simlipal Reserve Buffer Zone Firebreak Exercise",
        "description": "Simulated dry canopy fire spread testing aerial water bucket drop coordination with forest protection teams.",
        "category": "wildfire",
        "severity": "low",
        "status": "resolved",
        "latitude": 21.642,
        "longitude": 86.345,
        "location_description": "Baripada Sector West, Mayurbhanj",
        "source_type": "simulation",
        "verification_status": "verified",
        "assigned_commander": "Capt. Meera Nair",
        "affected_population": 1400,
        "created_by": "dev-seed-engine",
    },
]

DEV_SEED_SHELTERS = [
    {
        "id": uuid.UUID("a11ac10b-58cc-4372-a567-0e02b2c3d001"),
        "name": "Puri Coastal Multi-Purpose Cyclone Shelter",
        "shelter_type": "Cyclone Shelter",
        "capacity": 1200,
        "current_occupancy": 480,
        "latitude": 19.805,
        "longitude": 85.818,
        "address": "Marine Drive Sector 2, Puri, Odisha",
        "contact_person": "M. K. Das",
        "contact_phone": "+91-6752-224411",
        "supplies_status": "adequate",
        "power_backup": True,
        "medical_station": True,
        "status": "open",
    },
    {
        "id": uuid.UUID("a11ac10b-58cc-4372-a567-0e02b2c3d002"),
        "name": "Guwahati Higher Secondary Relief Camp",
        "shelter_type": "School / Community Hall",
        "capacity": 800,
        "current_occupancy": 650,
        "latitude": 26.178,
        "longitude": 91.753,
        "address": "G.S. Road, Kamrup Metropolitan, Assam",
        "contact_person": "B. C. Barman",
        "contact_phone": "+91-361-2458900",
        "supplies_status": "adequate",
        "power_backup": True,
        "medical_station": True,
        "status": "open",
    },
    {
        "id": uuid.UUID("a11ac10b-58cc-4372-a567-0e02b2c3d003"),
        "name": "Rudraprayag Community Staging Shelter",
        "shelter_type": "Evacuation Center",
        "capacity": 350,
        "current_occupancy": 110,
        "latitude": 30.138,
        "longitude": 78.775,
        "address": "Kedarnath Valley Access Way, Rudraprayag, Uttarakhand",
        "contact_person": "D. Rawat",
        "contact_phone": "+91-1364-233110",
        "supplies_status": "adequate",
        "power_backup": True,
        "medical_station": True,
        "status": "open",
    },
    {
        "id": uuid.UUID("a11ac10b-58cc-4372-a567-0e02b2c3d004"),
        "name": "Dharamshala Indoor Stadium Relief Hub",
        "shelter_type": "Stadium / Sports Complex",
        "capacity": 2500,
        "current_occupancy": 0,
        "latitude": 32.221,
        "longitude": 76.319,
        "address": "Kotwali Bazaar Road, Kangra, Himachal Pradesh",
        "contact_person": "Sunil Thakur",
        "contact_phone": "+91-1892-228760",
        "supplies_status": "adequate",
        "power_backup": True,
        "medical_station": True,
        "status": "open",
    },
]

DEV_SEED_TEAMS = [
    {
        "id": uuid.UUID("b22ac10b-58cc-4372-a567-0e02b2c3d001"),
        "team_callsign": "NDRF-12-BRAVO",
        "unit_type": "NDRF Urban Search & Rescue",
        "personnel_count": 45,
        "commander_name": "Cmdr. R. K. Sharma",
        "contact_channel": "VHF CH-16 (156.800 MHz)",
        "current_status": "assigned",
        "current_latitude": 26.182,
        "current_longitude": 91.745,
        "base_location": "Guwahati Riverfront Staging Base",
        "assigned_base_shelter_id": uuid.UUID("a11ac10b-58cc-4372-a567-0e02b2c3d002"),
        "assigned_incident_id": uuid.UUID("f47ac10b-58cc-4372-a567-0e02b2c3d401"),
    },
    {
        "id": uuid.UUID("b22ac10b-58cc-4372-a567-0e02b2c3d002"),
        "team_callsign": "SDRF-ODISHA-04",
        "unit_type": "SDRF Coastal Cyclone Battalion",
        "personnel_count": 35,
        "commander_name": "Insp. Pradeep Mohanty",
        "contact_channel": "SAT-PHONE #8816-419",
        "current_status": "assigned",
        "current_latitude": 19.810,
        "current_longitude": 85.825,
        "base_location": "Puri District Staging HQ",
        "assigned_base_shelter_id": uuid.UUID("a11ac10b-58cc-4372-a567-0e02b2c3d001"),
        "assigned_incident_id": uuid.UUID("f47ac10b-58cc-4372-a567-0e02b2c3d402"),
    },
    {
        "id": uuid.UUID("b22ac10b-58cc-4372-a567-0e02b2c3d003"),
        "team_callsign": "MED-TRIAGE-ALPHA",
        "unit_type": "Mobile Trauma & Emergency Medical Unit",
        "personnel_count": 18,
        "commander_name": "Dr. Ananya Sen",
        "contact_channel": "MED-COMM Frequency 412.35 MHz",
        "current_status": "available",
        "current_latitude": 26.175,
        "current_longitude": 91.760,
        "base_location": "Guwahati Medical College Perimeter",
        "assigned_base_shelter_id": uuid.UUID("a11ac10b-58cc-4372-a567-0e02b2c3d002"),
        "assigned_incident_id": None,
    },
    {
        "id": uuid.UUID("b22ac10b-58cc-4372-a567-0e02b2c3d004"),
        "team_callsign": "AERO-DRONE-RECON-7",
        "unit_type": "Aerial Drone Reconnaissance & Thermal Survey",
        "personnel_count": 6,
        "commander_name": "Flight Lt. Vikram Joshi",
        "contact_channel": "UAV Telemetry Encrypted 5.8GHz",
        "current_status": "assigned",
        "current_latitude": 30.145,
        "current_longitude": 78.780,
        "base_location": "Rudraprayag Helipad Staging",
        "assigned_base_shelter_id": uuid.UUID("a11ac10b-58cc-4372-a567-0e02b2c3d003"),
        "assigned_incident_id": uuid.UUID("f47ac10b-58cc-4372-a567-0e02b2c3d403"),
    },
    {
        "id": uuid.UUID("b22ac10b-58cc-4372-a567-0e02b2c3d005"),
        "team_callsign": "HAZMAT-CONTAIN-02",
        "unit_type": "Chemical & Environmental HAZMAT Unit",
        "personnel_count": 12,
        "commander_name": "Capt. Meera Nair",
        "contact_channel": "HAZMAT Secure Line #3",
        "current_status": "available",
        "current_latitude": 21.640,
        "current_longitude": 86.340,
        "base_location": "Baripada Industrial Logistics Depot",
        "assigned_base_shelter_id": None,
        "assigned_incident_id": None,
    },
]

DEV_SEED_TASKS = [
    {
        "id": uuid.UUID("c33ac10b-58cc-4372-a567-0e02b2c3d001"),
        "incident_id": uuid.UUID("f47ac10b-58cc-4372-a567-0e02b2c3d401"),
        "assigned_team_id": uuid.UUID("b22ac10b-58cc-4372-a567-0e02b2c3d001"),
        "title": "Deploy 6 Inflatable Rescue Boats to Sector 4 Low-Lands",
        "description": "Evacuate 120 stranded residents from waterlogged riverine wards. Establish shallow-water ferry corridor.",
        "priority": "critical",
        "status": "in_progress",
        "target_latitude": 26.185,
        "target_longitude": 91.748,
    },
    {
        "id": uuid.UUID("c33ac10b-58cc-4372-a567-0e02b2c3d002"),
        "incident_id": uuid.UUID("f47ac10b-58cc-4372-a567-0e02b2c3d401"),
        "assigned_team_id": None,
        "title": "Establish Emergency Trauma Triage at Assam High Grounds",
        "description": "Set up secondary field stabilization point with sterile hydration packs and antivenom stockpiles.",
        "priority": "critical",
        "status": "pending",
        "target_latitude": 26.178,
        "target_longitude": 91.753,
    },
    {
        "id": uuid.UUID("c33ac10b-58cc-4372-a567-0e02b2c3d003"),
        "incident_id": uuid.UUID("f47ac10b-58cc-4372-a567-0e02b2c3d402"),
        "assigned_team_id": uuid.UUID("b22ac10b-58cc-4372-a567-0e02b2c3d002"),
        "title": "Verify Structural Integrity of Puri Cyclone Shelter Alpha",
        "description": "Inspect reinforced concrete cyclone baffle walls and calibrate storm shutter locking mechanisms.",
        "priority": "high",
        "status": "in_progress",
        "target_latitude": 19.805,
        "target_longitude": 85.818,
    },
    {
        "id": uuid.UUID("c33ac10b-58cc-4372-a567-0e02b2c3d004"),
        "incident_id": uuid.UUID("f47ac10b-58cc-4372-a567-0e02b2c3d403"),
        "assigned_team_id": uuid.UUID("b22ac10b-58cc-4372-a567-0e02b2c3d004"),
        "title": "Aerial Drone Survey of Km 44 Debris Ridge",
        "description": "Capture volumetric elevation models of the rockslide debris tongue to guide hydraulic earthmovers.",
        "priority": "high",
        "status": "in_progress",
        "target_latitude": 30.146,
        "target_longitude": 78.784,
    },
    {
        "id": uuid.UUID("c33ac10b-58cc-4372-a567-0e02b2c3d005"),
        "incident_id": uuid.UUID("f47ac10b-58cc-4372-a567-0e02b2c3d405"),
        "assigned_team_id": None,
        "title": "Coordinate Aerial Water Drop Perimeter with Forestry Division",
        "description": "Establish thermal perimeter survey line and mark dry canopy coordinates for airborne retardant drops.",
        "priority": "medium",
        "status": "completed",
        "target_latitude": 21.642,
        "target_longitude": 86.345,
    },
]

DEV_SEED_RESOURCES = [
    {
        "id": uuid.UUID("d44ac10b-58cc-4372-a567-0e02b2c3d001"),
        "resource_code": "RES-MED-01",
        "name": "Emergency Trauma & Surgical Field Kits",
        "category": "Medical",
        "quantity_total": 450.0,
        "quantity_available": 310.0,
        "unit": "kits",
        "shelter_id": uuid.UUID("a11ac10b-58cc-4372-a567-0e02b2c3d002"),
        "storage_location": "Guwahati Central Depot",
        "status": "in_stock",
    },
    {
        "id": uuid.UUID("d44ac10b-58cc-4372-a567-0e02b2c3d002"),
        "resource_code": "RES-WAT-02",
        "name": "Reverse Osmosis Mobile Water Purification Units",
        "category": "Food & Water",
        "quantity_total": 60.0,
        "quantity_available": 42.0,
        "unit": "units",
        "shelter_id": uuid.UUID("a11ac10b-58cc-4372-a567-0e02b2c3d001"),
        "storage_location": "Puri Municipal Warehouse",
        "status": "in_stock",
    },
    {
        "id": uuid.UUID("d44ac10b-58cc-4372-a567-0e02b2c3d003"),
        "resource_code": "RES-RFT-03",
        "name": "Inflatable High-Tonnage Flood Rescue Rafts",
        "category": "Rescue Equipment",
        "quantity_total": 120.0,
        "quantity_available": 45.0,
        "unit": "craft",
        "shelter_id": uuid.UUID("a11ac10b-58cc-4372-a567-0e02b2c3d002"),
        "storage_location": "Assam Relief Logistics Center",
        "status": "in_stock",
    },
    {
        "id": uuid.UUID("d44ac10b-58cc-4372-a567-0e02b2c3d004"),
        "resource_code": "RES-PWR-04",
        "name": "Heavy-Duty Diesel Generator Units (45kVA)",
        "category": "Power & Fuel",
        "quantity_total": 35.0,
        "quantity_available": 12.0,
        "unit": "generators",
        "shelter_id": uuid.UUID("a11ac10b-58cc-4372-a567-0e02b2c3d003"),
        "storage_location": "Rudraprayag Staging Yard",
        "status": "in_stock",
    },
    {
        "id": uuid.UUID("d44ac10b-58cc-4372-a567-0e02b2c3d005"),
        "resource_code": "RES-RAT-05",
        "name": "High-Calorie Ready-to-Eat Disaster Rations",
        "category": "Food & Water",
        "quantity_total": 15000.0,
        "quantity_available": 11400.0,
        "unit": "packs",
        "shelter_id": uuid.UUID("a11ac10b-58cc-4372-a567-0e02b2c3d001"),
        "storage_location": "Kolkata Regional Logistics Depot",
        "status": "in_stock",
    },
    {
        "id": uuid.UUID("d44ac10b-58cc-4372-a567-0e02b2c3d006"),
        "resource_code": "RES-TNT-06",
        "name": "All-Weather Modular Family Shelter Tents",
        "category": "Shelter Gear",
        "quantity_total": 800.0,
        "quantity_available": 220.0,
        "unit": "units",
        "shelter_id": uuid.UUID("a11ac10b-58cc-4372-a567-0e02b2c3d001"),
        "storage_location": "Puri Cyclone Reserve",
        "status": "in_stock",
    },
]


def seed_dev_incidents(db: Session, reset: bool = False) -> dict:
    """
    Deterministically seeds simulated development incidents, teams, tasks,
    shelters, and resources into the database.
    """
    if rakshagrid_settings.is_production:
        raise RuntimeError("Deterministic seeding is strictly prohibited in production environment!")

    engine = db.get_bind()
    Base.metadata.create_all(bind=engine)

    inserted_incidents = 0
    skipped_incidents = 0
    deleted = 0
    inserted_shelters = 0
    inserted_teams = 0
    inserted_tasks = 0
    inserted_resources = 0

    if reset:
        deleted = (
            db.query(Incident)
            .filter(Incident.source_type == "simulation")
            .delete(synchronize_session=False)
        )
        db.commit()

    now = utcnow()

    # 1. Incidents
    for item in DEV_SEED_INCIDENTS:
        existing = db.query(Incident).filter(Incident.incident_code == item["incident_code"]).first()
        if existing:
            skipped_incidents += 1
            continue

        incident = Incident(
            id=item["id"],
            incident_code=item["incident_code"],
            title=item["title"],
            description=item["description"],
            category=item["category"],
            severity=item["severity"],
            status=item["status"],
            latitude=item["latitude"],
            longitude=item["longitude"],
            location_description=item["location_description"],
            source_type=item["source_type"],
            verification_status=item["verification_status"],
            assigned_commander=item["assigned_commander"],
            affected_population=item["affected_population"],
            created_by=item["created_by"],
            reported_at=now - timedelta(hours=6),
            created_at=now - timedelta(hours=6),
            updated_at=now - timedelta(minutes=15),
        )
        history = IncidentUpdate(
            id=uuid.uuid4(),
            incident_id=item["id"],
            actor_id="dev-seed-engine",
            previous_status=None,
            new_status=item["status"],
            update_type="creation",
            message=f"Simulation baseline initialized for table-top exercise: {item['incident_code']}",
            metadata_payload=json.dumps({"source": "deterministic_seed", "severity": item["severity"]}),
            created_at=now - timedelta(hours=6),
        )
        db.add(incident)
        db.add(history)
        inserted_incidents += 1

    db.commit()

    # 2. Shelters
    for item in DEV_SEED_SHELTERS:
        existing = db.query(Shelter).filter(Shelter.id == item["id"]).first()
        if not existing:
            sh = Shelter(
                id=item["id"],
                name=item["name"],
                shelter_type=item["shelter_type"],
                capacity=item["capacity"],
                current_occupancy=item["current_occupancy"],
                latitude=item["latitude"],
                longitude=item["longitude"],
                address=item["address"],
                contact_person=item["contact_person"],
                contact_phone=item["contact_phone"],
                supplies_status=item["supplies_status"],
                power_backup=item["power_backup"],
                medical_station=item["medical_station"],
                status=item["status"],
                created_at=now - timedelta(hours=12),
                updated_at=now - timedelta(hours=1),
            )
            db.add(sh)
            inserted_shelters += 1

    db.commit()

    # 3. Teams
    for item in DEV_SEED_TEAMS:
        existing = db.query(ResponseTeam).filter(ResponseTeam.team_callsign == item["team_callsign"]).first()
        if not existing:
            tm = ResponseTeam(
                id=item["id"],
                team_callsign=item["team_callsign"],
                unit_type=item["unit_type"],
                personnel_count=item["personnel_count"],
                commander_name=item["commander_name"],
                contact_channel=item["contact_channel"],
                current_status=item["current_status"],
                current_latitude=item["current_latitude"],
                current_longitude=item["current_longitude"],
                base_location=item["base_location"],
                assigned_base_shelter_id=item["assigned_base_shelter_id"],
                assigned_incident_id=item["assigned_incident_id"],
                created_at=now - timedelta(hours=12),
                updated_at=now - timedelta(hours=1),
            )
            db.add(tm)
            inserted_teams += 1

    db.commit()

    # 4. Tasks
    for item in DEV_SEED_TASKS:
        existing = db.query(ResponseTask).filter(ResponseTask.id == item["id"]).first()
        if not existing:
            tsk = ResponseTask(
                id=item["id"],
                incident_id=item["incident_id"],
                assigned_team_id=item["assigned_team_id"],
                title=item["title"],
                description=item["description"],
                priority=item["priority"],
                status=item["status"],
                target_latitude=item["target_latitude"],
                target_longitude=item["target_longitude"],
                due_at=now + timedelta(hours=3),
                completed_at=now if item["status"] == "completed" else None,
                created_at=now - timedelta(hours=3),
                updated_at=now - timedelta(minutes=30),
            )
            db.add(tsk)
            inserted_tasks += 1

    db.commit()

    # 5. Resources
    for item in DEV_SEED_RESOURCES:
        existing = db.query(Resource).filter(Resource.resource_code == item["resource_code"]).first()
        if not existing:
            res = Resource(
                id=item["id"],
                resource_code=item["resource_code"],
                name=item["name"],
                category=item["category"],
                quantity_total=item["quantity_total"],
                quantity_available=item["quantity_available"],
                unit=item["unit"],
                shelter_id=item["shelter_id"],
                storage_location=item["storage_location"],
                status=item["status"],
                created_at=now - timedelta(hours=24),
                updated_at=now - timedelta(hours=2),
            )
            db.add(res)
            inserted_resources += 1

    db.commit()

    return {
        "status": "success",
        "inserted": inserted_incidents,
        "skipped": skipped_incidents,
        "reset_deleted": deleted,
        "total_seed_templates": len(DEV_SEED_INCIDENTS),
        "incidents_seeded": inserted_incidents,
        "shelters_seeded": inserted_shelters,
        "teams_seeded": inserted_teams,
        "tasks_seeded": inserted_tasks,
        "resources_seeded": inserted_resources,
    }


def main():
    parser = argparse.ArgumentParser(description="Seed deterministic disaster incidents and coordination data.")
    parser.add_argument("--reset", action="store_true", help="Clear existing simulation records before seeding.")
    args = parser.parse_args()

    factory = get_session_factory()
    with factory() as db:
        res = seed_dev_incidents(db, reset=args.reset)
        print(f"Seed complete: {res}")


if __name__ == "__main__":
    main()

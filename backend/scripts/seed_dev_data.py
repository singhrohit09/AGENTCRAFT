"""
RakshaGrid Deterministic Development Seeding Script
Populates fictional, simulation-tagged disaster incidents and timeline histories
for local development, verification, and automated UI testing.
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

from backend.database.session import Base, get_engine, get_session_factory
from backend.rakshagrid.config import rakshagrid_settings
from backend.rakshagrid.models import Incident, IncidentUpdate

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


def seed_dev_incidents(db: Session, reset: bool = False) -> dict:
    """
    Deterministically seeds simulated development incidents into the database.
    Idempotent: skips records that already exist by incident_code.
    Safeguard: strictly prohibited in production.
    """
    if rakshagrid_settings.is_production:
        raise RuntimeError("Deterministic seeding is strictly prohibited in production environment!")

    # Ensure tables exist
    engine = db.get_bind()
    Base.metadata.create_all(bind=engine)

    inserted = 0
    skipped = 0
    deleted = 0

    if reset:
        # Delete only simulation records to protect user-created operational entries
        deleted = (
            db.query(Incident)
            .filter(Incident.source_type == "simulation")
            .delete(synchronize_session=False)
        )
        db.commit()

    now = utcnow()

    for item in DEV_SEED_INCIDENTS:
        existing = db.query(Incident).filter(Incident.incident_code == item["incident_code"]).first()
        if existing:
            skipped += 1
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
        inserted += 1

    db.commit()
    return {
        "status": "success",
        "inserted": inserted,
        "skipped": skipped,
        "reset_deleted": deleted,
        "total_seed_templates": len(DEV_SEED_INCIDENTS),
    }


def main():
    parser = argparse.ArgumentParser(description="Seed deterministic fictional disaster incidents for development.")
    parser.add_argument("--reset", action="store_true", help="Clear existing simulation records before seeding.")
    args = parser.parse_args()

    factory = get_session_factory()
    with factory() as db:
        res = seed_dev_incidents(db, reset=args.reset)
        print(f"Seed complete: {res['inserted']} inserted, {res['skipped']} skipped, {res['reset_deleted']} reset.")


if __name__ == "__main__":
    main()

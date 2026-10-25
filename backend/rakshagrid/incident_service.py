"""
Incident Service Layer
Coordinates database transactions, status transition rules,
full-text search, and historical audit logging for disaster incidents.
"""

import json
import logging
import math
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple, Union
from sqlalchemy import or_, desc, asc, func
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from backend.rakshagrid.auth import UserIdentity, UserRole
from backend.rakshagrid.config import rakshagrid_settings
from backend.rakshagrid.incident_schemas import (
    IncidentCreate,
    IncidentUpdatePatch,
    IncidentUpdateCreate,
    IncidentCategory,
    IncidentSeverity,
    IncidentStatus,
    VALID_STATUS_TRANSITIONS,
)
from backend.rakshagrid.models import Incident, IncidentUpdate

logger = logging.getLogger("rakshagrid.incident_service")


def utcnow():
    return datetime.now(timezone.utc)


def parse_uuid(val: Union[str, uuid.UUID]) -> uuid.UUID:
    if isinstance(val, uuid.UUID):
        return val
    try:
        return uuid.UUID(str(val))
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=422,
            detail=f"Invalid UUID format: '{val}'",
        )


def generate_incident_code(category: str, db: Session) -> str:
    """Generates a sequential human-readable incident code (e.g., RG-2026-FL-0001)."""
    prefix_map = {
        "flood": "FL",
        "severe_weather": "SW",
        "wildfire": "WF",
        "earthquake": "EQ",
        "landslide": "LS",
        "industrial_accident": "IA",
        "other": "HZ",
    }
    cat_prefix = prefix_map.get(category.lower(), "HZ")
    year = utcnow().year
    # Count existing incidents for this category to determine sequence
    count = db.query(func.count(Incident.id)).scalar() or 0
    return f"RG-{year}-{cat_prefix}-{count + 1:04d}"


class IncidentService:
    """Manages transactional CRUD operations, status state transitions, and audit updates."""

    def create_incident(self, db: Session, payload: IncidentCreate, caller: UserIdentity) -> Incident:
        """
        Atomically persists a new incident and logs its creation history.
        Transaction rolls back if history logging fails.
        """
        category_val = payload.category.value if isinstance(payload.category, IncidentCategory) else str(payload.category)
        severity_val = payload.severity.value if isinstance(payload.severity, IncidentSeverity) else str(payload.severity)
        status_val = payload.status.value if isinstance(payload.status, IncidentStatus) else str(payload.status)
        source_type_val = payload.source_type.value if hasattr(payload.source_type, "value") else str(payload.source_type)
        verif_val = payload.verification_status.value if hasattr(payload.verification_status, "value") else str(payload.verification_status)

        incident_code = generate_incident_code(category_val, db)
        incident_id = uuid.uuid4()
        now = utcnow()

        incident = Incident(
            id=incident_id,
            incident_code=incident_code,
            title=payload.title,
            description=payload.description,
            category=category_val,
            severity=severity_val,
            status=status_val,
            latitude=payload.latitude,
            longitude=payload.longitude,
            location_description=payload.location_description or "Unspecified Location",
            source_type=source_type_val,
            verification_status=verif_val,
            reported_at=payload.reported_at or now,
            created_by=caller.user_id,
            assigned_commander=payload.assigned_commander,
            affected_population=payload.affected_population or 0,
            created_at=now,
            updated_at=now,
        )

        creation_history = IncidentUpdate(
            id=uuid.uuid4(),
            incident_id=incident_id,
            actor_id=caller.user_id,
            previous_status=None,
            new_status=status_val,
            update_type="creation",
            message=f"Incident {incident_code} logged: '{payload.title}' by {caller.user_id}",
            metadata_payload=json.dumps({
                "action": "create",
                "severity": severity_val,
                "category": category_val,
                "source_type": source_type_val,
                "auth_mechanism": caller.auth_mechanism,
            }),
            created_at=now,
        )

        try:
            db.add(incident)
            db.add(creation_history)
            db.commit()
            db.refresh(incident)
            return incident
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to create incident: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Database transaction aborted: {str(e)}",
            )

    def list_incidents(
        self,
        db: Session,
        page: int = 1,
        page_size: int = 20,
        category: Optional[str] = None,
        severity: Optional[str] = None,
        status_filter: Optional[str] = None,
        verification_status: Optional[str] = None,
        search: Optional[str] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> Tuple[List[Incident], int, int]:
        """
        Queries incidents with pagination, multi-criteria filtering, text search, and sorting.
        Returns: (items, total_count, total_pages)
        """
        page = max(1, page)
        max_limit = rakshagrid_settings.PAGINATION_MAX_PAGE_SIZE
        if page_size > max_limit:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Requested page_size {page_size} exceeds maximum allowable limit of {max_limit}",
            )
        page_size = max(1, page_size)

        query = db.query(Incident)

        # Filters
        if category:
            norm_cat = IncidentCategory.normalize(category).value
            query = query.filter(Incident.category == norm_cat)
        if severity:
            norm_sev = IncidentSeverity.normalize(severity).value
            query = query.filter(Incident.severity == norm_sev)
        if status_filter:
            norm_stat = IncidentStatus.normalize(status_filter).value
            query = query.filter(Incident.status == norm_stat)
        if verification_status:
            query = query.filter(Incident.verification_status == verification_status.lower().strip())

        # Full-text / Substring search across title, description, location
        if search and search.strip():
            term = f"%{search.strip()}%"
            query = query.filter(
                or_(
                    Incident.title.ilike(term),
                    Incident.description.ilike(term),
                    Incident.location_description.ilike(term),
                    Incident.incident_code.ilike(term),
                )
            )

        total_count = query.count()
        total_pages = math.ceil(total_count / page_size) if total_count > 0 else 1

        # Sorting
        sort_col = Incident.reported_at if sort_by == "reported_at" else Incident.created_at
        order_func = desc if sort_order.lower() == "desc" else asc
        query = query.order_by(order_func(sort_col))

        # Pagination slice
        offset = (page - 1) * page_size
        items = query.offset(offset).limit(page_size).all()

        return items, total_count, total_pages

    def get_incident(self, db: Session, incident_id: Union[str, uuid.UUID]) -> Incident:
        """Retrieves an incident by UUID, raising 404 if not found."""
        parsed_id = parse_uuid(incident_id)
        incident = db.query(Incident).filter(Incident.id == parsed_id).first()
        if not incident:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Incident with ID '{parsed_id}' does not exist.",
            )
        return incident

    def update_incident(
        self,
        db: Session,
        incident_id: Union[str, uuid.UUID],
        payload: IncidentUpdatePatch,
        caller: UserIdentity,
    ) -> Incident:
        """
        Updates permitted incident fields and records a historical audit update.
        Enforces valid status state transitions.
        """
        incident = self.get_incident(db, incident_id)
        changed_fields = {}
        old_status = incident.status

        # Status transition verification
        if payload.status is not None:
            new_status_val = payload.status.value if isinstance(payload.status, IncidentStatus) else str(payload.status)
            if new_status_val != old_status:
                valid_next_states = VALID_STATUS_TRANSITIONS.get(old_status, [])
                # Allow admin override, else enforce state machine
                if caller.role != UserRole.ADMIN and new_status_val not in valid_next_states:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=(
                            f"Invalid status transition from '{old_status}' to '{new_status_val}'. "
                            f"Permitted transitions from '{old_status}': {valid_next_states}"
                        ),
                    )
                changed_fields["status"] = {"old": old_status, "new": new_status_val}
                incident.status = new_status_val

        # Update remaining permitted fields
        if payload.title is not None and payload.title != incident.title:
            changed_fields["title"] = {"old": incident.title, "new": payload.title}
            incident.title = payload.title

        if payload.description is not None and payload.description != incident.description:
            changed_fields["description"] = "updated"
            incident.description = payload.description

        if payload.category is not None:
            cat_val = payload.category.value if isinstance(payload.category, IncidentCategory) else str(payload.category)
            if cat_val != incident.category:
                changed_fields["category"] = {"old": incident.category, "new": cat_val}
                incident.category = cat_val

        if payload.severity is not None:
            sev_val = payload.severity.value if isinstance(payload.severity, IncidentSeverity) else str(payload.severity)
            if sev_val != incident.severity:
                changed_fields["severity"] = {"old": incident.severity, "new": sev_val}
                incident.severity = sev_val

        if payload.latitude is not None:
            changed_fields["latitude"] = {"old": incident.latitude, "new": payload.latitude}
            incident.latitude = payload.latitude

        if payload.longitude is not None:
            changed_fields["longitude"] = {"old": incident.longitude, "new": payload.longitude}
            incident.longitude = payload.longitude

        if payload.location_description is not None:
            changed_fields["location_description"] = {"old": incident.location_description, "new": payload.location_description}
            incident.location_description = payload.location_description

        if payload.assigned_commander is not None:
            changed_fields["assigned_commander"] = {"old": incident.assigned_commander, "new": payload.assigned_commander}
            incident.assigned_commander = payload.assigned_commander

        if payload.affected_population is not None:
            changed_fields["affected_population"] = {"old": incident.affected_population, "new": payload.affected_population}
            incident.affected_population = payload.affected_population

        if payload.verification_status is not None:
            ver_val = payload.verification_status.value if hasattr(payload.verification_status, "value") else str(payload.verification_status)
            changed_fields["verification_status"] = {"old": incident.verification_status, "new": ver_val}
            incident.verification_status = ver_val

        # If nothing changed, return current record
        if not changed_fields:
            return incident

        incident.updated_at = utcnow()

        # Build update record
        update_type = "status_change" if "status" in changed_fields else "modification"
        msg = payload.change_reason or f"Incident updated: {', '.join(changed_fields.keys())} modified by {caller.user_id}"

        history_update = IncidentUpdate(
            id=uuid.uuid4(),
            incident_id=incident.id,
            actor_id=caller.user_id,
            previous_status=old_status,
            new_status=incident.status,
            update_type=update_type,
            message=msg,
            metadata_payload=json.dumps(changed_fields),
            created_at=utcnow(),
        )

        try:
            db.add(history_update)
            db.commit()
            db.refresh(incident)
            return incident
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update incident: {str(e)}",
            )

    def list_incident_updates(
        self,
        db: Session,
        incident_id: Union[str, uuid.UUID],
        page: int = 1,
        page_size: int = 50,
    ) -> Tuple[List[IncidentUpdate], int]:
        """Returns the chronological timeline of updates for an incident."""
        incident = self.get_incident(db, incident_id)
        query = db.query(IncidentUpdate).filter(IncidentUpdate.incident_id == incident.id)
        total = query.count()
        updates = (
            query.order_by(asc(IncidentUpdate.created_at))
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        return updates, total

    def add_incident_update(
        self,
        db: Session,
        incident_id: Union[str, uuid.UUID],
        payload: IncidentUpdateCreate,
        caller: UserIdentity,
    ) -> IncidentUpdate:
        """Appends a new verified update or situation report to an incident timeline."""
        incident = self.get_incident(db, incident_id)
        now = utcnow()

        old_status = incident.status
        new_status = old_status

        if payload.new_status is not None:
            stat_val = payload.new_status.value if isinstance(payload.new_status, IncidentStatus) else str(payload.new_status)
            if stat_val != old_status:
                incident.status = stat_val
                incident.updated_at = now
                new_status = stat_val

        meta_json = json.dumps(payload.metadata_payload) if payload.metadata_payload else None

        update_record = IncidentUpdate(
            id=uuid.uuid4(),
            incident_id=incident.id,
            actor_id=caller.user_id,
            previous_status=old_status,
            new_status=new_status,
            update_type=payload.update_type or "situation_report",
            message=payload.message,
            metadata_payload=meta_json,
            created_at=now,
        )

        try:
            db.add(update_record)
            db.commit()
            db.refresh(update_record)
            return update_record
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to append timeline update: {str(e)}",
            )

    def archive_or_delete_incident(
        self,
        db: Session,
        incident_id: Union[str, uuid.UUID],
        caller: UserIdentity,
        permanent: bool = False,
    ) -> Dict[str, Any]:
        """
        Closes/archives incident or performs permanent administrative deletion.
        Enforces admin role requirement.
        """
        if caller.role != UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Incident archival and deletion is restricted to authorized administrators.",
            )

        incident = self.get_incident(db, incident_id)

        if not permanent:
            # Documented archival/closure workflow
            old_status = incident.status
            incident.status = IncidentStatus.CLOSED.value
            incident.updated_at = utcnow()
            archive_update = IncidentUpdate(
                id=uuid.uuid4(),
                incident_id=incident.id,
                actor_id=caller.user_id,
                previous_status=old_status,
                new_status=IncidentStatus.CLOSED.value,
                update_type="closure",
                message=f"Incident closed and archived by administrator: {caller.user_id}",
                created_at=utcnow(),
            )
            db.add(archive_update)
            db.commit()
            return {
                "success": True,
                "action": "archived",
                "incident_id": str(incident.id),
                "incident_code": incident.incident_code,
                "status": "closed",
                "message": "Incident record has been archived and marked closed.",
            }

        # Permanent destructive deletion
        code = incident.incident_code
        db.delete(incident)
        db.commit()
        return {
            "success": True,
            "action": "deleted",
            "incident_id": str(incident_id),
            "incident_code": code,
            "message": "Incident record and associated timeline have been permanently removed.",
        }


# Global singleton instance
incident_service = IncidentService()

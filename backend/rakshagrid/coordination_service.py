"""
RakshaGrid Phase 3 Coordination & Disaster Logistics Service
Implements database operations, relational validations, referential integrity,
and atomic state transitions for Teams, Tasks, Shelters, and Resources.
"""

import math
import uuid
from datetime import datetime, timezone
from typing import List, Optional, Tuple
from fastapi import HTTPException, status
from sqlalchemy import or_, and_, desc, asc
from sqlalchemy.orm import Session, joinedload

from backend.rakshagrid.models import (
    Incident,
    ResponseTeam,
    ResponseTask,
    Shelter,
    Resource,
    ResourceMovement,
)
from backend.rakshagrid.coordination_schemas import (
    TeamCreate,
    TeamUpdatePatch,
    TeamResponse,
    TaskCreate,
    TaskUpdatePatch,
    TaskResponse,
    ShelterCreate,
    ShelterUpdatePatch,
    ShelterResponse,
    ResourceCreate,
    ResourceUpdatePatch,
    ResourceAllocateRequest,
    ResourceReturnRequest,
    ResourceResponse,
    ResourceMovementResponse,
)


def utcnow():
    return datetime.now(timezone.utc)


def parse_uuid(val: str, field_name: str = "ID") -> uuid.UUID:
    try:
        return uuid.UUID(str(val))
    except (ValueError, TypeError, AttributeError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid UUID format for {field_name}: '{val}'",
        )


class CoordinationService:
    """Manages transactional logistics and operational coordination."""

    # ==========================================================================
    # Response Teams
    # ==========================================================================

    def list_teams(
        self,
        db: Session,
        page: int = 1,
        page_size: int = 20,
        status_filter: Optional[str] = None,
        unit_type: Optional[str] = None,
        search: Optional[str] = None,
    ) -> Tuple[List[TeamResponse], int, int]:
        query = db.query(ResponseTeam).options(
            joinedload(ResponseTeam.tasks),
            joinedload(ResponseTeam.assigned_incident),
        )

        if status_filter:
            norm_status = status_filter.strip().lower()
            if norm_status == "standby":
                norm_status = "available"
            elif norm_status == "deployed":
                norm_status = "assigned"
            query = query.filter(ResponseTeam.current_status == norm_status)

        if unit_type:
            query = query.filter(ResponseTeam.unit_type.ilike(f"%{unit_type.strip()}%"))

        if search:
            s = f"%{search.strip()}%"
            query = query.filter(
                or_(
                    ResponseTeam.team_callsign.ilike(s),
                    ResponseTeam.commander_name.ilike(s),
                    ResponseTeam.base_location.ilike(s),
                    ResponseTeam.contact_channel.ilike(s),
                )
            )

        total = query.count()
        total_pages = max(1, math.ceil(total / page_size))
        offset = (page - 1) * page_size
        teams = query.order_by(asc(ResponseTeam.team_callsign)).offset(offset).limit(page_size).all()

        results = []
        for t in teams:
            active_tasks = sum(1 for task in t.tasks if task.status in ("pending", "in_progress"))
            results.append(
                TeamResponse(
                    id=str(t.id),
                    team_callsign=t.team_callsign,
                    unit_type=t.unit_type,
                    personnel_count=t.personnel_count,
                    commander_name=t.commander_name,
                    contact_channel=t.contact_channel,
                    current_status=t.current_status,
                    current_latitude=t.current_latitude,
                    current_longitude=t.current_longitude,
                    base_location=t.base_location,
                    assigned_base_shelter_id=str(t.assigned_base_shelter_id) if t.assigned_base_shelter_id else None,
                    assigned_incident_id=str(t.assigned_incident_id) if t.assigned_incident_id else None,
                    assigned_incident_title=t.assigned_incident.title if t.assigned_incident else None,
                    assigned_incident_code=t.assigned_incident.incident_code if t.assigned_incident else None,
                    active_tasks_count=active_tasks,
                    created_at=t.created_at,
                    updated_at=t.updated_at,
                )
            )

        return results, total, total_pages

    def create_team(self, db: Session, payload: TeamCreate) -> TeamResponse:
        existing = db.query(ResponseTeam).filter(ResponseTeam.team_callsign == payload.team_callsign.strip()).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Team callsign '{payload.team_callsign}' already exists.",
            )

        shelter_uuid = None
        if payload.assigned_base_shelter_id:
            shelter_uuid = parse_uuid(payload.assigned_base_shelter_id, "Shelter ID")
            if not db.query(Shelter).filter(Shelter.id == shelter_uuid).first():
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assigned shelter not found.")

        incident_uuid = None
        if payload.assigned_incident_id:
            incident_uuid = parse_uuid(payload.assigned_incident_id, "Incident ID")
            if not db.query(Incident).filter(Incident.id == incident_uuid).first():
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assigned incident not found.")

        team = ResponseTeam(
            id=uuid.uuid4(),
            team_callsign=payload.team_callsign.strip(),
            unit_type=payload.unit_type.strip(),
            personnel_count=payload.personnel_count,
            commander_name=payload.commander_name.strip(),
            contact_channel=payload.contact_channel.strip(),
            current_status=payload.current_status,
            current_latitude=payload.current_latitude,
            current_longitude=payload.current_longitude,
            base_location=payload.base_location.strip(),
            assigned_base_shelter_id=shelter_uuid,
            assigned_incident_id=incident_uuid,
            created_at=utcnow(),
            updated_at=utcnow(),
        )
        db.add(team)
        db.commit()
        db.refresh(team)

        return TeamResponse(
            id=str(team.id),
            team_callsign=team.team_callsign,
            unit_type=team.unit_type,
            personnel_count=team.personnel_count,
            commander_name=team.commander_name,
            contact_channel=team.contact_channel,
            current_status=team.current_status,
            current_latitude=team.current_latitude,
            current_longitude=team.current_longitude,
            base_location=team.base_location,
            assigned_base_shelter_id=str(team.assigned_base_shelter_id) if team.assigned_base_shelter_id else None,
            assigned_incident_id=str(team.assigned_incident_id) if team.assigned_incident_id else None,
            active_tasks_count=0,
            created_at=team.created_at,
            updated_at=team.updated_at,
        )

    def get_team(self, db: Session, team_id: str) -> TeamResponse:
        t_uuid = parse_uuid(team_id, "Team ID")
        team = db.query(ResponseTeam).options(
            joinedload(ResponseTeam.tasks),
            joinedload(ResponseTeam.assigned_incident),
        ).filter(ResponseTeam.id == t_uuid).first()

        if not team:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Response team '{team_id}' not found.")

        active_tasks = sum(1 for task in team.tasks if task.status in ("pending", "in_progress"))
        return TeamResponse(
            id=str(team.id),
            team_callsign=team.team_callsign,
            unit_type=team.unit_type,
            personnel_count=team.personnel_count,
            commander_name=team.commander_name,
            contact_channel=team.contact_channel,
            current_status=team.current_status,
            current_latitude=team.current_latitude,
            current_longitude=team.current_longitude,
            base_location=team.base_location,
            assigned_base_shelter_id=str(team.assigned_base_shelter_id) if team.assigned_base_shelter_id else None,
            assigned_incident_id=str(team.assigned_incident_id) if team.assigned_incident_id else None,
            assigned_incident_title=team.assigned_incident.title if team.assigned_incident else None,
            assigned_incident_code=team.assigned_incident.incident_code if team.assigned_incident else None,
            active_tasks_count=active_tasks,
            created_at=team.created_at,
            updated_at=team.updated_at,
        )

    def update_team(self, db: Session, team_id: str, payload: TeamUpdatePatch) -> TeamResponse:
        t_uuid = parse_uuid(team_id, "Team ID")
        team = db.query(ResponseTeam).filter(ResponseTeam.id == t_uuid).first()
        if not team:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Response team '{team_id}' not found.")

        if payload.team_callsign and payload.team_callsign.strip() != team.team_callsign:
            duplicate = db.query(ResponseTeam).filter(
                ResponseTeam.team_callsign == payload.team_callsign.strip(),
                ResponseTeam.id != t_uuid,
            ).first()
            if duplicate:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Team callsign already in use.")
            team.team_callsign = payload.team_callsign.strip()

        if payload.unit_type is not None:
            team.unit_type = payload.unit_type.strip()
        if payload.personnel_count is not None:
            team.personnel_count = payload.personnel_count
        if payload.commander_name is not None:
            team.commander_name = payload.commander_name.strip()
        if payload.contact_channel is not None:
            team.contact_channel = payload.contact_channel.strip()
        if payload.base_location is not None:
            team.base_location = payload.base_location.strip()
        if payload.current_latitude is not None:
            team.current_latitude = payload.current_latitude
        if payload.current_longitude is not None:
            team.current_longitude = payload.current_longitude

        if payload.current_status is not None:
            team.current_status = payload.current_status

        if payload.assigned_base_shelter_id is not None:
            if payload.assigned_base_shelter_id == "":
                team.assigned_base_shelter_id = None
            else:
                sh_uuid = parse_uuid(payload.assigned_base_shelter_id, "Shelter ID")
                if not db.query(Shelter).filter(Shelter.id == sh_uuid).first():
                    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Shelter not found.")
                team.assigned_base_shelter_id = sh_uuid

        if payload.assigned_incident_id is not None:
            if payload.assigned_incident_id == "":
                team.assigned_incident_id = None
            else:
                inc_uuid = parse_uuid(payload.assigned_incident_id, "Incident ID")
                if not db.query(Incident).filter(Incident.id == inc_uuid).first():
                    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found.")
                team.assigned_incident_id = inc_uuid

        team.updated_at = utcnow()
        db.commit()
        db.refresh(team)
        return self.get_team(db, team_id)

    def delete_team(self, db: Session, team_id: str) -> dict:
        t_uuid = parse_uuid(team_id, "Team ID")
        team = db.query(ResponseTeam).options(joinedload(ResponseTeam.tasks)).filter(ResponseTeam.id == t_uuid).first()
        if not team:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Response team '{team_id}' not found.")

        active_tasks = [t for t in team.tasks if t.status in ("pending", "in_progress")]
        if active_tasks:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot delete team '{team.team_callsign}' while assigned to {len(active_tasks)} active task(s). Reassign or cancel tasks first.",
            )

        callsign = team.team_callsign
        db.delete(team)
        db.commit()
        return {"status": "success", "message": f"Response team '{callsign}' successfully deleted."}

    # ==========================================================================
    # Response Tasks
    # ==========================================================================

    def list_tasks(
        self,
        db: Session,
        page: int = 1,
        page_size: int = 20,
        incident_id: Optional[str] = None,
        assigned_team_id: Optional[str] = None,
        status_filter: Optional[str] = None,
        priority: Optional[str] = None,
        search: Optional[str] = None,
    ) -> Tuple[List[TaskResponse], int, int]:
        query = db.query(ResponseTask).options(
            joinedload(ResponseTask.incident),
            joinedload(ResponseTask.assigned_team),
        )

        if incident_id:
            inc_uuid = parse_uuid(incident_id, "Incident ID")
            query = query.filter(ResponseTask.incident_id == inc_uuid)

        if assigned_team_id:
            tm_uuid = parse_uuid(assigned_team_id, "Team ID")
            query = query.filter(ResponseTask.assigned_team_id == tm_uuid)

        if status_filter:
            query = query.filter(ResponseTask.status == status_filter.strip().lower())

        if priority:
            query = query.filter(ResponseTask.priority == priority.strip().lower())

        if search:
            s = f"%{search.strip()}%"
            query = query.filter(
                or_(
                    ResponseTask.title.ilike(s),
                    ResponseTask.description.ilike(s),
                )
            )

        total = query.count()
        total_pages = max(1, math.ceil(total / page_size))
        offset = (page - 1) * page_size
        tasks = query.order_by(desc(ResponseTask.created_at)).offset(offset).limit(page_size).all()

        results = []
        for t in tasks:
            results.append(
                TaskResponse(
                    id=str(t.id),
                    incident_id=str(t.incident_id),
                    incident_title=t.incident.title if t.incident else None,
                    incident_code=t.incident.incident_code if t.incident else None,
                    assigned_team_id=str(t.assigned_team_id) if t.assigned_team_id else None,
                    assigned_team_callsign=t.assigned_team.team_callsign if t.assigned_team else None,
                    title=t.title,
                    description=t.description,
                    priority=t.priority,
                    status=t.status,
                    target_latitude=t.target_latitude,
                    target_longitude=t.target_longitude,
                    due_at=t.due_at,
                    completed_at=t.completed_at,
                    created_at=t.created_at,
                    updated_at=t.updated_at,
                )
            )

        return results, total, total_pages

    def create_task(self, db: Session, payload: TaskCreate) -> TaskResponse:
        inc_uuid = parse_uuid(payload.incident_id, "Incident ID")
        incident = db.query(Incident).filter(Incident.id == inc_uuid).first()
        if not incident:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Referenced incident not found.")

        team_uuid = None
        if payload.assigned_team_id:
            team_uuid = parse_uuid(payload.assigned_team_id, "Team ID")
            team = db.query(ResponseTeam).filter(ResponseTeam.id == team_uuid).first()
            if not team:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Referenced response team not found.")
            if team.current_status in ("offline", "busy"):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Team '{team.team_callsign}' is currently {team.current_status} and unavailable for new assignments.",
                )
            # Update team status to assigned and link incident
            team.current_status = "assigned"
            if not team.assigned_incident_id:
                team.assigned_incident_id = incident.id
            team.updated_at = utcnow()

        task = ResponseTask(
            id=uuid.uuid4(),
            incident_id=inc_uuid,
            assigned_team_id=team_uuid,
            title=payload.title.strip(),
            description=payload.description.strip(),
            priority=payload.priority,
            status="in_progress" if team_uuid else "pending",
            target_latitude=payload.target_latitude or incident.latitude,
            target_longitude=payload.target_longitude or incident.longitude,
            due_at=payload.due_at,
            created_at=utcnow(),
            updated_at=utcnow(),
        )
        db.add(task)
        db.commit()
        db.refresh(task)

        return self.get_task(db, str(task.id))

    def get_task(self, db: Session, task_id: str) -> TaskResponse:
        tsk_uuid = parse_uuid(task_id, "Task ID")
        task = db.query(ResponseTask).options(
            joinedload(ResponseTask.incident),
            joinedload(ResponseTask.assigned_team),
        ).filter(ResponseTask.id == tsk_uuid).first()

        if not task:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Response task '{task_id}' not found.")

        return TaskResponse(
            id=str(task.id),
            incident_id=str(task.incident_id),
            incident_title=task.incident.title if task.incident else None,
            incident_code=task.incident.incident_code if task.incident else None,
            assigned_team_id=str(task.assigned_team_id) if task.assigned_team_id else None,
            assigned_team_callsign=task.assigned_team.team_callsign if task.assigned_team else None,
            title=task.title,
            description=task.description,
            priority=task.priority,
            status=task.status,
            target_latitude=task.target_latitude,
            target_longitude=task.target_longitude,
            due_at=task.due_at,
            completed_at=task.completed_at,
            created_at=task.created_at,
            updated_at=task.updated_at,
        )

    def update_task(self, db: Session, task_id: str, payload: TaskUpdatePatch) -> TaskResponse:
        tsk_uuid = parse_uuid(task_id, "Task ID")
        task = db.query(ResponseTask).filter(ResponseTask.id == tsk_uuid).first()
        if not task:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Response task '{task_id}' not found.")

        old_team_id = task.assigned_team_id

        if payload.title is not None:
            task.title = payload.title.strip()
        if payload.description is not None:
            task.description = payload.description.strip()
        if payload.priority is not None:
            task.priority = payload.priority
        if payload.target_latitude is not None:
            task.target_latitude = payload.target_latitude
        if payload.target_longitude is not None:
            task.target_longitude = payload.target_longitude
        if payload.due_at is not None:
            task.due_at = payload.due_at

        # Team reassignment handling
        if payload.assigned_team_id is not None:
            if payload.assigned_team_id == "":
                task.assigned_team_id = None
                if task.status == "in_progress":
                    task.status = "pending"
            else:
                new_team_uuid = parse_uuid(payload.assigned_team_id, "Team ID")
                new_team = db.query(ResponseTeam).filter(ResponseTeam.id == new_team_uuid).first()
                if not new_team:
                    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Response team not found.")
                if new_team_uuid != old_team_id and new_team.current_status in ("offline", "busy"):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Team '{new_team.team_callsign}' is currently {new_team.current_status} and cannot be assigned.",
                    )
                task.assigned_team_id = new_team_uuid
                new_team.current_status = "assigned"
                if not new_team.assigned_incident_id:
                    new_team.assigned_incident_id = task.incident_id
                new_team.updated_at = utcnow()

        # Status transition handling
        if payload.status is not None:
            task.status = payload.status
            if payload.status == "completed":
                task.completed_at = utcnow()
            elif payload.status in ("pending", "in_progress"):
                task.completed_at = None

        task.updated_at = utcnow()
        db.commit()

        # Refresh availability for old team if relieved
        if old_team_id and (old_team_id != task.assigned_team_id or task.status in ("completed", "cancelled")):
            self._recalculate_team_availability(db, old_team_id)

        return self.get_task(db, task_id)

    def complete_task(self, db: Session, task_id: str) -> TaskResponse:
        return self.update_task(db, task_id, TaskUpdatePatch(status="completed"))

    def _recalculate_team_availability(self, db: Session, team_id: uuid.UUID):
        remaining_active = db.query(ResponseTask).filter(
            ResponseTask.assigned_team_id == team_id,
            ResponseTask.status.in_(["pending", "in_progress"]),
        ).count()

        team = db.query(ResponseTeam).filter(ResponseTeam.id == team_id).first()
        if team and remaining_active == 0 and team.current_status not in ("offline", "busy"):
            team.current_status = "available"
            team.assigned_incident_id = None
            team.updated_at = utcnow()
            db.commit()

    # ==========================================================================
    # Shelters
    # ==========================================================================

    def list_shelters(
        self,
        db: Session,
        page: int = 1,
        page_size: int = 20,
        status_filter: Optional[str] = None,
        shelter_type: Optional[str] = None,
        available_only: bool = False,
        search: Optional[str] = None,
    ) -> Tuple[List[ShelterResponse], int, int]:
        query = db.query(Shelter)

        if status_filter:
            query = query.filter(Shelter.status == status_filter.strip().lower())

        if shelter_type:
            query = query.filter(Shelter.shelter_type.ilike(f"%{shelter_type.strip()}%"))

        if available_only:
            query = query.filter(
                Shelter.status == "open",
                Shelter.current_occupancy < Shelter.capacity,
            )

        if search:
            s = f"%{search.strip()}%"
            query = query.filter(
                or_(
                    Shelter.name.ilike(s),
                    Shelter.address.ilike(s),
                    Shelter.contact_person.ilike(s),
                )
            )

        total = query.count()
        total_pages = max(1, math.ceil(total / page_size))
        offset = (page - 1) * page_size
        shelters = query.order_by(asc(Shelter.name)).offset(offset).limit(page_size).all()

        results = []
        for sh in shelters:
            rem = max(0, sh.capacity - sh.current_occupancy)
            pct = round((sh.current_occupancy / sh.capacity * 100), 1) if sh.capacity > 0 else 0.0
            results.append(
                ShelterResponse(
                    id=str(sh.id),
                    name=sh.name,
                    shelter_type=sh.shelter_type,
                    capacity=sh.capacity,
                    current_occupancy=sh.current_occupancy,
                    remaining_capacity=rem,
                    occupancy_pct=pct,
                    latitude=sh.latitude,
                    longitude=sh.longitude,
                    address=sh.address,
                    contact_person=sh.contact_person,
                    contact_phone=sh.contact_phone,
                    supplies_status=sh.supplies_status,
                    power_backup=sh.power_backup,
                    medical_station=sh.medical_station,
                    status=sh.status,
                    created_at=sh.created_at,
                    updated_at=sh.updated_at,
                )
            )

        return results, total, total_pages

    def create_shelter(self, db: Session, payload: ShelterCreate) -> ShelterResponse:
        sh_status = payload.status
        if payload.current_occupancy >= payload.capacity:
            sh_status = "full"

        shelter = Shelter(
            id=uuid.uuid4(),
            name=payload.name.strip(),
            shelter_type=payload.shelter_type.strip(),
            capacity=payload.capacity,
            current_occupancy=payload.current_occupancy,
            latitude=payload.latitude,
            longitude=payload.longitude,
            address=payload.address.strip(),
            contact_person=payload.contact_person.strip(),
            contact_phone=payload.contact_phone.strip(),
            supplies_status=payload.supplies_status,
            power_backup=payload.power_backup,
            medical_station=payload.medical_station,
            status=sh_status,
            created_at=utcnow(),
            updated_at=utcnow(),
        )
        db.add(shelter)
        db.commit()
        db.refresh(shelter)

        return self.get_shelter(db, str(shelter.id))

    def get_shelter(self, db: Session, shelter_id: str) -> ShelterResponse:
        sh_uuid = parse_uuid(shelter_id, "Shelter ID")
        sh = db.query(Shelter).filter(Shelter.id == sh_uuid).first()
        if not sh:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Shelter '{shelter_id}' not found.")

        rem = max(0, sh.capacity - sh.current_occupancy)
        pct = round((sh.current_occupancy / sh.capacity * 100), 1) if sh.capacity > 0 else 0.0
        return ShelterResponse(
            id=str(sh.id),
            name=sh.name,
            shelter_type=sh.shelter_type,
            capacity=sh.capacity,
            current_occupancy=sh.current_occupancy,
            remaining_capacity=rem,
            occupancy_pct=pct,
            latitude=sh.latitude,
            longitude=sh.longitude,
            address=sh.address,
            contact_person=sh.contact_person,
            contact_phone=sh.contact_phone,
            supplies_status=sh.supplies_status,
            power_backup=sh.power_backup,
            medical_station=sh.medical_station,
            status=sh.status,
            created_at=sh.created_at,
            updated_at=sh.updated_at,
        )

    def update_shelter(self, db: Session, shelter_id: str, payload: ShelterUpdatePatch) -> ShelterResponse:
        sh_uuid = parse_uuid(shelter_id, "Shelter ID")
        sh = db.query(Shelter).filter(Shelter.id == sh_uuid).first()
        if not sh:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Shelter '{shelter_id}' not found.")

        if payload.name is not None:
            sh.name = payload.name.strip()
        if payload.shelter_type is not None:
            sh.shelter_type = payload.shelter_type.strip()
        if payload.address is not None:
            sh.address = payload.address.strip()
        if payload.contact_person is not None:
            sh.contact_person = payload.contact_person.strip()
        if payload.contact_phone is not None:
            sh.contact_phone = payload.contact_phone.strip()
        if payload.latitude is not None:
            sh.latitude = payload.latitude
        if payload.longitude is not None:
            sh.longitude = payload.longitude
        if payload.supplies_status is not None:
            sh.supplies_status = payload.supplies_status
        if payload.power_backup is not None:
            sh.power_backup = payload.power_backup
        if payload.medical_station is not None:
            sh.medical_station = payload.medical_station

        new_capacity = payload.capacity if payload.capacity is not None else sh.capacity
        new_occupancy = payload.current_occupancy if payload.current_occupancy is not None else sh.current_occupancy

        if new_occupancy > new_capacity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Occupancy ({new_occupancy}) cannot exceed capacity ({new_capacity}).",
            )
        if new_occupancy < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Occupancy cannot be negative.",
            )

        sh.capacity = new_capacity
        sh.current_occupancy = new_occupancy

        if payload.status is not None:
            sh.status = payload.status
        else:
            if sh.current_occupancy >= sh.capacity:
                sh.status = "full"
            elif sh.status == "full" and sh.current_occupancy < sh.capacity:
                sh.status = "open"

        sh.updated_at = utcnow()
        db.commit()
        db.refresh(sh)
        return self.get_shelter(db, shelter_id)

    def admit_occupants(self, db: Session, shelter_id: str, count: int, notes: Optional[str] = None) -> ShelterResponse:
        sh_uuid = parse_uuid(shelter_id, "Shelter ID")
        sh = db.query(Shelter).filter(Shelter.id == sh_uuid).with_for_update().first()
        if not sh:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Shelter '{shelter_id}' not found.")

        if sh.status == "closed":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot admit occupants to a closed shelter facility.")

        available_space = sh.capacity - sh.current_occupancy
        if count > available_space:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot admit {count} persons. Only {available_space} spaces remaining (capacity: {sh.capacity}, current: {sh.current_occupancy}).",
            )

        sh.current_occupancy += count
        if sh.current_occupancy >= sh.capacity:
            sh.status = "full"

        sh.updated_at = utcnow()
        db.commit()
        db.refresh(sh)
        return self.get_shelter(db, shelter_id)

    def discharge_occupants(self, db: Session, shelter_id: str, count: int, notes: Optional[str] = None) -> ShelterResponse:
        sh_uuid = parse_uuid(shelter_id, "Shelter ID")
        sh = db.query(Shelter).filter(Shelter.id == sh_uuid).with_for_update().first()
        if not sh:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Shelter '{shelter_id}' not found.")

        if count > sh.current_occupancy:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Discharge count ({count}) exceeds current occupancy ({sh.current_occupancy}).",
            )

        sh.current_occupancy -= count
        if sh.status == "full" and sh.current_occupancy < sh.capacity:
            sh.status = "open"

        sh.updated_at = utcnow()
        db.commit()
        db.refresh(sh)
        return self.get_shelter(db, shelter_id)

    def delete_shelter(self, db: Session, shelter_id: str) -> dict:
        sh_uuid = parse_uuid(shelter_id, "Shelter ID")
        sh = db.query(Shelter).filter(Shelter.id == sh_uuid).first()
        if not sh:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Shelter '{shelter_id}' not found.")

        if sh.current_occupancy > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot delete shelter '{sh.name}' with {sh.current_occupancy} active occupants. Relocate occupants first.",
            )

        name = sh.name
        db.delete(sh)
        db.commit()
        return {"status": "success", "message": f"Shelter facility '{name}' deleted."}

    # ==========================================================================
    # Emergency Resources
    # ==========================================================================

    def list_resources(
        self,
        db: Session,
        page: int = 1,
        page_size: int = 20,
        category: Optional[str] = None,
        shelter_id: Optional[str] = None,
        low_stock_only: bool = False,
        search: Optional[str] = None,
    ) -> Tuple[List[ResourceResponse], int, int]:
        query = db.query(Resource).options(
            joinedload(Resource.shelter),
            joinedload(Resource.movements),
        )

        if category:
            query = query.filter(Resource.category.ilike(f"%{category.strip()}%"))

        if shelter_id:
            sh_uuid = parse_uuid(shelter_id, "Shelter ID")
            query = query.filter(Resource.shelter_id == sh_uuid)

        if low_stock_only:
            query = query.filter(Resource.quantity_available <= 0.25 * Resource.quantity_total)

        if search:
            s = f"%{search.strip()}%"
            query = query.filter(
                or_(
                    Resource.name.ilike(s),
                    Resource.resource_code.ilike(s),
                    Resource.storage_location.ilike(s),
                )
            )

        total = query.count()
        total_pages = max(1, math.ceil(total / page_size))
        offset = (page - 1) * page_size
        resources = query.order_by(asc(Resource.name)).offset(offset).limit(page_size).all()

        results = []
        for r in resources:
            allocated = max(0.0, r.quantity_total - r.quantity_available)
            recent_movs = [
                ResourceMovementResponse(
                    id=str(m.id),
                    resource_id=str(m.resource_id),
                    source_location=m.source_location,
                    destination_location=m.destination_location,
                    quantity=m.quantity,
                    status=m.status,
                    transport_mode=m.transport_mode,
                    dispatched_at=m.dispatched_at,
                    delivered_at=m.delivered_at,
                    incident_id=str(m.incident_id) if m.incident_id else None,
                    task_id=str(m.task_id) if m.task_id else None,
                    team_id=str(m.team_id) if m.team_id else None,
                    shelter_id=str(m.shelter_id) if m.shelter_id else None,
                    notes=m.notes,
                    created_at=m.created_at,
                )
                for m in sorted(r.movements, key=lambda x: x.created_at, reverse=True)[:5]
            ]

            results.append(
                ResourceResponse(
                    id=str(r.id),
                    resource_code=r.resource_code,
                    name=r.name,
                    category=r.category,
                    quantity_total=r.quantity_total,
                    quantity_available=r.quantity_available,
                    allocated_quantity=round(allocated, 2),
                    unit=r.unit,
                    shelter_id=str(r.shelter_id) if r.shelter_id else None,
                    shelter_name=r.shelter.name if r.shelter else None,
                    storage_location=r.storage_location,
                    status=r.status,
                    created_at=r.created_at,
                    updated_at=r.updated_at,
                    recent_movements=recent_movs,
                )
            )

        return results, total, total_pages

    def create_resource(self, db: Session, payload: ResourceCreate) -> ResourceResponse:
        existing = db.query(Resource).filter(Resource.resource_code == payload.resource_code.strip()).first()
        if existing:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Resource code '{payload.resource_code}' already exists.")

        sh_uuid = None
        if payload.shelter_id:
            sh_uuid = parse_uuid(payload.shelter_id, "Shelter ID")
            if not db.query(Shelter).filter(Shelter.id == sh_uuid).first():
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assigned shelter not found.")

        qty_avail = payload.quantity_available if payload.quantity_available is not None else payload.quantity_total
        res = Resource(
            id=uuid.uuid4(),
            resource_code=payload.resource_code.strip(),
            name=payload.name.strip(),
            category=payload.category.strip(),
            quantity_total=payload.quantity_total,
            quantity_available=qty_avail,
            unit=payload.unit.strip(),
            shelter_id=sh_uuid,
            storage_location=payload.storage_location.strip() if payload.storage_location else "Central Logistics Warehouse",
            status=payload.status,
            created_at=utcnow(),
            updated_at=utcnow(),
        )
        db.add(res)
        db.commit()
        db.refresh(res)
        return self.get_resource(db, str(res.id))

    def get_resource(self, db: Session, resource_id: str) -> ResourceResponse:
        res_uuid = parse_uuid(resource_id, "Resource ID")
        r = db.query(Resource).options(
            joinedload(Resource.shelter),
            joinedload(Resource.movements),
        ).filter(Resource.id == res_uuid).first()

        if not r:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Resource '{resource_id}' not found.")

        allocated = max(0.0, r.quantity_total - r.quantity_available)
        recent_movs = [
            ResourceMovementResponse(
                id=str(m.id),
                resource_id=str(m.resource_id),
                source_location=m.source_location,
                destination_location=m.destination_location,
                quantity=m.quantity,
                status=m.status,
                transport_mode=m.transport_mode,
                dispatched_at=m.dispatched_at,
                delivered_at=m.delivered_at,
                incident_id=str(m.incident_id) if m.incident_id else None,
                task_id=str(m.task_id) if m.task_id else None,
                team_id=str(m.team_id) if m.team_id else None,
                shelter_id=str(m.shelter_id) if m.shelter_id else None,
                notes=m.notes,
                created_at=m.created_at,
            )
            for m in sorted(r.movements, key=lambda x: x.created_at, reverse=True)[:10]
        ]

        return ResourceResponse(
            id=str(r.id),
            resource_code=r.resource_code,
            name=r.name,
            category=r.category,
            quantity_total=r.quantity_total,
            quantity_available=r.quantity_available,
            allocated_quantity=round(allocated, 2),
            unit=r.unit,
            shelter_id=str(r.shelter_id) if r.shelter_id else None,
            shelter_name=r.shelter.name if r.shelter else None,
            storage_location=r.storage_location,
            status=r.status,
            created_at=r.created_at,
            updated_at=r.updated_at,
            recent_movements=recent_movs,
        )

    def update_resource(self, db: Session, resource_id: str, payload: ResourceUpdatePatch) -> ResourceResponse:
        res_uuid = parse_uuid(resource_id, "Resource ID")
        r = db.query(Resource).filter(Resource.id == res_uuid).first()
        if not r:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Resource '{resource_id}' not found.")

        if payload.resource_code and payload.resource_code.strip() != r.resource_code:
            dup = db.query(Resource).filter(Resource.resource_code == payload.resource_code.strip(), Resource.id != res_uuid).first()
            if dup:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Resource code already exists.")
            r.resource_code = payload.resource_code.strip()

        if payload.name is not None:
            r.name = payload.name.strip()
        if payload.category is not None:
            r.category = payload.category.strip()
        if payload.unit is not None:
            r.unit = payload.unit.strip()
        if payload.storage_location is not None:
            r.storage_location = payload.storage_location.strip()
        if payload.status is not None:
            r.status = payload.status

        new_total = payload.quantity_total if payload.quantity_total is not None else r.quantity_total
        new_avail = payload.quantity_available if payload.quantity_available is not None else r.quantity_available

        if new_avail > new_total:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Available stock cannot exceed total stock.")
        if new_avail < 0 or new_total < 0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Stock quantities cannot be negative.")

        r.quantity_total = new_total
        r.quantity_available = new_avail

        if payload.shelter_id is not None:
            if payload.shelter_id == "":
                r.shelter_id = None
            else:
                sh_uuid = parse_uuid(payload.shelter_id, "Shelter ID")
                if not db.query(Shelter).filter(Shelter.id == sh_uuid).first():
                    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Shelter not found.")
                r.shelter_id = sh_uuid

        r.updated_at = utcnow()
        db.commit()
        db.refresh(r)
        return self.get_resource(db, resource_id)

    def allocate_resource(self, db: Session, resource_id: str, payload: ResourceAllocateRequest) -> ResourceResponse:
        res_uuid = parse_uuid(resource_id, "Resource ID")
        r = db.query(Resource).filter(Resource.id == res_uuid).with_for_update().first()
        if not r:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Resource '{resource_id}' not found.")

        if payload.quantity > r.quantity_available:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Requested allocation ({payload.quantity} {r.unit}) exceeds available stock ({r.quantity_available} {r.unit}).",
            )

        inc_uuid = parse_uuid(payload.incident_id, "Incident ID") if payload.incident_id else None
        task_uuid = parse_uuid(payload.task_id, "Task ID") if payload.task_id else None
        team_uuid = parse_uuid(payload.team_id, "Team ID") if payload.team_id else None
        shelter_uuid = parse_uuid(payload.shelter_id, "Shelter ID") if payload.shelter_id else None

        # Verify foreign keys if provided
        if inc_uuid and not db.query(Incident).filter(Incident.id == inc_uuid).first():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Linked incident not found.")
        if task_uuid and not db.query(ResponseTask).filter(ResponseTask.id == task_uuid).first():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Linked task not found.")
        if team_uuid and not db.query(ResponseTeam).filter(ResponseTeam.id == team_uuid).first():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Linked team not found.")
        if shelter_uuid and not db.query(Shelter).filter(Shelter.id == shelter_uuid).first():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Linked shelter not found.")

        # Deduct stock
        r.quantity_available -= payload.quantity
        if r.quantity_available == 0:
            r.status = "depleted"
        elif r.quantity_available <= 0.25 * r.quantity_total:
            r.status = "low_stock"
        else:
            r.status = "in_stock"
        r.updated_at = utcnow()

        # Log movement audit
        source = r.shelter.name if r.shelter else (r.storage_location or "Central Logistics Warehouse")
        movement = ResourceMovement(
            id=uuid.uuid4(),
            resource_id=r.id,
            source_location=source,
            destination_location=payload.destination_location.strip(),
            quantity=payload.quantity,
            status="dispatched",
            transport_mode=payload.transport_mode or "Ground Logistics",
            incident_id=inc_uuid,
            task_id=task_uuid,
            team_id=team_uuid,
            shelter_id=shelter_uuid,
            notes=payload.notes,
            dispatched_at=utcnow(),
            created_at=utcnow(),
        )
        db.add(movement)
        db.commit()
        db.refresh(r)
        return self.get_resource(db, resource_id)

    def return_resource(self, db: Session, resource_id: str, payload: ResourceReturnRequest) -> ResourceResponse:
        res_uuid = parse_uuid(resource_id, "Resource ID")
        r = db.query(Resource).filter(Resource.id == res_uuid).with_for_update().first()
        if not r:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Resource '{resource_id}' not found.")

        if r.quantity_available + payload.quantity > r.quantity_total:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Returned quantity ({payload.quantity} {r.unit}) would exceed total inventory limit ({r.quantity_total} {r.unit}).",
            )

        r.quantity_available += payload.quantity
        if r.quantity_available > 0.25 * r.quantity_total:
            r.status = "in_stock"
        elif r.quantity_available > 0:
            r.status = "low_stock"
        r.updated_at = utcnow()

        dest = r.shelter.name if r.shelter else (r.storage_location or "Central Logistics Warehouse")
        movement = ResourceMovement(
            id=uuid.uuid4(),
            resource_id=r.id,
            source_location=payload.source_location.strip(),
            destination_location=dest,
            quantity=payload.quantity,
            status="returned",
            transport_mode="Ground Logistics Return",
            notes=payload.notes,
            dispatched_at=utcnow(),
            delivered_at=utcnow(),
            created_at=utcnow(),
        )
        db.add(movement)
        db.commit()
        db.refresh(r)
        return self.get_resource(db, resource_id)

    def delete_resource(self, db: Session, resource_id: str) -> dict:
        res_uuid = parse_uuid(resource_id, "Resource ID")
        r = db.query(Resource).options(joinedload(Resource.movements)).filter(Resource.id == res_uuid).first()
        if not r:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Resource '{resource_id}' not found.")

        if r.quantity_available < r.quantity_total:
            allocated = r.quantity_total - r.quantity_available
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot delete resource '{r.name}' with {allocated} {r.unit} currently deployed/allocated. Return stock first.",
            )

        name = r.name
        # Delete associated movements
        for m in r.movements:
            db.delete(m)
        db.delete(r)
        db.commit()
        return {"status": "success", "message": f"Resource stockpile '{name}' deleted."}


coordination_service = CoordinationService()

"""
AgentCraft Intelligent Alerts Service
Implements rule-driven, traceable disaster alert generation, deduplication with cooldowns,
lifecycle management (active -> acknowledged -> resolved), and integration with incidents.
Conforms to AGENTCRAFT 2026 directives and CAP alerting principles.
"""

import hashlib
import time
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from backend.rakshagrid.models import (
    Alert,
    Incident,
    RiskAssessment,
    Shelter,
    Resource,
)
from backend.services.risk_engine import disaster_risk_engine
from backend.services.external_data_service import disaster_data_service


def utcnow():
    return datetime.now(timezone.utc)


class AlertThresholds:
    """Configurable rule thresholds for automated disaster alert evaluation."""
    RISK_CRITICAL = 75.0
    RISK_HIGH = 50.0
    PRECIPITATION_HEAVY_MM = 35.0
    SHELTER_HIGH_OCCUPANCY_PCT = 85.0
    RESOURCE_LOW_STOCK_PCT = 25.0
    COOLDOWN_SECONDS = 900  # 15 minutes suppression for unchanged condition


class AlertService:
    """
    Intelligent Alert Management & Rule Evaluation Engine.
    Evaluates incidents, shelters, and resources; suppresses duplicates within cooldown;
    and manages operational lifecycle transitions.
    """

    def __init__(self, thresholds: Optional[AlertThresholds] = None):
        self.thresholds = thresholds or AlertThresholds()

    def _generate_alert_code(self, prefix: str = "ALT") -> str:
        """Generates a human-readable, unique alert code."""
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        suffix = hashlib.sha256(str(time.time()).encode()).hexdigest()[:4].upper()
        return f"{prefix}-{timestamp}-{suffix}"

    def _generate_dedup_key(self, incident_id: Optional[str], rule_name: str, scope: str) -> str:
        """Computes deterministic deduplication fingerprint."""
        raw = f"{incident_id or 'global'}:{rule_name}:{scope}"
        return hashlib.sha256(raw.encode()).hexdigest()[:32]

    def is_suppressed(self, db: Session, dedup_key: str) -> bool:
        """
        Checks whether an active or recent alert with the identical fingerprint exists
        within the configured cooldown window.
        """
        cooldown_cutoff = utcnow() - timedelta(seconds=self.thresholds.COOLDOWN_SECONDS)
        existing = (
            db.query(Alert)
            .filter(
                Alert.dedup_key == dedup_key,
                Alert.broadcast_status.in_(["active", "acknowledged"]),
                Alert.issued_at >= cooldown_cutoff,
            )
            .first()
        )
        return existing is not None

    def evaluate_incident_alerts(self, db: Session, incident: Incident) -> List[Alert]:
        """
        Evaluates risk and telemetry thresholds for a specific incident,
        generating traceable alerts if thresholds are breached and not suppressed.
        """
        generated_alerts: List[Alert] = []

        # 1. Assess Risk Score
        assessment = disaster_risk_engine.assess_incident(incident, db=db, persist=False)
        score = assessment["calculated_risk_score"]

        # Critical Hazard Alert Rule
        if score >= self.thresholds.RISK_CRITICAL:
            dedup = self._generate_dedup_key(str(incident.id), "critical_hazard_risk", "critical")
            if not self.is_suppressed(db, dedup):
                alert = Alert(
                    incident_id=incident.id,
                    alert_code=self._generate_alert_code("ALT-CRIT"),
                    headline=f"CRITICAL HAZARD: {incident.title} (Risk {score}/100)",
                    urgency="immediate",
                    severity="critical",
                    certainty="observed" if incident.verification_status == "verified" else "likely",
                    target_region=incident.location_description or "Incident Sector",
                    evacuation_recommended=score >= 80.0,
                    instructions="Activate immediate emergency containment. Prepare evacuation routes and alert nearest shelters.",
                    broadcast_status="active",
                    trigger_reason=f"Calculated risk score reached {score}/100 (Threshold: {self.thresholds.RISK_CRITICAL}).",
                    source_type="risk_engine",
                    dedup_key=dedup,
                    issued_at=utcnow(),
                )
                db.add(alert)
                generated_alerts.append(alert)

        # High Hazard Alert Rule
        elif score >= self.thresholds.RISK_HIGH:
            dedup = self._generate_dedup_key(str(incident.id), "high_hazard_risk", "high")
            if not self.is_suppressed(db, dedup):
                alert = Alert(
                    incident_id=incident.id,
                    alert_code=self._generate_alert_code("ALT-HIGH"),
                    headline=f"ELEVATED HAZARD: {incident.title} (Risk {score}/100)",
                    urgency="expected",
                    severity="high",
                    certainty="likely",
                    target_region=incident.location_description or "Incident Sector",
                    evacuation_recommended=False,
                    instructions="Stage local response units and review relief stockpile availability.",
                    broadcast_status="active",
                    trigger_reason=f"Calculated risk score reached {score}/100 (Threshold: {self.thresholds.RISK_HIGH}).",
                    source_type="risk_engine",
                    dedup_key=dedup,
                    issued_at=utcnow(),
                )
                db.add(alert)
                generated_alerts.append(alert)

        # 2. Check Severe Rainfall Telemetry
        if incident.latitude is not None and incident.longitude is not None:
            weather = disaster_data_service.get_weather(incident.latitude, incident.longitude)
            precip = weather.get("precipitation_mm") or 0.0
            if precip >= self.thresholds.PRECIPITATION_HEAVY_MM:
                dedup = self._generate_dedup_key(str(incident.id), "heavy_precipitation_surge", f"precip_{int(precip)}")
                if not self.is_suppressed(db, dedup):
                    alert = Alert(
                        incident_id=incident.id,
                        alert_code=self._generate_alert_code("ALT-MET"),
                        headline=f"HEAVY PRECIPITATION ADVISORY: {precip}mm recorded at {incident.location_description or incident.title}",
                        urgency="immediate",
                        severity="high",
                        certainty="observed" if weather.get("status") == "live" else "likely",
                        target_region=incident.location_description or "Local Watershed",
                        evacuation_recommended=False,
                        instructions="Monitor culverts, road underpasses, and river embankment levels for flash flooding.",
                        broadcast_status="active",
                        trigger_reason=f"Live telemetry recorded {precip}mm precipitation (Threshold: {self.thresholds.PRECIPITATION_HEAVY_MM}mm).",
                        source_type="external_telemetry",
                        dedup_key=dedup,
                        issued_at=utcnow(),
                    )
                    db.add(alert)
                    generated_alerts.append(alert)

        if generated_alerts:
            db.commit()

        return generated_alerts

    def evaluate_system_alerts(self, db: Session) -> Dict[str, Any]:
        """
        Runs comprehensive alert sweep across all active incidents, shelter capacities,
        and resource stockpiles.
        """
        active_incidents = db.query(Incident).filter(Incident.status.notin_(["resolved", "closed"])).all()
        created_count = 0
        suppressed_count = 0
        all_new_alerts = []

        # 1. Incidents evaluation
        for inc in active_incidents:
            new_alts = self.evaluate_incident_alerts(db, inc)
            created_count += len(new_alts)
            all_new_alerts.extend(new_alts)

        # 2. Shelters capacity evaluation
        open_shelters = db.query(Shelter).filter(Shelter.status == "open").all()
        for sh in open_shelters:
            occ_pct = (sh.current_occupancy / max(sh.capacity, 1)) * 100.0
            if occ_pct >= self.thresholds.SHELTER_HIGH_OCCUPANCY_PCT:
                dedup = self._generate_dedup_key(None, "shelter_capacity_surge", str(sh.id))
                if not self.is_suppressed(db, dedup):
                    alert = Alert(
                        incident_id=None,
                        alert_code=self._generate_alert_code("ALT-SHELTER"),
                        headline=f"SHELTER CAPACITY SURGE: {sh.name} at {round(occ_pct, 1)}% Capacity",
                        urgency="expected",
                        severity="high" if occ_pct < 100.0 else "critical",
                        certainty="observed",
                        target_region=sh.address,
                        evacuation_recommended=False,
                        instructions=f"Divert incoming displaced families to secondary shelters. Remaining capacity: {sh.remaining_capacity}.",
                        broadcast_status="active",
                        trigger_reason=f"Shelter occupancy reached {round(occ_pct, 1)}% (Threshold: {self.thresholds.SHELTER_HIGH_OCCUPANCY_PCT}%).",
                        source_type="shelter_monitoring",
                        dedup_key=dedup,
                        issued_at=utcnow(),
                    )
                    db.add(alert)
                    db.commit()
                    created_count += 1
                    all_new_alerts.append(alert)
                else:
                    suppressed_count += 1

        # 3. Resource stockpile shortages
        critical_resources = db.query(Resource).all()
        for res in critical_resources:
            pct = (res.quantity_available / max(res.quantity_total, 1.0)) * 100.0
            if pct <= self.thresholds.RESOURCE_LOW_STOCK_PCT:
                dedup = self._generate_dedup_key(None, "resource_shortage", str(res.id))
                if not self.is_suppressed(db, dedup):
                    alert = Alert(
                        incident_id=None,
                        alert_code=self._generate_alert_code("ALT-STOCK"),
                        headline=f"CRITICAL RELIEF SHORTAGE: {res.name} at {round(pct, 1)}% Availability",
                        urgency="expected",
                        severity="medium" if pct > 10.0 else "high",
                        certainty="observed",
                        target_region=res.storage_location or "Central Logistics",
                        evacuation_recommended=False,
                        instructions=f"Expedite resupply requisition for {res.name}. Only {res.quantity_available} {res.unit} available.",
                        broadcast_status="active",
                        trigger_reason=f"Stock availability fell to {round(pct, 1)}% (Threshold: {self.thresholds.RESOURCE_LOW_STOCK_PCT}%).",
                        source_type="resource_inventory",
                        dedup_key=dedup,
                        issued_at=utcnow(),
                    )
                    db.add(alert)
                    db.commit()
                    created_count += 1
                    all_new_alerts.append(alert)
                else:
                    suppressed_count += 1

        return {
            "eval_timestamp": utcnow().isoformat(),
            "incidents_evaluated": len(active_incidents),
            "shelters_evaluated": len(open_shelters),
            "resources_evaluated": len(critical_resources),
            "alerts_created": created_count,
            "alerts_suppressed_by_cooldown": suppressed_count,
            "created_alert_codes": [a.alert_code for a in all_new_alerts],
        }

    def list_alerts(
        self,
        db: Session,
        status_filter: Optional[str] = None,
        severity: Optional[str] = None,
        incident_id: Optional[str] = None,
        limit: int = 50,
    ) -> List[Alert]:
        """Queries alerts with filters, ordered by issued_at desc."""
        query = db.query(Alert)
        if status_filter and status_filter.lower() != "all":
            query = query.filter(Alert.broadcast_status == status_filter.lower())
        if severity and severity.lower() != "all":
            query = query.filter(Alert.severity == severity.lower())
        if incident_id:
            try:
                inc_uuid = UUID(str(incident_id))
                query = query.filter(Alert.incident_id == inc_uuid)
            except ValueError:
                pass

        return query.order_by(Alert.issued_at.desc()).limit(limit).all()

    def acknowledge_alert(self, db: Session, alert_id: str, operator_name: str) -> Alert:
        """Transitions alert to acknowledged state with actor timestamp."""
        try:
            aid = UUID(str(alert_id))
            alert = db.query(Alert).filter(Alert.id == aid).first()
        except ValueError:
            alert = db.query(Alert).filter(Alert.alert_code == str(alert_id)).first()

        if not alert:
            raise ValueError(f"Alert '{alert_id}' not found.")

        alert.broadcast_status = "acknowledged"
        alert.acknowledged_at = utcnow()
        alert.acknowledged_by = operator_name
        db.commit()
        db.refresh(alert)
        return alert

    def resolve_alert(self, db: Session, alert_id: str, operator_name: str, resolution_notes: str = "") -> Alert:
        """Resolves an alert with resolution timestamp and notes."""
        try:
            aid = UUID(str(alert_id))
            alert = db.query(Alert).filter(Alert.id == aid).first()
        except ValueError:
            alert = db.query(Alert).filter(Alert.alert_code == str(alert_id)).first()

        if not alert:
            raise ValueError(f"Alert '{alert_id}' not found.")

        alert.broadcast_status = "resolved"
        alert.resolved_at = utcnow()
        alert.resolved_by = operator_name
        if resolution_notes:
            alert.instructions += f" [RESOLVED by {operator_name}: {resolution_notes}]"
        db.commit()
        db.refresh(alert)
        return alert


# Singleton alert service
alert_service = AlertService()

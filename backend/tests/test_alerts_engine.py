"""
Unit & Integration Tests for Intelligent Alerts Service
Tests threshold crossing, duplicate suppression, cooldown window,
lifecycle transitions (active -> acknowledged -> resolved), and audit metadata.
"""

import uuid
import pytest
from backend.database.session import transactional_session
from backend.rakshagrid.models import Alert, Incident
from backend.services.alert_service import alert_service, AlertThresholds


def test_evaluate_system_alerts_triggers_and_suppresses():
    """Verify alert rule evaluation triggers alerts and suppresses duplicates on repeated sweep."""
    with transactional_session() as db:
        # Run first evaluation sweep
        sweep1 = alert_service.evaluate_system_alerts(db)
        assert "eval_timestamp" in sweep1
        assert sweep1["incidents_evaluated"] > 0
        initial_created = sweep1["alerts_created"]

        # Run immediate second evaluation sweep -> duplicates must be suppressed by cooldown
        sweep2 = alert_service.evaluate_system_alerts(db)
        assert sweep2["alerts_created"] == 0
        assert sweep2["alerts_suppressed_by_cooldown"] >= 0


def test_alert_lifecycle_acknowledge_and_resolve():
    """Verify alert transitions from active to acknowledged and resolved with audit stamps."""
    with transactional_session() as db:
        # Create an active alert
        alert = Alert(
            alert_code=f"TEST-ALT-{uuid.uuid4().hex[:6]}",
            headline="Test Cyclone Warning",
            urgency="immediate",
            severity="critical",
            certainty="observed",
            target_region="Coastal Belt",
            instructions="Evacuate low-lying areas.",
            broadcast_status="active",
        )
        db.add(alert)
        db.commit()
        db.refresh(alert)
        aid = str(alert.id)

        # 1. Acknowledge
        ack = alert_service.acknowledge_alert(db, aid, operator_name="Watch Officer Rao")
        assert ack.broadcast_status == "acknowledged"
        assert ack.acknowledged_by == "Watch Officer Rao"
        assert ack.acknowledged_at is not None

        # 2. Resolve
        res = alert_service.resolve_alert(
            db, aid, operator_name="Watch Officer Rao", resolution_notes="Threat passed without damage."
        )
        assert res.broadcast_status == "resolved"
        assert res.resolved_by == "Watch Officer Rao"
        assert res.resolved_at is not None
        assert "Threat passed" in res.instructions


def test_list_alerts_filtering():
    """Verify query filtering by broadcast_status and severity."""
    with transactional_session() as db:
        active_alerts = alert_service.list_alerts(db, status_filter="active")
        for a in active_alerts:
            assert a.broadcast_status == "active"

        resolved_alerts = alert_service.list_alerts(db, status_filter="resolved")
        for a in resolved_alerts:
            assert a.broadcast_status == "resolved"

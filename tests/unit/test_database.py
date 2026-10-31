"""Unit tests for SQLite schema, foreign keys, migrations, and repositories."""

import pytest
from pathlib import Path
from level_crossing.common.types import CrossingState, ZoneType, RuleClass, SeverityLevel, EventStatus, AlertType, AlertStatus
from level_crossing.database.db import DatabaseManager
from level_crossing.database.repository import EventRepository, AlertRepository, SystemLogRepository
from level_crossing.events.event import SafetyEvent
from level_crossing.alerts.alert import AlertRecord


@pytest.fixture
def temp_db(tmp_path: Path):
    db_file = tmp_path / "test_safety.sqlite3"
    return DatabaseManager(db_file)


def test_database_initialization(temp_db):
    with temp_db.connection() as conn:
        tables = [
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
            ).fetchall()
        ]
        assert "events" in tables
        assert "alerts" in tables
        assert "zones" in tables
        assert "system_logs" in tables
        assert "schema_migrations" in tables


def test_multiple_alerts_per_event(temp_db):
    event_repo = EventRepository(temp_db)
    alert_repo = AlertRepository(temp_db)

    # 1. Create and save event
    event = SafetyEvent.create(
        track_id=1,
        rule_class=RuleClass.PERSON,
        zone_type=ZoneType.DANGER_TRACK,
        severity=SeverityLevel.HIGH,
        crossing_state=CrossingState.OPEN,
        timestamp=1.0,
    )
    event_repo.save(event)

    # 2. Add INITIAL alert
    alert1 = AlertRecord.create(
        event_id=event.event_id,
        alert_type=AlertType.INITIAL,
        severity=SeverityLevel.HIGH,
        timestamp=1.5,
        message="Initial Intrusion",
    )
    alert_repo.save(alert1)

    # 3. Add ESCALATION alert for same event
    alert2 = AlertRecord.create(
        event_id=event.event_id,
        alert_type=AlertType.ESCALATION,
        severity=SeverityLevel.CRITICAL,
        timestamp=3.0,
        message="Escalated Hazard",
    )
    alert_repo.save(alert2)

    # 4. Verify multiple alerts retrieved for single event
    retrieved_alerts = alert_repo.list_for_event(event.event_id)
    assert len(retrieved_alerts) == 2
    assert retrieved_alerts[0].alert_type == "INITIAL"
    assert retrieved_alerts[1].alert_type == "ESCALATION"


def test_system_logs(temp_db):
    log_repo = SystemLogRepository(temp_db)
    log_repo.log(
        component="severity_evaluator",
        level="WARNING",
        message="Missing rule fallback triggered",
        context={"state": "UNKNOWN", "zone": "DANGER_TRACK"},
    )
    logs = log_repo.list_logs(limit=10)
    assert len(logs) == 1
    assert logs[0].component == "severity_evaluator"
    assert logs[0].level == "WARNING"
    assert "Missing rule fallback" in logs[0].message

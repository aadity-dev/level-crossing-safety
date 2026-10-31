"""Integration tests for FastAPI endpoints and health degradation semantics."""

import pytest
from fastapi.testclient import TestClient
from pathlib import Path

from level_crossing.common.types import HealthStatus, CrossingState, SeverityLevel, RuleClass, ZoneType, AlertType
from level_crossing.database.db import DatabaseManager
from level_crossing.api.main import create_app
from level_crossing.events.event import SafetyEvent
from level_crossing.alerts.alert import AlertRecord


@pytest.fixture
def client(tmp_path: Path):
    db_file = tmp_path / "test_api.sqlite3"
    app = create_app(config_dir="configs", db_path=str(db_file))
    with TestClient(app) as test_client:
        yield test_client


def test_health_normal_mode(client):
    # Test versioned endpoint
    res = client.get("/api/v1/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == HealthStatus.HEALTHY.value
    assert data["database_connected"] is True

    # Test root-level /health endpoint
    res_root = client.get("/health")
    assert res_root.status_code == 200
    assert res_root.json()["status"] == HealthStatus.HEALTHY.value

    # Test root discovery / endpoint
    res_index = client.get("/")
    assert res_index.status_code == 200
    assert res_index.json()["health_url"] == "/health"


def test_health_unknown_state_degrades(client):
    """V3.1 Gate: UNKNOWN crossing state must set health to DEGRADED, never NORMAL/HEALTHY."""
    # Set service crossing state to UNKNOWN
    service = client.app.state.safety_service
    service.set_crossing_state(CrossingState.UNKNOWN)

    res = client.get("/api/v1/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == HealthStatus.DEGRADED.value
    assert data["crossing_state"] == CrossingState.UNKNOWN.value


def test_events_and_alerts_endpoints(client):
    service = client.app.state.safety_service

    # Seed an event
    evt = SafetyEvent.create(
        track_id=10,
        rule_class=RuleClass.PERSON,
        zone_type=ZoneType.DANGER_TRACK,
        severity=SeverityLevel.CRITICAL,
        crossing_state=CrossingState.TRAIN_APPROACHING,
        timestamp=2.5,
    )
    service.event_repo.save(evt)

    # Seed an alert
    alt = AlertRecord.create(
        event_id=evt.event_id,
        alert_type=AlertType.INITIAL,
        severity=SeverityLevel.CRITICAL,
        timestamp=3.0,
        message="Critical Person in Track",
    )
    service.alert_repo.save(alt)

    # Query events
    res_events = client.get("/api/v1/events")
    assert res_events.status_code == 200
    events_list = res_events.json()
    assert len(events_list) >= 1
    assert events_list[0]["event_id"] == evt.event_id

    # Query event detail
    res_detail = client.get(f"/api/v1/events/{evt.event_id}")
    assert res_detail.status_code == 200
    detail = res_detail.json()
    assert len(detail["alerts"]) == 1
    assert detail["alerts"][0]["alert_id"] == alt.alert_id

    # Query alerts
    res_alerts = client.get("/api/v1/alerts")
    assert res_alerts.status_code == 200
    alerts_list = res_alerts.json()
    assert len(alerts_list) >= 1

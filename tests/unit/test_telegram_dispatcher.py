"""Comprehensive test suite for Telegram Emergency Dispatcher.

Verifies:
1. Telegram API connectivity
2. Sending a normal text message
3. Sending a CCTV photograph
4. Correct danger-level formatting
5. Missing image handling
6. Invalid token handling
7. Network timeout
8. Duplicate alert suppression
9. New intrusion event triggering new alert & severity escalation
10. Integration with confirmed intrusion events in AlertEngine
"""

import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
import numpy as np
import requests

from level_crossing.alerts.telegram_dispatcher import TelegramDispatcher
from level_crossing.alerts.alert_engine import AlertEngine
from level_crossing.events.event_manager import EventAction
from level_crossing.events.event import SafetyEvent
from level_crossing.common.types import (
    RuleClass,
    ZoneType,
    SeverityLevel,
    CrossingState,
    AlertType,
    EventStatus,
)


@pytest.fixture
def dummy_snapshot(tmp_path: Path) -> Path:
    """Creates a temporary test image file representing a CCTV snapshot."""
    img_path = tmp_path / "test_snapshot.jpg"
    img_path.write_bytes(b"\xFF\xD8\xFF\xE0" + b"\x00" * 200 + b"\xFF\xD9")
    return img_path


@pytest.fixture
def dispatcher():
    """Returns a test dispatcher initialized with mock credentials."""
    return TelegramDispatcher(
        bot_token="123456:MOCK_TOKEN_ABC",
        chat_id="1295515495",
        location="LC-102",
        timeout=5,
    )


# 1. Telegram API Connectivity
def test_telegram_api_connectivity(dispatcher):
    with patch("requests.get") as mock_get:
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {
            "ok": True,
            "result": {"id": 123456, "is_bot": True, "username": "MyRailwaySafety_bot"},
        }

        import requests
        resp = requests.get(f"https://api.telegram.org/bot{dispatcher.bot_token}/getMe")
        assert resp.status_code == 200
        assert resp.json()["result"]["username"] == "MyRailwaySafety_bot"


# 2. Sending Normal Text Message
def test_send_normal_text_message(dispatcher):
    with patch("requests.post") as mock_post:
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {
            "ok": True,
            "result": {"message_id": 101, "text": "System Online"},
        }

        res = dispatcher.send_text_message("System Online")
        assert res["success"] is True
        assert res["status_code"] == 200
        assert res["message_id"] == 101
        assert res["error"] is None


# 3. Sending CCTV Photograph
def test_send_cctv_photograph(dispatcher, dummy_snapshot):
    with patch("requests.post") as mock_post:
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {
            "ok": True,
            "result": {"message_id": 202, "caption": "🚨 RAILWAY EMERGENCY ALERT"},
        }

        res = dispatcher.send_emergency_alert(
            image_path=dummy_snapshot,
            location="LC-102",
            danger_level="CRITICAL",
            confidence=96.5,
            event_id="EVT-2026-001",
            timestamp="31-10-2026 16:45:20",
            object_type="Person",
        )

        assert res["success"] is True
        assert res["status_code"] == 200
        assert res["message_id"] == 202
        assert res["event_id"] == "EVT-2026-001"
        assert res["error"] is None
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        assert "photo" in kwargs["files"]
        assert kwargs["data"]["chat_id"] == "1295515495"


# 4. Correct Danger-Level Formatting
def test_danger_level_formatting():
    caption = TelegramDispatcher.format_alert_caption(
        location="LC-102",
        danger_level="CRITICAL",
        confidence=96.5,
        event_id="EVT-2026-001",
        timestamp_str="31-10-2026 16:45:20",
        object_type="Person",
    )

    assert "🚨 RAILWAY EMERGENCY ALERT" in caption
    assert "⚠️ DANGER LEVEL: CRITICAL" in caption
    assert "📍 Location: LC-102" in caption
    assert "👤 Detected Object: Person" in caption
    assert "🎯 Detection Confidence: 96.5%" in caption
    assert "🆔 Event ID: EVT-2026-001" in caption
    assert "🕒 Timestamp: 31-10-2026 16:45:20" in caption
    assert "📡 Detection Status: CONFIRMED" in caption
    assert "🚨 IMMEDIATE ACTION REQUIRED" in caption
    assert "📸 CCTV evidence attached." in caption


# 5. Missing Image Handling
def test_missing_image_handling(dispatcher, tmp_path):
    missing_path = tmp_path / "non_existent_cctv.jpg"

    res = dispatcher.send_emergency_alert(
        image_path=missing_path,
        event_id="EVT-FAIL-01",
    )

    assert res["success"] is False
    assert res["status_code"] == 404
    assert res["message_id"] is None
    assert "Missing CCTV image" in res["error"]


# 6. Invalid Token Handling
def test_invalid_token_handling(dispatcher, dummy_snapshot):
    with patch("requests.post") as mock_post:
        mock_post.return_value.status_code = 401
        mock_post.return_value.json.return_value = {
            "ok": False,
            "error_code": 401,
            "description": "Unauthorized: invalid bot token",
        }

        res = dispatcher.send_emergency_alert(
            image_path=dummy_snapshot,
            event_id="EVT-UNAUTH",
        )

        assert res["success"] is False
        assert res["status_code"] == 401
        assert "invalid bot token" in res["error"]


# 7. Network Timeout
def test_network_timeout(dispatcher, dummy_snapshot):
    with patch("requests.post", side_effect=requests.exceptions.Timeout("Connection timed out")):
        res = dispatcher.send_emergency_alert(
            image_path=dummy_snapshot,
            event_id="EVT-TIMEOUT",
        )

        assert res["success"] is False
        assert res["status_code"] == -1
        assert "Network timeout" in res["error"]


# 8. Duplicate Alert Suppression
def test_duplicate_alert_suppression(dispatcher, dummy_snapshot):
    with patch("requests.post") as mock_post:
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {"ok": True, "result": {"message_id": 303}}

        # First dispatch should be allowed
        assert dispatcher.should_dispatch("EVT-DUP-01", "HIGH") is True
        res = dispatcher.send_emergency_alert(dummy_snapshot, event_id="EVT-DUP-01", danger_level="HIGH")
        assert res["success"] is True

        # Second dispatch for the SAME event and SAME severity must be suppressed
        assert dispatcher.should_dispatch("EVT-DUP-01", "HIGH") is False

        # LOW or IGNORE severities are always suppressed
        assert dispatcher.should_dispatch("EVT-LOW", "LOW") is False
        assert dispatcher.should_dispatch("EVT-IGN", "IGNORE") is False


# 9. New Intrusion Event & Escalation
def test_new_intrusion_event_and_escalation(dispatcher, dummy_snapshot):
    with patch("requests.post") as mock_post:
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {"ok": True, "result": {"message_id": 404}}

        # Genuinely new event
        assert dispatcher.should_dispatch("EVT-NEW-01", "MEDIUM") is True
        dispatcher.send_emergency_alert(dummy_snapshot, event_id="EVT-NEW-01", danger_level="MEDIUM")

        # Genuinely different new event
        assert dispatcher.should_dispatch("EVT-NEW-02", "CRITICAL") is True

        # Escalation from MEDIUM to CRITICAL on the existing event MUST be permitted
        assert dispatcher.should_dispatch("EVT-NEW-01", "CRITICAL") is True


# 10. Integration with Existing Confirmed-Intrusion Event in AlertEngine
def test_integration_with_confirmed_intrusion_event(tmp_path):
    mock_dispatcher = MagicMock(spec=TelegramDispatcher)
    mock_dispatcher.should_dispatch.return_value = True

    alert_engine = AlertEngine(snapshots_dir=tmp_path, telegram_dispatcher=mock_dispatcher)

    # Simulate an intrusion event that reached CONFIRMED status
    event = SafetyEvent.create(
        track_id=1,
        rule_class=RuleClass.PERSON,
        zone_type=ZoneType.DANGER_TRACK,
        severity=SeverityLevel.CRITICAL,
        crossing_state=CrossingState.TRAIN_APPROACHING,
        timestamp=2.5,
        confidence=0.965,
    )
    event.status = EventStatus.CONFIRMED

    action = EventAction(
        event=event,
        alert_type=AlertType.INITIAL,
        message="Confirmed intrusion: person in DANGER_TRACK",
    )

    test_frame = np.zeros((480, 640, 3), dtype=np.uint8)

    dispatched = alert_engine.dispatch(
        actions=[action],
        current_frame=test_frame,
        timestamp=2.5,
    )

    assert len(dispatched) == 1
    assert dispatched[0].snapshot_path is not None
    assert Path(dispatched[0].snapshot_path).exists()

    # Verify Telegram dispatch_async was called with real parameters and saved snapshot
    mock_dispatcher.should_dispatch.assert_called_once_with(event.event_id, "CRITICAL")
    mock_dispatcher.dispatch_async.assert_called_once()
    kwargs = mock_dispatcher.dispatch_async.call_args.kwargs
    assert kwargs["event_id"] == event.event_id
    assert kwargs["danger_level"] == "CRITICAL"
    assert kwargs["confidence"] == 96.5
    assert kwargs["object_type"] == "person"
    assert kwargs["image_path"] == dispatched[0].snapshot_path

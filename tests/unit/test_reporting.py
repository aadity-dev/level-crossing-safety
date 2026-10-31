"""Unit tests for official incident PDF report generation."""

import pytest
from level_crossing.reporting.incident_report import generate_incident_pdf_bytes


def test_generate_incident_pdf_bytes_no_image():
    pdf_bytes = generate_incident_pdf_bytes(
        alert_id="ALT-TEST-123",
        event_id="EVT-TEST-456",
        severity="CRITICAL",
        alert_type="INITIAL",
        message="Confirmed intrusion: person in DANGER_TRACK for 1.0s",
        crossing_state="TRAIN_APPROACHING",
        timestamp_sec=1.2,
        wall_clock_time="2026-10-31T12:00:00Z",
        snapshot_path=None,
    )
    assert len(pdf_bytes) > 1000
    assert pdf_bytes.startswith(b"%PDF-")


def test_generate_incident_pdf_bytes_medium_severity():
    pdf_bytes = generate_incident_pdf_bytes(
        alert_id="ALT-TEST-999",
        event_id="EVT-TEST-888",
        severity="MEDIUM",
        alert_type="RECOVERY",
        message="Hazard recovered",
        crossing_state="OPEN",
        timestamp_sec=5.0,
        wall_clock_time="2026-10-31T12:05:00Z",
        snapshot_path=None,
    )
    assert len(pdf_bytes) > 1000
    assert pdf_bytes.startswith(b"%PDF-")

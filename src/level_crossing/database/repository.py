"""Repository pattern implementation for SQLite storage."""

import json
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from level_crossing.database.db import DatabaseManager
from level_crossing.database.models import EventDBRecord, AlertDBRecord, ZoneDBRecord, LogDBRecord
from level_crossing.events.event import SafetyEvent
from level_crossing.alerts.alert import AlertRecord


class EventRepository:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    def save(self, event: SafetyEvent) -> None:
        created_at = datetime.now(timezone.utc).isoformat()
        with self.db.connection() as conn:
            conn.execute(
                """
                INSERT INTO events (
                    event_id, track_id, rule_class, zone_type, initial_severity,
                    current_severity, crossing_state, start_time, end_time,
                    status, unsafe_duration, escalation_count, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(event_id) DO UPDATE SET
                    current_severity=excluded.current_severity,
                    crossing_state=excluded.crossing_state,
                    end_time=excluded.end_time,
                    status=excluded.status,
                    unsafe_duration=excluded.unsafe_duration,
                    escalation_count=excluded.escalation_count
                """,
                (
                    event.event_id,
                    event.track_id,
                    event.rule_class.value,
                    event.zone_type.value,
                    event.initial_severity.value,
                    event.current_severity.value,
                    event.crossing_state.value,
                    event.start_time,
                    event.end_time,
                    event.status.value,
                    event.unsafe_duration,
                    event.escalation_count,
                    created_at,
                ),
            )

    def get_by_id(self, event_id: str) -> Optional[EventDBRecord]:
        with self.db.connection() as conn:
            row = conn.execute("SELECT * FROM events WHERE event_id = ?", (event_id,)).fetchone()
            if row:
                return EventDBRecord(**dict(row))
            return None

    def list_events(self, limit: int = 100) -> List[EventDBRecord]:
        with self.db.connection() as conn:
            rows = conn.execute("SELECT * FROM events ORDER BY start_time DESC LIMIT ?", (limit,)).fetchall()
            return [EventDBRecord(**dict(r)) for r in rows]


class AlertRepository:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    def save(self, alert: AlertRecord) -> None:
        with self.db.connection() as conn:
            conn.execute(
                """
                INSERT INTO alerts (
                    alert_id, event_id, alert_type, severity, timestamp,
                    wall_clock_time, status, message, snapshot_path
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(alert_id) DO UPDATE SET
                    status=excluded.status
                """,
                (
                    alert.alert_id,
                    alert.event_id,
                    alert.alert_type.value,
                    alert.severity.value,
                    alert.timestamp,
                    alert.wall_clock_time,
                    alert.status.value,
                    alert.message,
                    alert.snapshot_path,
                ),
            )

    def list_alerts(self, limit: int = 100) -> List[AlertDBRecord]:
        with self.db.connection() as conn:
            rows = conn.execute("SELECT * FROM alerts ORDER BY timestamp DESC LIMIT ?", (limit,)).fetchall()
            return [AlertDBRecord(**dict(r)) for r in rows]

    def list_for_event(self, event_id: str) -> List[AlertDBRecord]:
        with self.db.connection() as conn:
            rows = conn.execute("SELECT * FROM alerts WHERE event_id = ? ORDER BY timestamp ASC", (event_id,)).fetchall()
            return [AlertDBRecord(**dict(r)) for r in rows]


class SystemLogRepository:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    def log(self, component: str, level: str, message: str, context: Optional[Dict[str, Any]] = None) -> None:
        ts = datetime.now(timezone.utc).isoformat()
        ctx_str = json.dumps(context) if context else None
        with self.db.connection() as conn:
            conn.execute(
                "INSERT INTO system_logs (timestamp, component, level, message, context_json) VALUES (?, ?, ?, ?, ?)",
                (ts, component, level, message, ctx_str),
            )

    def list_logs(self, limit: int = 100) -> List[LogDBRecord]:
        with self.db.connection() as conn:
            rows = conn.execute("SELECT * FROM system_logs ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
            return [LogDBRecord(**dict(r)) for r in rows]

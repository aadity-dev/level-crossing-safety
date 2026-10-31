"""Safety service encapsulating data access and health monitoring."""

from typing import List, Optional, Dict, Any
from pathlib import Path

from level_crossing.common.types import HealthStatus, CrossingState
from level_crossing.database.db import DatabaseManager
from level_crossing.database.repository import EventRepository, AlertRepository, SystemLogRepository
from level_crossing.database.models import EventDBRecord, AlertDBRecord


class SafetyService:
    """Provides application-layer services for API routes."""

    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        self.event_repo = EventRepository(db_manager)
        self.alert_repo = AlertRepository(db_manager)
        self.log_repo = SystemLogRepository(db_manager)
        self.current_crossing_state: CrossingState = CrossingState.OPEN

    def set_crossing_state(self, state: CrossingState) -> None:
        self.current_crossing_state = state

    def check_health(self) -> Dict[str, Any]:
        """Evaluates system health. UNKNOWN crossing state immediately sets health to DEGRADED."""
        db_ok = False
        try:
            with self.db.connection() as conn:
                conn.execute("SELECT 1")
            db_ok = True
        except Exception:
            db_ok = False

        status = HealthStatus.HEALTHY
        details = {}

        if not db_ok:
            status = HealthStatus.FAILED
            details["database"] = "unhealthy"
        else:
            details["database"] = "connected"

        # V3.1 Specification: UNKNOWN crossing state must set health to DEGRADED, never NORMAL/HEALTHY
        if self.current_crossing_state == CrossingState.UNKNOWN:
            status = HealthStatus.DEGRADED
            details["crossing_state_reason"] = "Crossing state is UNKNOWN - safe degraded mode engaged"

        return {
            "status": status,
            "crossing_state": self.current_crossing_state,
            "database_connected": db_ok,
            "model_loaded": True,
            "details": details,
        }

    def list_events(self, limit: int = 50) -> List[EventDBRecord]:
        return self.event_repo.list_events(limit=limit)

    def get_event(self, event_id: str) -> Optional[EventDBRecord]:
        return self.event_repo.get_by_id(event_id)

    def list_alerts(self, limit: int = 50) -> List[AlertDBRecord]:
        return self.alert_repo.list_alerts(limit=limit)

    def get_event_alerts(self, event_id: str) -> List[AlertDBRecord]:
        return self.alert_repo.list_for_event(event_id)

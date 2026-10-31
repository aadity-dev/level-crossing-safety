"""Alert API schemas."""

from pydantic import BaseModel
from typing import Optional
from level_crossing.common.types import SeverityLevel, AlertType, AlertStatus


class AlertItemResponse(BaseModel):
    alert_id: str
    event_id: str
    alert_type: AlertType
    severity: SeverityLevel
    timestamp: float
    wall_clock_time: str
    status: AlertStatus
    message: str
    snapshot_path: Optional[str] = None

"""Event API schemas."""

from pydantic import BaseModel
from typing import Optional, List
from level_crossing.common.types import EventStatus, SeverityLevel, RuleClass, ZoneType, CrossingState


class EventResponse(BaseModel):
    event_id: str
    track_id: int
    rule_class: RuleClass
    zone_type: ZoneType
    initial_severity: SeverityLevel
    current_severity: SeverityLevel
    crossing_state: CrossingState
    start_time: float
    end_time: Optional[float]
    status: EventStatus
    unsafe_duration: float
    escalation_count: int
    created_at: str


class EventDetailResponse(EventResponse):
    alerts: List["AlertResponse"] = []


class AlertResponse(BaseModel):
    alert_id: str
    event_id: str
    alert_type: str
    severity: SeverityLevel
    timestamp: float
    wall_clock_time: str
    status: str
    message: str
    snapshot_path: Optional[str] = None

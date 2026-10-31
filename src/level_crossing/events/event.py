"""Safety event data models and state transitions."""

import uuid
from dataclasses import dataclass, field
from typing import List, Optional
from level_crossing.common.types import (
    EventStatus,
    SeverityLevel,
    RuleClass,
    ZoneType,
    CrossingState,
    BoundingBox,
)


@dataclass
class SafetyEvent:
    """Stateful safety event lifecycle record."""
    event_id: str
    track_id: int
    rule_class: RuleClass
    zone_type: ZoneType
    initial_severity: SeverityLevel
    current_severity: SeverityLevel
    crossing_state: CrossingState
    start_time: float       # Timestamp when condition became unsafe
    last_update_time: float
    status: EventStatus = EventStatus.PENDING
    end_time: Optional[float] = None
    last_bbox: Optional[BoundingBox] = None
    alert_ids: List[str] = field(default_factory=list)
    escalation_count: int = 0
    unsafe_duration: float = 0.0

    @classmethod
    def create(
        cls,
        track_id: int,
        rule_class: RuleClass,
        zone_type: ZoneType,
        severity: SeverityLevel,
        crossing_state: CrossingState,
        timestamp: float,
        bbox: Optional[BoundingBox] = None,
    ) -> "SafetyEvent":
        return cls(
            event_id=f"EVT-{uuid.uuid4().hex[:8].upper()}",
            track_id=track_id,
            rule_class=rule_class,
            zone_type=zone_type,
            initial_severity=severity,
            current_severity=severity,
            crossing_state=crossing_state,
            start_time=timestamp,
            last_update_time=timestamp,
            status=EventStatus.PENDING,
            last_bbox=bbox,
            unsafe_duration=0.0,
        )

    def update_condition(
        self,
        severity: SeverityLevel,
        crossing_state: CrossingState,
        zone_type: ZoneType,
        timestamp: float,
        bbox: Optional[BoundingBox] = None,
    ) -> bool:
        self.last_update_time = timestamp
        self.crossing_state = crossing_state
        self.zone_type = zone_type
        if bbox is not None:
            self.last_bbox = bbox
        self.unsafe_duration = max(0.0, timestamp - self.start_time)

        escalated = False
        if severity > self.current_severity:
            self.current_severity = severity
            self.escalation_count += 1
            escalated = True
        return escalated

    def close(self, timestamp: float, recovered: bool = True) -> None:
        self.end_time = timestamp
        self.last_update_time = timestamp
        self.unsafe_duration = max(0.0, timestamp - self.start_time)
        self.status = EventStatus.RECOVERED if recovered else EventStatus.CLOSED

"""Data transfer records matching database relational schema."""

from dataclasses import dataclass
from typing import Optional, List, Dict, Any


@dataclass
class EventDBRecord:
    event_id: str
    track_id: int
    rule_class: str
    zone_type: str
    initial_severity: str
    current_severity: str
    crossing_state: str
    start_time: float
    end_time: Optional[float]
    status: str
    unsafe_duration: float
    escalation_count: int
    created_at: str


@dataclass
class AlertDBRecord:
    alert_id: str
    event_id: str
    alert_type: str
    severity: str
    timestamp: float
    wall_clock_time: str
    status: str
    message: str
    snapshot_path: Optional[str]


@dataclass
class ZoneDBRecord:
    zone_id: str
    name: str
    zone_type: str
    description: str
    polygon_json: str
    criticality: int
    updated_at: str


@dataclass
class LogDBRecord:
    id: Optional[int]
    timestamp: str
    component: str
    level: str
    message: str
    context_json: Optional[str]

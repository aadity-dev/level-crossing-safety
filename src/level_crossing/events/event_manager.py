"""Stateful safety event manager orchestrating temporal risk lifecycle and transitions."""

from typing import Dict, List, Optional, Tuple, Set
from level_crossing.common.types import (
    CrossingState,
    ZoneType,
    RuleClass,
    SeverityLevel,
    EventStatus,
    AlertType,
)
from level_crossing.common.config import EventManagerThresholds
from level_crossing.common.logger import get_logger
from level_crossing.scene_state.zone_manager import TrackSceneState
from level_crossing.events.event import SafetyEvent

logger = get_logger("event_manager")


class EventAction:
    """Action emitted by EventManager to notify the Alert Engine."""
    def __init__(self, event: SafetyEvent, alert_type: AlertType, message: str):
        self.event = event
        self.alert_type = alert_type
        self.message = message


class EventManager:
    """Owns unsafe-condition timers, event lifecycles, and alert trigger decisions."""

    def __init__(self, thresholds: EventManagerThresholds):
        self.thresholds = thresholds
        # Active events mapped by track_id
        self.active_events: Dict[int, SafetyEvent] = {}
        # Historical / completed events
        self.closed_events: List[SafetyEvent] = []
        # Cooldown tracking: track_id -> last_alert_time
        self._last_alert_time: Dict[int, float] = {}
        # Tracks pending escalation alert awaiting cooldown expiration
        self._pending_escalation: Dict[int, bool] = {}

    def is_unsafe(self, severity: SeverityLevel) -> bool:
        """Determines if a severity level constitutes an alertable unsafe condition."""
        return severity in (SeverityLevel.MEDIUM, SeverityLevel.HIGH, SeverityLevel.CRITICAL)

    def process(
        self,
        evaluated_states: List[Tuple[TrackSceneState, SeverityLevel]],
        crossing_state: CrossingState,
        timestamp: float,
    ) -> List[EventAction]:
        """Evaluates temporal state transitions and returns required alert actions."""
        actions: List[EventAction] = []
        seen_track_ids: Set[int] = set()

        for scene_state, severity in evaluated_states:
            tid = scene_state.track_id
            seen_track_ids.add(tid)
            is_currently_unsafe = self.is_unsafe(severity)

            existing_event = self.active_events.get(tid)

            if is_currently_unsafe:
                if existing_event is None:
                    # New unsafe condition initiated at current timestamp
                    event = SafetyEvent.create(
                        track_id=tid,
                        rule_class=scene_state.rule_class,
                        zone_type=scene_state.zone_type or ZoneType.APPROACH_ROAD,
                        severity=severity,
                        crossing_state=crossing_state,
                        timestamp=timestamp,
                        bbox=scene_state.bbox,
                    )
                    self.active_events[tid] = event
                    logger.info(
                        f"Unsafe condition initiated for Track {tid} ({scene_state.rule_class.value}) "
                        f"in {scene_state.zone_type} at severity {severity.value} (t={timestamp:.2f}s)"
                    )
                    existing_event = event
                else:
                    # Update existing active event
                    severity_increased = existing_event.update_condition(
                        severity=severity,
                        crossing_state=crossing_state,
                        zone_type=scene_state.zone_type or existing_event.zone_type,
                        timestamp=timestamp,
                        bbox=scene_state.bbox,
                    )
                    if severity_increased:
                        self._pending_escalation[tid] = True

                # Check lifecycle transitions
                dwell_limit = self.thresholds.confirmation_dwell_seconds.get(
                    existing_event.zone_type.value,
                    self.thresholds.confirmation_dwell_seconds.get("default", 1.5),
                )

                # 1. PENDING -> CONFIRMED
                if existing_event.status == EventStatus.PENDING:
                    if existing_event.unsafe_duration >= dwell_limit:
                        existing_event.status = EventStatus.CONFIRMED
                        self._last_alert_time[tid] = timestamp
                        msg = (
                            f"Confirmed intrusion: {existing_event.rule_class.value} in "
                            f"{existing_event.zone_type.value} for {existing_event.unsafe_duration:.1f}s "
                            f"(Severity: {existing_event.current_severity.value})"
                        )
                        actions.append(EventAction(existing_event, AlertType.INITIAL, msg))
                        logger.warning(f"EVENT CONFIRMED: {msg}")

                # 2. CONFIRMED / ESCALATED -> ESCALATION ALERT
                if existing_event.status in (EventStatus.CONFIRMED, EventStatus.ESCALATED):
                    time_since_alert = timestamp - self._last_alert_time.get(tid, 0.0)
                    duration_escalate = existing_event.unsafe_duration >= self.thresholds.escalation_seconds
                    pending = self._pending_escalation.get(tid, False)

                    if (pending or duration_escalate) and (time_since_alert >= self.thresholds.cooldown_seconds):
                        existing_event.status = EventStatus.ESCALATED
                        self._last_alert_time[tid] = timestamp
                        self._pending_escalation[tid] = False
                        msg = (
                            f"Escalated hazard: {existing_event.rule_class.value} persists in "
                            f"{existing_event.zone_type.value} ({existing_event.unsafe_duration:.1f}s, "
                            f"Severity: {existing_event.current_severity.value})"
                        )
                        actions.append(EventAction(existing_event, AlertType.ESCALATION, msg))
                        logger.error(f"EVENT ESCALATED: {msg}")

            else:
                # Severity is safe (IGNORE or LOW) -> check if an existing event has recovered
                if existing_event is not None and existing_event.status in (
                    EventStatus.CONFIRMED,
                    EventStatus.ESCALATED,
                ):
                    existing_event.close(timestamp, recovered=True)
                    self.closed_events.append(existing_event)
                    self.active_events.pop(tid, None)
                    self._last_alert_time.pop(tid, None)
                    self._pending_escalation.pop(tid, None)

                    msg = f"Hazard cleared: Track {tid} exited danger condition at t={timestamp:.2f}s"
                    actions.append(EventAction(existing_event, AlertType.RECOVERY, msg))
                    logger.info(f"EVENT RECOVERED: {msg}")
                elif existing_event is not None and existing_event.status == EventStatus.PENDING:
                    # Cancelled before confirmation
                    self.active_events.pop(tid, None)
                    self._pending_escalation.pop(tid, None)

        # Handle tracks that disappeared from the frame (track lost / deleted)
        missing_tracks = [tid for tid in self.active_events.keys() if tid not in seen_track_ids]
        for tid in missing_tracks:
            event = self.active_events[tid]
            time_since_seen = timestamp - event.last_update_time
            if time_since_seen > self.thresholds.track_lost_timeout_seconds:
                event.close(timestamp, recovered=False)
                self.closed_events.append(event)
                self.active_events.pop(tid, None)
                self._last_alert_time.pop(tid, None)
                self._pending_escalation.pop(tid, None)
                logger.info(f"Track {tid} lost beyond timeout. Event {event.event_id} closed.")

        return actions

    def reset(self) -> None:
        self.active_events.clear()
        self.closed_events.clear()
        self._last_alert_time.clear()
        self._pending_escalation.clear()

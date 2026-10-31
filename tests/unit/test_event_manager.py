"""Unit tests for Event Manager temporal reasoning, unsafe timer, and state transitions."""

import pytest
from level_crossing.common.types import (
    CrossingState,
    ZoneType,
    RuleClass,
    SeverityLevel,
    EventStatus,
    MovementStatus,
    BoundingBox,
    AlertType,
)
from level_crossing.common.config import EventManagerThresholds
from level_crossing.scene_state.zone_manager import TrackSceneState
from level_crossing.events.event_manager import EventManager


def create_dummy_scene_state(
    track_id: int,
    rule_class: RuleClass,
    zone_type: ZoneType,
    crossing_state: CrossingState,
    timestamp: float,
    dwell_sec: float = 0.0,
) -> TrackSceneState:
    return TrackSceneState(
        track_id=track_id,
        rule_class=rule_class,
        bbox=BoundingBox(10, 10, 50, 50),
        zone=None,
        zone_type=zone_type,
        dwell_seconds=dwell_sec,
        movement_status=MovementStatus.STATIONARY,
        crossing_state=crossing_state,
        entry_timestamp=timestamp - dwell_sec,
        timestamp=timestamp,
    )


def test_person_already_in_zone_when_state_changes():
    """V3.1 CRITICAL TEST: If a person is already inside a zone when the crossing state becomes unsafe,
    the unsafe-condition timer must start at the exact state-change timestamp."""
    thresholds = EventManagerThresholds(
        confirmation_dwell_seconds={"DANGER_TRACK": 1.0, "default": 1.0},
        cooldown_seconds=5.0,
    )
    manager = EventManager(thresholds=thresholds)

    # t=0.0s to t=5.0s: Person in PEDESTRIAN_CROSSING during OPEN (Severity: LOW -> safe)
    # Zone dwell is 5.0s, but condition is safe -> NO active event
    ss_safe = create_dummy_scene_state(
        track_id=1,
        rule_class=RuleClass.PERSON,
        zone_type=ZoneType.PEDESTRIAN_CROSSING,
        crossing_state=CrossingState.OPEN,
        timestamp=5.0,
        dwell_sec=5.0,
    )
    actions = manager.process([(ss_safe, SeverityLevel.LOW)], CrossingState.OPEN, timestamp=5.0)
    assert len(actions) == 0
    assert 1 not in manager.active_events

    # At t=10.0s: State transitions to TRAIN_APPROACHING!
    # Severity becomes CRITICAL. Person has been in zone for 10s, but unsafe condition starts AT t=10.0s!
    ss_danger = create_dummy_scene_state(
        track_id=1,
        rule_class=RuleClass.PERSON,
        zone_type=ZoneType.PEDESTRIAN_CROSSING,
        crossing_state=CrossingState.TRAIN_APPROACHING,
        timestamp=10.0,
        dwell_sec=10.0,
    )
    actions = manager.process([(ss_danger, SeverityLevel.CRITICAL)], CrossingState.TRAIN_APPROACHING, timestamp=10.0)
    assert 1 in manager.active_events
    event = manager.active_events[1]
    # Unsafe timer started at t=10.0s (not t=0.0s)
    assert event.start_time == 10.0
    assert event.unsafe_duration == 0.0
    assert event.status == EventStatus.PENDING

    # At t=11.2s: 1.2s has elapsed since state transition -> exceeds confirmation threshold (1.0s) -> CONFIRMED!
    ss_danger_11 = create_dummy_scene_state(
        track_id=1,
        rule_class=RuleClass.PERSON,
        zone_type=ZoneType.PEDESTRIAN_CROSSING,
        crossing_state=CrossingState.TRAIN_APPROACHING,
        timestamp=11.2,
        dwell_sec=11.2,
    )
    actions = manager.process([(ss_danger_11, SeverityLevel.CRITICAL)], CrossingState.TRAIN_APPROACHING, timestamp=11.2)
    assert len(actions) == 1
    assert actions[0].alert_type == AlertType.INITIAL
    assert event.status == EventStatus.CONFIRMED


def test_escalation_and_cooldown():
    """Tests HIGH to CRITICAL escalation and cooldown window enforcement."""
    thresholds = EventManagerThresholds(
        confirmation_dwell_seconds={"DANGER_TRACK": 0.5, "default": 0.5},
        escalation_seconds=2.0,
        cooldown_seconds=4.0,
    )
    manager = EventManager(thresholds=thresholds)

    # t=1.0s: Vehicle in DANGER_TRACK during OPEN -> HIGH
    ss_high = create_dummy_scene_state(
        track_id=2,
        rule_class=RuleClass.VEHICLE,
        zone_type=ZoneType.DANGER_TRACK,
        crossing_state=CrossingState.OPEN,
        timestamp=1.0,
    )
    manager.process([(ss_high, SeverityLevel.HIGH)], CrossingState.OPEN, timestamp=1.0)

    # t=1.6s: Confirmed INITIAL alert emitted
    ss_high_16 = create_dummy_scene_state(
        track_id=2,
        rule_class=RuleClass.VEHICLE,
        zone_type=ZoneType.DANGER_TRACK,
        crossing_state=CrossingState.OPEN,
        timestamp=1.6,
    )
    actions = manager.process([(ss_high_16, SeverityLevel.HIGH)], CrossingState.OPEN, timestamp=1.6)
    assert len(actions) == 1
    assert actions[0].alert_type == AlertType.INITIAL

    # t=2.0s: Crossing state changes to TRAIN_APPROACHING -> Severity escalates to CRITICAL
    # But cooldown (4.0s from 1.6s) is active -> action suppressed until cooldown expires
    ss_crit = create_dummy_scene_state(
        track_id=2,
        rule_class=RuleClass.VEHICLE,
        zone_type=ZoneType.DANGER_TRACK,
        crossing_state=CrossingState.TRAIN_APPROACHING,
        timestamp=2.0,
    )
    actions = manager.process([(ss_crit, SeverityLevel.CRITICAL)], CrossingState.TRAIN_APPROACHING, timestamp=2.0)
    assert len(actions) == 0  # Cooldown active

    # t=5.7s: Cooldown expired (1.6 + 4.0 = 5.6s) -> ESCALATION alert emitted
    ss_crit_57 = create_dummy_scene_state(
        track_id=2,
        rule_class=RuleClass.VEHICLE,
        zone_type=ZoneType.DANGER_TRACK,
        crossing_state=CrossingState.TRAIN_APPROACHING,
        timestamp=5.7,
    )
    actions = manager.process([(ss_crit_57, SeverityLevel.CRITICAL)], CrossingState.TRAIN_APPROACHING, timestamp=5.7)
    assert len(actions) == 1
    assert actions[0].alert_type == AlertType.ESCALATION


def test_hazard_recovery_when_exiting_danger():
    """When tracked object leaves danger zone, event transitions to RECOVERED and emits RECOVERY action."""
    thresholds = EventManagerThresholds(
        confirmation_dwell_seconds={"DANGER_TRACK": 0.5, "default": 0.5},
    )
    manager = EventManager(thresholds=thresholds)

    ss_in = create_dummy_scene_state(
        track_id=3,
        rule_class=RuleClass.PERSON,
        zone_type=ZoneType.DANGER_TRACK,
        crossing_state=CrossingState.OPEN,
        timestamp=1.0,
    )
    manager.process([(ss_in, SeverityLevel.MEDIUM)], CrossingState.OPEN, timestamp=1.0)

    ss_in_conf = create_dummy_scene_state(
        track_id=3,
        rule_class=RuleClass.PERSON,
        zone_type=ZoneType.DANGER_TRACK,
        crossing_state=CrossingState.OPEN,
        timestamp=1.6,
    )
    manager.process([(ss_in_conf, SeverityLevel.MEDIUM)], CrossingState.OPEN, timestamp=1.6)

    # At t=2.0s: Person exits danger zone -> Severity becomes IGNORE
    ss_out = create_dummy_scene_state(
        track_id=3,
        rule_class=RuleClass.PERSON,
        zone_type=None,
        crossing_state=CrossingState.OPEN,
        timestamp=2.0,
    )
    actions = manager.process([(ss_out, SeverityLevel.IGNORE)], CrossingState.OPEN, timestamp=2.0)
    assert len(actions) == 1
    assert actions[0].alert_type == AlertType.RECOVERY
    assert 3 not in manager.active_events
    assert len(manager.closed_events) == 1
    assert manager.closed_events[0].status == EventStatus.RECOVERED

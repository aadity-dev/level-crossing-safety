"""Unit tests for train misclassification suppression and audit logging."""

import pytest
from level_crossing.common.types import CrossingState, ZoneType, RuleClass, MovementStatus, BoundingBox
from level_crossing.scene_state.zone_manager import TrackSceneState
from level_crossing.events.train_suppression import TrainMisclassificationMitigation


def test_truck_overlapping_train_suppressed_and_logged():
    mitigation = TrainMisclassificationMitigation(enabled=True, overlap_iou_threshold=0.25)

    # Train bounding box
    train_state = TrackSceneState(
        track_id=1,
        rule_class=RuleClass.TRAIN,
        bbox=BoundingBox(100, 100, 400, 300),
        zone=None,
        zone_type=ZoneType.DANGER_TRACK,
        dwell_seconds=1.0,
        movement_status=MovementStatus.SLOW,
        crossing_state=CrossingState.TRAIN_PASSING,
        entry_timestamp=0.0,
        timestamp=1.0,
    )

    # Suspected misclassified truck overlapping the train significantly (e.g. carriage)
    truck_state = TrackSceneState(
        track_id=2,
        rule_class=RuleClass.VEHICLE,
        bbox=BoundingBox(120, 110, 380, 290),  # Heavy overlap with train
        zone=None,
        zone_type=ZoneType.DANGER_TRACK,
        dwell_seconds=1.0,
        movement_status=MovementStatus.SLOW,
        crossing_state=CrossingState.TRAIN_PASSING,
        entry_timestamp=0.0,
        timestamp=1.0,
    )

    filtered = mitigation.filter_tracks(
        [train_state, truck_state],
        frame_width=640,
        frame_height=480,
        timestamp=1.0,
    )

    # Truck should be suppressed, only train retained
    assert len(filtered) == 1
    assert filtered[0].track_id == 1
    assert len(mitigation.suppression_history) == 1
    record = mitigation.suppression_history[0]
    assert record.track_id == 2
    assert "overlaps identified train bbox" in record.reason


def test_vehicle_not_suppressed_when_no_train():
    mitigation = TrainMisclassificationMitigation(enabled=True)

    # Real vehicle stopped on track during OPEN state
    car_state = TrackSceneState(
        track_id=3,
        rule_class=RuleClass.VEHICLE,
        bbox=BoundingBox(200, 200, 300, 280),
        zone=None,
        zone_type=ZoneType.DANGER_TRACK,
        dwell_seconds=2.0,
        movement_status=MovementStatus.STATIONARY,
        crossing_state=CrossingState.OPEN,
        entry_timestamp=0.0,
        timestamp=2.0,
    )

    filtered = mitigation.filter_tracks([car_state], frame_width=640, frame_height=480, timestamp=2.0)
    assert len(filtered) == 1
    assert filtered[0].track_id == 3
    assert len(mitigation.suppression_history) == 0

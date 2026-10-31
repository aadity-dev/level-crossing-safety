"""Unit tests for safety zones, dwell time, and kinematic movement."""

import pytest
from level_crossing.common.types import BoundingBox, Point2D, ZoneType, MovementStatus
from level_crossing.common.config import ZoneConfig
from level_crossing.scene_state.zone import Zone
from level_crossing.scene_state.zone_membership import ZoneMembershipEvaluator
from level_crossing.scene_state.dwell_tracker import DwellTracker
from level_crossing.scene_state.movement_analyzer import MovementAnalyzer
from level_crossing.tracking.track import Track, RuleClass


def test_zone_membership_bottom_center():
    cfg = ZoneConfig(
        id="z1",
        name="Danger Zone",
        zone_type=ZoneType.DANGER_TRACK,
        description="Tracks",
        polygon=[[0.2, 0.4], [0.8, 0.4], [0.8, 0.8], [0.2, 0.8]],
    )
    zone = Zone(cfg)
    evaluator = ZoneMembershipEvaluator([zone], hysteresis_normalized=0.01)

    # Box bottom-center is at (x=300, y=360) in a 600x600 image -> norm (0.5, 0.6) inside zone
    box_inside = BoundingBox(x1=250, y1=200, x2=350, y2=360)
    matched = evaluator.evaluate(box_inside, frame_width=600, frame_height=600)
    assert matched is not None
    assert matched.id == "z1"

    # Box bottom-center at (x=300, y=100) -> norm (0.5, 0.16) outside zone
    box_outside = BoundingBox(x1=250, y1=20, x2=350, y2=100)
    matched_out = evaluator.evaluate(box_outside, frame_width=600, frame_height=600)
    assert matched_out is None


def test_dwell_timer_progression_and_reset():
    dwell = DwellTracker()

    # t=1.0s enters z1
    d1 = dwell.update(track_id=1, current_zone_id="z1", timestamp=1.0)
    assert d1 == 0.0

    # t=2.5s still in z1
    d2 = dwell.update(track_id=1, current_zone_id="z1", timestamp=2.5)
    assert abs(d2 - 1.5) < 1e-4

    # t=3.0s exits zone (current_zone_id=None)
    d3 = dwell.update(track_id=1, current_zone_id=None, timestamp=3.0)
    assert d3 == 0.0
    assert dwell.get_dwell(track_id=1) == 0.0


def test_movement_analyzer():
    analyzer = MovementAnalyzer(stationary_speed_px_per_sec=10.0, slow_speed_px_per_sec=50.0)

    track = Track(
        track_id=1,
        initial_bbox=BoundingBox(0, 0, 10, 10),
        rule_class=RuleClass.PERSON,
        raw_class_name="person",
        confidence=0.9,
        first_seen_time=0.0,
        last_seen_time=0.0,
        first_frame=0,
        last_frame=0,
    )

    track.velocity_xy = Point2D(x=2.0, y=2.0)
    assert analyzer.analyze(track) == MovementStatus.STATIONARY

    track.velocity_xy = Point2D(x=20.0, y=10.0)
    assert analyzer.analyze(track) == MovementStatus.SLOW

    track.velocity_xy = Point2D(x=60.0, y=60.0)
    assert analyzer.analyze(track) == MovementStatus.FAST

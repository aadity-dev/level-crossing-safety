"""Unit tests for multi-object tracking, IoU calculation, and lifecycle states."""

import pytest
from level_crossing.common.types import BoundingBox, RuleClass
from level_crossing.detection.detection_result import DetectionResult
from level_crossing.tracking.track import TrackState
from level_crossing.tracking.tracker import ByteTracker, compute_iou


def test_compute_iou():
    boxA = BoundingBox(x1=0, y1=0, x2=10, y2=10)  # Area 100
    boxB = BoundingBox(x1=5, y1=0, x2=15, y2=10)  # Area 100, Inter: 5x10=50
    # Union = 100 + 100 - 50 = 150 -> IoU = 50 / 150 = 1/3
    assert abs(compute_iou(boxA, boxB) - (1.0 / 3.0)) < 1e-5

    boxC = BoundingBox(x1=20, y1=20, x2=30, y2=30)  # Disjoint
    assert compute_iou(boxA, boxC) == 0.0


def test_tracker_lifecycle_and_confirmation():
    tracker = ByteTracker(iou_threshold=0.3, max_lost_frames=5)

    det1 = DetectionResult(
        bbox=BoundingBox(x1=10, y1=10, x2=30, y2=50),
        confidence=0.8,
        raw_class_name="person",
        rule_class=RuleClass.PERSON,
    )

    # Frame 0: Track initialized as TENTATIVE
    active0 = tracker.update([det1], frame_idx=0, timestamp=0.0)
    assert len(active0) == 1
    t0 = active0[0]
    assert t0.track_id == 1
    assert t0.state == TrackState.TENTATIVE

    # Frame 1: Matched -> becomes CONFIRMED
    det2 = DetectionResult(
        bbox=BoundingBox(x1=12, y1=10, x2=32, y2=50),
        confidence=0.85,
        raw_class_name="person",
        rule_class=RuleClass.PERSON,
    )
    active1 = tracker.update([det2], frame_idx=1, timestamp=0.033)
    assert len(active1) == 1
    assert active1[0].track_id == 1
    assert active1[0].state == TrackState.CONFIRMED


def test_track_loss_grace_and_recovery():
    tracker = ByteTracker(iou_threshold=0.3, max_lost_frames=3)

    det = DetectionResult(
        bbox=BoundingBox(x1=50, y1=50, x2=100, y2=150),
        confidence=0.9,
        raw_class_name="person",
        rule_class=RuleClass.PERSON,
    )
    tracker.update([det], frame_idx=0, timestamp=0.0)
    tracker.update([det], frame_idx=1, timestamp=0.033)

    # Miss frame 2: enters LOST state
    tracker.update([], frame_idx=2, timestamp=0.066)
    assert tracker.tracks[1].state == TrackState.LOST

    # Recover frame 3: returns to CONFIRMED
    tracker.update([det], frame_idx=3, timestamp=0.099)
    assert tracker.tracks[1].state == TrackState.CONFIRMED

    # Miss 4 frames (exceeds max_lost_frames=3) -> enters DELETED
    tracker.update([], frame_idx=4, timestamp=0.132)
    tracker.update([], frame_idx=5, timestamp=0.165)
    tracker.update([], frame_idx=6, timestamp=0.198)
    tracker.update([], frame_idx=7, timestamp=0.231)
    assert tracker.tracks[1].state == TrackState.DELETED

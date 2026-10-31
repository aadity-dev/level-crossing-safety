"""Unit tests for the visual train optical approach estimator."""

import pytest
from level_crossing.detection.train_approach_estimator import TrainApproachEstimator
from level_crossing.detection.detection_result import DetectionResult
from level_crossing.common.types import RuleClass, BoundingBox, CrossingState


def test_train_looming_approach_detected():
    estimator = TrainApproachEstimator()

    for i in range(8):
        t = i * 0.1
        w = 60 + i * 8
        h = 100 + i * 10
        x1, y1 = 150, 80 + i * 12
        bbox = BoundingBox(x1, y1, x1 + w, y1 + h)
        det = DetectionResult(bbox=bbox, confidence=0.95, raw_class_name="train", rule_class=RuleClass.TRAIN)
        status = estimator.update([det], timestamp=t)

    assert status.is_train_detected is True
    assert status.is_approaching is True
    assert status.estimated_crossing_state == CrossingState.TRAIN_APPROACHING
    assert status.expansion_rate > 0.05


def test_train_receding_departing_detected():
    estimator = TrainApproachEstimator()

    # Train shrinking as it departs into distance
    for i in range(8):
        t = i * 0.1
        w = max(20, 120 - i * 8)
        h = max(30, 180 - i * 12)
        x1, y1 = 150, max(20, 150 - i * 10)
        bbox = BoundingBox(x1, y1, x1 + w, y1 + h)
        det = DetectionResult(bbox=bbox, confidence=0.95, raw_class_name="train", rule_class=RuleClass.TRAIN)
        status = estimator.update([det], timestamp=t)

    assert status.is_train_detected is True
    assert status.is_approaching is False
    assert status.estimated_crossing_state == CrossingState.OPEN
    assert status.expansion_rate < 0.0


def test_no_train_in_frame():
    estimator = TrainApproachEstimator()
    status = estimator.update([], timestamp=0.5)
    assert status.is_train_detected is False
    assert status.is_approaching is False
    assert status.estimated_crossing_state == CrossingState.OPEN

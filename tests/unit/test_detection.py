"""Unit tests for detection results, class mapping, and filtering."""

import pytest
from level_crossing.common.types import BoundingBox, Point2D, RuleClass
from level_crossing.detection.class_mapping import ClassMapper
from level_crossing.detection.detection_result import DetectionResult
from level_crossing.detection.detector import MockDetector


def test_class_mapper():
    mapper = ClassMapper()
    assert mapper.map_class("person") == RuleClass.PERSON
    assert mapper.map_class("pedestrian") == RuleClass.PERSON
    assert mapper.map_class("car") == RuleClass.VEHICLE
    assert mapper.map_class("truck") == RuleClass.VEHICLE
    assert mapper.map_class("bus") == RuleClass.VEHICLE
    assert mapper.map_class("bicycle") == RuleClass.BICYCLE
    assert mapper.map_class("motorcycle") == RuleClass.BICYCLE
    assert mapper.map_class("train") == RuleClass.TRAIN
    assert mapper.map_class("dog") == RuleClass.UNKNOWN


def test_detection_result_reference_point():
    bbox = BoundingBox(x1=100.0, y1=100.0, x2=200.0, y2=300.0)
    det = DetectionResult(
        bbox=bbox,
        confidence=0.85,
        raw_class_name="person",
        rule_class=RuleClass.PERSON,
    )
    # Bottom center reference point: x=(100+200)/2 = 150, y=300
    assert det.bottom_center == Point2D(x=150.0, y=300.0)


def test_detection_result_invalid_confidence():
    with pytest.raises(ValueError):
        DetectionResult(
            bbox=BoundingBox(x1=0, y1=0, x2=10, y2=10),
            confidence=1.5,
            raw_class_name="person",
            rule_class=RuleClass.PERSON,
        )


def test_detection_result_invalid_bbox():
    with pytest.raises(ValueError):
        DetectionResult(
            bbox=BoundingBox(x1=50, y1=50, x2=20, y2=40),  # x2 < x1
            confidence=0.8,
            raw_class_name="person",
            rule_class=RuleClass.PERSON,
        )

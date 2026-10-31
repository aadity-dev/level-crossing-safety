"""Detection package exports."""

from level_crossing.detection.class_mapping import ClassMapper, COCO_TO_RULE_CLASS
from level_crossing.detection.detection_result import DetectionResult, FrameDetections
from level_crossing.detection.detector import BaseDetector, YOLOv8Detector, MockDetector

__all__ = [
    "ClassMapper",
    "COCO_TO_RULE_CLASS",
    "DetectionResult",
    "FrameDetections",
    "BaseDetector",
    "YOLOv8Detector",
    "MockDetector",
]

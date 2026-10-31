"""Structured detection representations with coordinate validation."""

from dataclasses import dataclass
from typing import List, Tuple
from level_crossing.common.types import BoundingBox, Point2D, RuleClass


@dataclass(frozen=True)
class DetectionResult:
    """A single object detection candidate."""
    bbox: BoundingBox
    confidence: float
    raw_class_name: str
    rule_class: RuleClass
    raw_class_id: int = -1

    def __post_init__(self):
        if not (0.0 <= self.confidence <= 1.0):
            raise ValueError(f"Confidence must be in [0.0, 1.0], got {self.confidence}")
        if self.bbox.x2 < self.bbox.x1 or self.bbox.y2 < self.bbox.y1:
            raise ValueError(f"Invalid bounding box coordinates: {self.bbox}")

    @property
    def bottom_center(self) -> Point2D:
        return self.bbox.bottom_center

    @property
    def center(self) -> Point2D:
        return self.bbox.center


@dataclass
class FrameDetections:
    """Collection of detections for a single video frame."""
    frame_idx: int
    timestamp_sec: float
    detections: List[DetectionResult]
    inference_time_ms: float = 0.0

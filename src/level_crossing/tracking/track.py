"""Track representation decoupling object identification from spatial zones and safety decisions."""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional
import numpy as np

from level_crossing.common.types import BoundingBox, Point2D, RuleClass


class TrackState(str, Enum):
    TENTATIVE = "TENTATIVE"
    CONFIRMED = "CONFIRMED"
    LOST = "LOST"
    DELETED = "DELETED"


@dataclass
class Track:
    """Individual object track identity and spatial trajectory."""
    track_id: int
    initial_bbox: BoundingBox
    rule_class: RuleClass
    raw_class_name: str
    confidence: float
    first_seen_time: float
    last_seen_time: float
    first_frame: int
    last_frame: int

    current_bbox: BoundingBox = field(init=False)
    bbox_history: List[BoundingBox] = field(default_factory=list)
    timestamps: List[float] = field(default_factory=list)
    state: TrackState = TrackState.TENTATIVE
    hits: int = 1
    missed_frames: int = 0
    velocity_xy: Point2D = field(default_factory=lambda: Point2D(0.0, 0.0))

    def __post_init__(self):
        self.current_bbox = self.initial_bbox
        self.bbox_history.append(self.initial_bbox)
        self.timestamps.append(self.first_seen_time)

    @property
    def lifetime_seconds(self) -> float:
        return max(0.0, self.last_seen_time - self.first_seen_time)

    @property
    def reference_point(self) -> Point2D:
        """Bottom-center reference point for ground-plane zone intersection."""
        return self.current_bbox.bottom_center

    def update(self, detection_bbox: BoundingBox, confidence: float, frame_idx: int, timestamp: float) -> None:
        """Updates track with a new matched detection."""
        # Calculate instantaneous velocity (pixels/sec)
        dt = timestamp - self.last_seen_time
        if dt > 0.001:
            p_old = self.current_bbox.bottom_center
            p_new = detection_bbox.bottom_center
            vx = (p_new.x - p_old.x) / dt
            vy = (p_new.y - p_old.y) / dt
            # Exponential smoothing
            self.velocity_xy = Point2D(
                x=0.7 * self.velocity_xy.x + 0.3 * vx,
                y=0.7 * self.velocity_xy.y + 0.3 * vy,
            )

        self.current_bbox = detection_bbox
        self.bbox_history.append(detection_bbox)
        self.timestamps.append(timestamp)
        self.confidence = confidence
        self.last_seen_time = timestamp
        self.last_frame = frame_idx
        self.hits += 1
        self.missed_frames = 0

        if self.state == TrackState.TENTATIVE and self.hits >= 2:
            self.state = TrackState.CONFIRMED
        elif self.state == TrackState.LOST:
            self.state = TrackState.CONFIRMED

    def mark_missed(self, frame_idx: int, max_lost_frames: int) -> None:
        """Increments missed frames count during occlusion/missed detection."""
        self.missed_frames += 1
        if self.missed_frames > max_lost_frames:
            self.state = TrackState.DELETED
        else:
            self.state = TrackState.LOST

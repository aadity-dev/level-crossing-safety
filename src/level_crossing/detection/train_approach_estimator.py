"""Visual Train Optical Approach Estimator (Perspective Looming Analysis).

Infer crossing state dynamically for unmanned rural crossings without electrical track circuits.
Evaluates perspective expansion (dA/dt) and motion trajectory of approaching locomotives.
"""

from dataclasses import dataclass
from collections import deque
from typing import List, Optional, Tuple, Dict, Any
import numpy as np

from level_crossing.common.types import CrossingState, RuleClass
from level_crossing.common.logger import get_logger

logger = get_logger("train_approach_estimator")


@dataclass
class TrainApproachStatus:
    """State output from the visual train approach estimator."""
    is_train_detected: bool
    is_approaching: bool
    expansion_rate: float            # Relative area growth per second (dA / (A * dt))
    estimated_crossing_state: CrossingState
    confidence: float
    optical_velocity_y: float        # Vertical motion towards crossing (pixels/sec)
    history_window_seconds: float
    description: str


class TrainApproachEstimator:
    """Estimates whether an approaching locomotive is closing distance to the level crossing.
    
    Physics & Optics:
    Under perspective projection, as a train at distance Z(t) approaches the camera, its visual
    bounding box area A(t) grows inversely with distance squared: A(t) ~ 1 / Z(t)^2.
    Therefore, an approaching train exhibits a positive area expansion rate: dA/dt > 0.
    A departing/receding train exhibits dA/dt < 0.
    A stopped/distant train exhibits dA/dt ~ 0.
    """

    def __init__(
        self,
        min_expansion_rate: float = 0.03,      # Min 3% area growth per second to trigger approach
        window_seconds: float = 1.0,           # Sliding temporal estimation window
        min_observation_frames: int = 5,       # Minimum required observations
        receding_threshold: float = -0.03,     # Negative threshold indicating departure
    ):
        self.min_expansion_rate = min_expansion_rate
        self.window_seconds = window_seconds
        self.min_observation_frames = min_observation_frames
        self.receding_threshold = receding_threshold
        # Sliding buffer of (timestamp, bbox_area, center_x, center_y, bbox)
        self.history = deque()
        self.last_approaching_time = 0.0
        self.hold_time_sec = 3.0               # Maintain APPROACHING state for at least 3s once triggered

    def update(
        self,
        detections: List[Any],
        timestamp: float,
    ) -> TrainApproachStatus:
        """Processes current frame detections and estimates locomotive approach status."""
        # Find train detection with highest confidence
        train_det = None
        for det in detections:
            rule_cls = getattr(det, "rule_class", None)
            if rule_cls == RuleClass.TRAIN:
                if train_det is None or det.confidence > train_det.confidence:
                    train_det = det

        # Prune old history outside temporal sliding window
        while self.history and (timestamp - self.history[0][0]) > self.window_seconds:
            self.history.popleft()

        if train_det is None:
            # If train was recently confirmed approaching within hold window, retain alert state
            if (timestamp - self.last_approaching_time) < self.hold_time_sec and self.last_approaching_time > 0:
                return TrainApproachStatus(
                    is_train_detected=False,
                    is_approaching=True,
                    expansion_rate=0.0,
                    estimated_crossing_state=CrossingState.TRAIN_APPROACHING,
                    confidence=0.85,
                    optical_velocity_y=0.0,
                    history_window_seconds=0.0,
                    description="Autonomous visual hold: Locomotive recently confirmed on track trajectory",
                )

            return TrainApproachStatus(
                is_train_detected=False,
                is_approaching=False,
                expansion_rate=0.0,
                estimated_crossing_state=CrossingState.OPEN,
                confidence=1.0,
                optical_velocity_y=0.0,
                history_window_seconds=0.0,
                description="No locomotive detected on rail trajectory",
            )

        # Extract geometric properties
        bbox = train_det.bbox
        area = float(bbox.area)
        cx = (bbox.x1 + bbox.x2) / 2.0
        cy = (bbox.y1 + bbox.y2) / 2.0

        self.history.append((timestamp, area, cx, cy, bbox))

        if len(self.history) < self.min_observation_frames:
            return TrainApproachStatus(
                is_train_detected=True,
                is_approaching=False,
                expansion_rate=0.0,
                estimated_crossing_state=CrossingState.OPEN,
                confidence=0.5,
                optical_velocity_y=0.0,
                history_window_seconds=timestamp - self.history[0][0],
                description=f"Accumulating optical baseline ({len(self.history)}/{self.min_observation_frames} frames)",
            )

        # Compute relative area expansion rate dA / (A * dt) using linear regression over window
        times = np.array([h[0] for h in self.history], dtype=np.float64)
        areas = np.array([h[1] for h in self.history], dtype=np.float64)
        cys = np.array([h[3] for h in self.history], dtype=np.float64)

        dt = times[-1] - times[0]
        if dt <= 0.001:
            return TrainApproachStatus(
                is_train_detected=True,
                is_approaching=False,
                expansion_rate=0.0,
                estimated_crossing_state=CrossingState.OPEN,
                confidence=0.5,
                optical_velocity_y=0.0,
                history_window_seconds=dt,
                description="Insufficient temporal baseline",
            )

        # Relative change
        area_baseline = np.mean(areas[:3])
        delta_area = areas[-1] - areas[0]
        relative_expansion_rate = float((delta_area / area_baseline) / dt)

        # Vertical velocity towards crossing (positive = moving down towards camera/crossing)
        delta_cy = cys[-1] - cys[0]
        velocity_y = float(delta_cy / dt)

        # Looming conditions: Area expanding OR significant downward motion along tracks
        is_looming = (relative_expansion_rate >= self.min_expansion_rate) or (velocity_y > 15.0 and relative_expansion_rate > -0.01)
        is_receding = relative_expansion_rate <= self.receding_threshold and velocity_y < -5.0

        if is_looming:
            self.last_approaching_time = timestamp
            state = CrossingState.TRAIN_APPROACHING
            confidence = float(np.clip(0.6 + relative_expansion_rate * 2.0, 0.65, 0.98))
            desc = f"LOOMING DETECTED: Locomotive expanding at {relative_expansion_rate*100:+.1f}%/s (Vy: {velocity_y:+.1f}px/s)"
        elif is_receding:
            state = CrossingState.OPEN
            confidence = 0.85
            desc = f"RECEDING: Locomotive departing crossing at {relative_expansion_rate*100:+.1f}%/s"
        else:
            state = CrossingState.TRAIN_PASSING if area > 0.3 * (self.history[0][4].x2 * 2 * self.history[0][4].y2 * 2) else CrossingState.OPEN
            confidence = 0.75
            desc = f"STATIONARY / STEADY: Expansion rate {relative_expansion_rate*100:+.1f}%/s within baseline"

        return TrainApproachStatus(
            is_train_detected=True,
            is_approaching=is_looming,
            expansion_rate=round(relative_expansion_rate, 4),
            estimated_crossing_state=state,
            confidence=round(confidence, 2),
            optical_velocity_y=round(velocity_y, 1),
            history_window_seconds=round(dt, 2),
            description=desc,
        )

    def reset(self) -> None:
        """Resets sliding window buffer."""
        self.history.clear()
        self.last_approaching_time = 0.0

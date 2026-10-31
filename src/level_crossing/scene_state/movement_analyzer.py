"""Movement and kinematic state analysis for tracked objects."""

import math
from typing import Optional
from level_crossing.common.types import MovementStatus, Point2D
from level_crossing.tracking.track import Track


class MovementAnalyzer:
    """Analyzes object velocity vectors and classifies motion state."""

    def __init__(self, stationary_speed_px_per_sec: float = 15.0, slow_speed_px_per_sec: float = 80.0):
        self.stationary_thresh = stationary_speed_px_per_sec
        self.slow_thresh = slow_speed_px_per_sec

    def analyze(self, track: Track) -> MovementStatus:
        """Determines movement status from smoothed velocity."""
        vx = track.velocity_xy.x
        vy = track.velocity_xy.y
        speed = math.sqrt(vx * vx + vy * vy)

        if speed < self.stationary_thresh:
            return MovementStatus.STATIONARY
        elif speed < self.slow_thresh:
            return MovementStatus.SLOW
        else:
            return MovementStatus.FAST

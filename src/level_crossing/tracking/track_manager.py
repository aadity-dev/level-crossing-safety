"""Track lifecycle manager providing safe queries and persistence snapshots."""

from typing import List, Dict, Optional
from level_crossing.tracking.track import Track, TrackState
from level_crossing.tracking.tracker import ByteTracker
from level_crossing.detection.detection_result import DetectionResult


class TrackManager:
    """Encapsulates tracking execution and lifecycle queries."""

    def __init__(self, tracker: Optional[ByteTracker] = None):
        self.tracker = tracker or ByteTracker()

    def step(self, detections: List[DetectionResult], frame_idx: int, timestamp: float) -> List[Track]:
        return self.tracker.update(detections, frame_idx, timestamp)

    def get_track(self, track_id: int) -> Optional[Track]:
        return self.tracker.tracks.get(track_id)

    @property
    def all_tracks(self) -> Dict[int, Track]:
        return self.tracker.tracks

    def reset(self) -> None:
        self.tracker.reset()

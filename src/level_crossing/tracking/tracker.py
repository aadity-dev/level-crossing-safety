"""High-performance multi-object association and tracking engine."""

from typing import List, Tuple, Dict, Optional
import numpy as np

from level_crossing.common.types import BoundingBox, RuleClass
from level_crossing.common.logger import get_logger
from level_crossing.detection.detection_result import DetectionResult
from level_crossing.tracking.track import Track, TrackState

logger = get_logger("tracker")


def compute_iou(boxA: BoundingBox, boxB: BoundingBox) -> float:
    """Computes Intersection over Union (IoU) between two bounding boxes."""
    xA = max(boxA.x1, boxB.x1)
    yA = max(boxA.y1, boxB.y1)
    xB = min(boxA.x2, boxB.x2)
    yB = min(boxA.y2, boxB.y2)

    inter_width = max(0.0, xB - xA)
    inter_height = max(0.0, yB - yA)
    inter_area = inter_width * inter_height

    boxA_area = boxA.area
    boxB_area = boxB.area
    union_area = boxA_area + boxB_area - inter_area

    if union_area <= 0.0:
        return 0.0
    return inter_area / union_area


class ByteTracker:
    """Multi-object tracker with track identity, history, and graceful occlusion recovery."""

    def __init__(self, iou_threshold: float = 0.30, max_lost_frames: int = 30):
        self.iou_threshold = iou_threshold
        self.max_lost_frames = max_lost_frames
        self._next_id: int = 1
        self.tracks: Dict[int, Track] = {}

    def update(self, detections: List[DetectionResult], frame_idx: int, timestamp: float) -> List[Track]:
        """Associates incoming detections with existing tracks and updates track states."""
        active_track_ids = [
            tid for tid, t in self.tracks.items() if t.state in (TrackState.CONFIRMED, TrackState.TENTATIVE, TrackState.LOST)
        ]

        # Compute IoU matrix
        iou_matrix = np.zeros((len(active_track_ids), len(detections)), dtype=np.float32)
        for i, tid in enumerate(active_track_ids):
            track_box = self.tracks[tid].current_bbox
            for j, det in enumerate(detections):
                # Only match same rule class (e.g. Person with Person)
                if self.tracks[tid].rule_class == det.rule_class:
                    iou_matrix[i, j] = compute_iou(track_box, det.bbox)
                else:
                    iou_matrix[i, j] = 0.0

        matched_tracks = set()
        matched_dets = set()

        if len(active_track_ids) > 0 and len(detections) > 0:
            # Greedy bipartite matching
            while True:
                max_val = np.max(iou_matrix)
                if max_val < self.iou_threshold:
                    break
                row, col = np.unravel_index(np.argmax(iou_matrix), iou_matrix.shape)
                if row in matched_tracks or col in matched_dets:
                    iou_matrix[row, col] = 0.0
                    continue

                matched_tracks.add(row)
                matched_dets.add(col)
                tid = active_track_ids[row]
                det = detections[col]
                self.tracks[tid].update(det.bbox, det.confidence, frame_idx, timestamp)
                iou_matrix[row, :] = 0.0
                iou_matrix[:, col] = 0.0

        # Mark unmatched active tracks as missed
        for i, tid in enumerate(active_track_ids):
            if i not in matched_tracks:
                self.tracks[tid].mark_missed(frame_idx, self.max_lost_frames)

        # Create new tracks for unmatched detections
        for j, det in enumerate(detections):
            if j not in matched_dets:
                new_track = Track(
                    track_id=self._next_id,
                    initial_bbox=det.bbox,
                    rule_class=det.rule_class,
                    raw_class_name=det.raw_class_name,
                    confidence=det.confidence,
                    first_seen_time=timestamp,
                    last_seen_time=timestamp,
                    first_frame=frame_idx,
                    last_frame=frame_idx,
                )
                self.tracks[self._next_id] = new_track
                self._next_id += 1

        # Return active tracks
        return [
            t for t in self.tracks.values()
            if t.state in (TrackState.CONFIRMED, TrackState.TENTATIVE)
        ]

    def reset(self) -> None:
        self.tracks.clear()
        self._next_id = 1

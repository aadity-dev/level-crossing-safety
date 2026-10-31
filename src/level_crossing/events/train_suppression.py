"""Mitigation for train misclassification during active train states."""

from dataclasses import dataclass
from typing import List, Tuple, Set
from level_crossing.common.types import CrossingState, RuleClass, BoundingBox
from level_crossing.common.logger import get_logger
from level_crossing.tracking.tracker import compute_iou
from level_crossing.scene_state.zone_manager import TrackSceneState

logger = get_logger("train_suppression")


@dataclass
class SuppressionRecord:
    track_id: int
    rule_class: RuleClass
    reason: str
    timestamp: float
    bbox: BoundingBox


class TrainMisclassificationMitigation:
    """Detects and suppresses suspected train cars misclassified as truck/bus during train movements."""

    def __init__(
        self,
        enabled: bool = True,
        overlap_iou_threshold: float = 0.25,
        area_ratio_threshold: float = 0.35,
    ):
        self.enabled = enabled
        self.overlap_iou_threshold = overlap_iou_threshold
        self.area_ratio_threshold = area_ratio_threshold
        self.suppression_history: List[SuppressionRecord] = []

    def filter_tracks(
        self,
        track_states: List[TrackSceneState],
        frame_width: int,
        frame_height: int,
        timestamp: float,
    ) -> List[TrackSceneState]:
        """Filters out suppressed tracks and audits every single decision."""
        if not self.enabled or not track_states:
            return track_states

        crossing_state = track_states[0].crossing_state
        # Only active during train transit states
        if crossing_state not in (CrossingState.TRAIN_APPROACHING, CrossingState.TRAIN_PASSING):
            return track_states

        frame_area = float(frame_width * frame_height)
        train_boxes = [ts.bbox for ts in track_states if ts.rule_class == RuleClass.TRAIN]

        filtered: List[TrackSceneState] = []
        for ts in track_states:
            if ts.rule_class != RuleClass.VEHICLE:
                filtered.append(ts)
                continue

            suppress = False
            reason = ""

            # Check 1: Overlap with identified train bbox
            for t_box in train_boxes:
                iou = compute_iou(ts.bbox, t_box)
                if iou >= self.overlap_iou_threshold:
                    suppress = True
                    reason = f"Vehicle overlaps identified train bbox (IoU={iou:.2f} >= {self.overlap_iou_threshold})"
                    break

            # Check 2: Oversized vehicle occupying rail zone during approaching/passing
            if not suppress:
                area_ratio = ts.bbox.area / frame_area
                if area_ratio >= self.area_ratio_threshold:
                    suppress = True
                    reason = f"Oversized vehicle bbox (area ratio {area_ratio:.2f} >= {self.area_ratio_threshold}) during {crossing_state.value}"

            if suppress:
                rec = SuppressionRecord(
                    track_id=ts.track_id,
                    rule_class=ts.rule_class,
                    reason=reason,
                    timestamp=timestamp,
                    bbox=ts.bbox,
                )
                self.suppression_history.append(rec)
                logger.info(
                    f"AUDIT SUPPRESSION: Track {ts.track_id} ({ts.rule_class.value}) suppressed. Reason: {reason}"
                )
            else:
                filtered.append(ts)

        return filtered

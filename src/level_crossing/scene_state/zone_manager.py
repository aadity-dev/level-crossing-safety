"""Scene state manager coordinating zones, dwell tracking, and movement analysis."""

from dataclasses import dataclass
from typing import List, Dict, Optional, Any
from level_crossing.common.types import (
    CrossingState,
    ZoneType,
    RuleClass,
    MovementStatus,
    BoundingBox,
    Point2D,
)
from level_crossing.common.config import ZonesFileConfig
from level_crossing.scene_state.zone import Zone
from level_crossing.scene_state.zone_membership import ZoneMembershipEvaluator
from level_crossing.scene_state.dwell_tracker import DwellTracker
from level_crossing.scene_state.movement_analyzer import MovementAnalyzer
from level_crossing.tracking.track import Track


@dataclass
class TrackSceneState:
    """Rich contextual scene state for a tracked entity."""
    track_id: int
    rule_class: RuleClass
    bbox: BoundingBox
    zone: Optional[Zone]
    zone_type: Optional[ZoneType]
    dwell_seconds: float
    movement_status: MovementStatus
    crossing_state: CrossingState
    entry_timestamp: Optional[float]
    timestamp: float
    confidence: float = 0.0


class ZoneManager:
    """Manages crossing zones and computes track scene states."""

    def __init__(self, config: ZonesFileConfig, hysteresis_normalized: float = 0.015):
        self.zones: List[Zone] = [Zone(zc) for zc in config.zones]
        self.membership_evaluator = ZoneMembershipEvaluator(self.zones, hysteresis_normalized)
        self.dwell_tracker = DwellTracker()
        self.movement_analyzer = MovementAnalyzer()
        self._prev_track_zones: Dict[int, Zone] = {}

    def evaluate_tracks(
        self,
        tracks: List[Track],
        crossing_state: CrossingState,
        frame_width: int,
        frame_height: int,
        timestamp: float,
    ) -> List[TrackSceneState]:
        """Evaluates scene state for all active tracks in the frame."""
        states: List[TrackSceneState] = []

        for track in tracks:
            prev_zone = self._prev_track_zones.get(track.track_id)
            current_zone = self.membership_evaluator.evaluate(
                track.current_bbox, frame_width, frame_height, prev_zone
            )

            if current_zone:
                self._prev_track_zones[track.track_id] = current_zone
                zone_id = current_zone.id
                zone_type = current_zone.zone_type
            else:
                self._prev_track_zones.pop(track.track_id, None)
                zone_id = None
                zone_type = None

            dwell_sec = self.dwell_tracker.update(track.track_id, zone_id, timestamp)
            entry_time = self.dwell_tracker.get_entry_time(track.track_id)
            movement = self.movement_analyzer.analyze(track)

            states.append(
                TrackSceneState(
                    track_id=track.track_id,
                    rule_class=track.rule_class,
                    bbox=track.current_bbox,
                    zone=current_zone,
                    zone_type=zone_type,
                    dwell_seconds=dwell_sec,
                    movement_status=movement,
                    crossing_state=crossing_state,
                    entry_timestamp=entry_time,
                    timestamp=timestamp,
                    confidence=track.confidence,
                )
            )

        return states

    def reset(self) -> None:
        self.dwell_tracker.reset()
        self._prev_track_zones.clear()

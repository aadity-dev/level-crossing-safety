"""Stateless contextual severity evaluator component."""

from typing import List, Dict, Optional
from level_crossing.common.types import SeverityLevel
from level_crossing.severity.matrix import SeverityMatrix
from level_crossing.scene_state.zone_manager import TrackSceneState


class SeverityEvaluator:
    """Evaluates contextual risk for tracks in a purely stateless manner."""

    def __init__(self, matrix: SeverityMatrix):
        self.matrix = matrix

    def evaluate_track(self, scene_state: TrackSceneState) -> SeverityLevel:
        """Computes stateless severity for a single track's scene state."""
        return self.matrix.lookup(
            crossing_state=scene_state.crossing_state,
            zone_type=scene_state.zone_type,
            rule_class=scene_state.rule_class,
        )

    def evaluate_all(self, track_states: List[TrackSceneState]) -> Dict[int, SeverityLevel]:
        """Evaluates severity for all tracks."""
        return {ts.track_id: self.evaluate_track(ts) for ts in track_states}

"""Evaluation package exports."""

from level_crossing.evaluation.ground_truth import GroundTruthEvent, GroundTruthDataset
from level_crossing.evaluation.matcher import EventMatcher, MatchResult, MatchingReport
from level_crossing.evaluation.metrics import SafetySystemMetrics, compute_safety_metrics
from level_crossing.evaluation.ablation import AblationStudyRunner

__all__ = [
    "GroundTruthEvent",
    "GroundTruthDataset",
    "EventMatcher",
    "MatchResult",
    "MatchingReport",
    "SafetySystemMetrics",
    "compute_safety_metrics",
    "AblationStudyRunner",
]

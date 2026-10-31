"""One-to-one event matching and latency benchmarking engine."""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Set
import numpy as np

from level_crossing.common.types import RuleClass
from level_crossing.evaluation.ground_truth import GroundTruthEvent
from level_crossing.events.event import SafetyEvent
from level_crossing.alerts.alert import AlertRecord


@dataclass
class MatchResult:
    gt_event: GroundTruthEvent
    predicted_event: SafetyEvent
    first_alert: Optional[AlertRecord]
    decision_latency_sec: float     # alert_video_time - gt_event_start_time
    temporal_overlap_sec: float


@dataclass
class MatchingReport:
    true_positives: int
    false_positives: int
    false_negatives: int
    matched_pairs: List[MatchResult]
    unmatched_predictions: List[SafetyEvent]
    missed_ground_truths: List[GroundTruthEvent]
    fragmentation_count: int        # Single GT matched by multiple predictions
    merge_count: int                # Single prediction matching multiple GTs
    decision_latencies: List[float]


class EventMatcher:
    """Rigorous 1-to-1 temporal event matcher adhering to V3.1 specification."""

    def __init__(self, tolerance_seconds: float = 2.0):
        self.tolerance = tolerance_seconds

    def match(
        self,
        ground_truth: List[GroundTruthEvent],
        predictions: List[SafetyEvent],
        alerts: List[AlertRecord],
    ) -> MatchingReport:
        """Matches predicted events against ground truth."""
        # Index alerts by event_id for fast lookup
        alerts_by_event: Dict[str, List[AlertRecord]] = {}
        for a in alerts:
            alerts_by_event.setdefault(a.event_id, []).append(a)

        # Sort alerts temporally
        for elist in alerts_by_event.values():
            elist.sort(key=lambda a: a.timestamp)

        matched_gt: Set[str] = set()
        matched_pred: Set[str] = set()
        match_results: List[MatchResult] = []
        fragmentation = 0
        merge = 0

        # Sort both lists by start time
        gt_sorted = sorted(ground_truth, key=lambda g: g.start_time)
        pred_sorted = sorted(predictions, key=lambda p: p.start_time)

        for gt in gt_sorted:
            best_candidate: Optional[SafetyEvent] = None
            best_latency_diff = float("inf")

            for pred in pred_sorted:
                if pred.event_id in matched_pred:
                    continue

                # Class compatibility check
                if pred.rule_class != gt.object_type:
                    continue

                # Temporal compatibility:
                # 1. Start time within tolerance
                start_diff = abs(pred.start_time - gt.start_time)
                # 2. Overlap interval
                overlap_start = max(gt.start_time, pred.start_time)
                overlap_end = min(gt.end_time, pred.end_time or (pred.start_time + 10.0))
                overlap_duration = max(0.0, overlap_end - overlap_start)

                if start_diff <= self.tolerance or overlap_duration > 0.5:
                    if start_diff < best_latency_diff:
                        best_candidate = pred
                        best_latency_diff = start_diff

            if best_candidate is not None:
                matched_gt.add(gt.event_id)
                matched_pred.add(best_candidate.event_id)

                event_alerts = alerts_by_event.get(best_candidate.event_id, [])
                first_alert = event_alerts[0] if event_alerts else None
                alert_time = first_alert.timestamp if first_alert else best_candidate.start_time
                decision_latency = max(0.0, alert_time - gt.start_time)

                overlap_sec = max(
                    0.0,
                    min(gt.end_time, best_candidate.end_time or (best_candidate.start_time + 10.0))
                    - max(gt.start_time, best_candidate.start_time),
                )

                match_results.append(
                    MatchResult(
                        gt_event=gt,
                        predicted_event=best_candidate,
                        first_alert=first_alert,
                        decision_latency_sec=decision_latency,
                        temporal_overlap_sec=overlap_sec,
                    )
                )

        unmatched_preds = [p for p in predictions if p.event_id not in matched_pred]
        missed_gts = [g for g in ground_truth if g.event_id not in matched_gt]

        # Check for fragmentation: unmatched preds overlapping already matched GT
        for p in unmatched_preds:
            for m in match_results:
                if p.rule_class == m.gt_event.object_type:
                    if max(p.start_time, m.gt_event.start_time) < min(p.end_time or 9999, m.gt_event.end_time):
                        fragmentation += 1
                        break

        latencies = [m.decision_latency_sec for m in match_results]

        return MatchingReport(
            true_positives=len(match_results),
            false_positives=len(unmatched_preds),
            false_negatives=len(missed_gts),
            matched_pairs=match_results,
            unmatched_predictions=unmatched_preds,
            missed_ground_truths=missed_gts,
            fragmentation_count=fragmentation,
            merge_count=merge,
            decision_latencies=latencies,
        )

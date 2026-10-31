"""Evaluation metrics computation for event recall, false alert rates, and latency."""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional
import numpy as np

from level_crossing.evaluation.matcher import MatchingReport


@dataclass
class SafetySystemMetrics:
    total_ground_truth_events: int
    true_positives: int
    false_positives: int
    false_negatives: int
    event_recall: float
    event_precision: float
    f1_score: float
    total_footage_hours: float
    false_alerts_per_hour: float
    mean_decision_latency_sec: float
    p50_decision_latency_sec: float
    p95_decision_latency_sec: float
    fragmentation_count: int
    merge_count: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_ground_truth_events": self.total_ground_truth_events,
            "true_positives": self.true_positives,
            "false_positives": self.false_positives,
            "false_negatives": self.false_negatives,
            "event_recall": round(self.event_recall, 4),
            "event_precision": round(self.event_precision, 4),
            "f1_score": round(self.f1_score, 4),
            "total_footage_hours": round(self.total_footage_hours, 4),
            "false_alerts_per_hour": round(self.false_alerts_per_hour, 2),
            "mean_decision_latency_sec": round(self.mean_decision_latency_sec, 3),
            "p50_decision_latency_sec": round(self.p50_decision_latency_sec, 3),
            "p95_decision_latency_sec": round(self.p95_decision_latency_sec, 3),
            "fragmentation_count": self.fragmentation_count,
            "merge_count": self.merge_count,
        }


def compute_safety_metrics(report: MatchingReport, footage_duration_seconds: float) -> SafetySystemMetrics:
    """Calculates comprehensive safety KPIs from match report and footage length."""
    tp = report.true_positives
    fp = report.false_positives
    fn = report.false_negatives
    total_gt = tp + fn

    recall = (tp / total_gt) if total_gt > 0 else 0.0
    precision = (tp / (tp + fp)) if (tp + fp) > 0 else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0.0

    total_hours = max(0.0001, footage_duration_seconds / 3600.0)
    fa_per_hour = fp / total_hours

    latencies = report.decision_latencies
    if latencies:
        mean_lat = float(np.mean(latencies))
        p50_lat = float(np.percentile(latencies, 50))
        p95_lat = float(np.percentile(latencies, 95))
    else:
        mean_lat = 0.0
        p50_lat = 0.0
        p95_lat = 0.0

    return SafetySystemMetrics(
        total_ground_truth_events=total_gt,
        true_positives=tp,
        false_positives=fp,
        false_negatives=fn,
        event_recall=recall,
        event_precision=precision,
        f1_score=f1,
        total_footage_hours=total_hours,
        false_alerts_per_hour=fa_per_hour,
        mean_decision_latency_sec=mean_lat,
        p50_decision_latency_sec=p50_lat,
        p95_decision_latency_sec=p95_lat,
        fragmentation_count=report.fragmentation_count,
        merge_count=report.merge_count,
    )

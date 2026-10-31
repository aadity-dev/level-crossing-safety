"""Four-way ablation study runner comparing incremental system components."""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from pathlib import Path

from level_crossing.common.config import SystemConfig
from level_crossing.common.types import CrossingState, SeverityLevel
from level_crossing.evaluation.ground_truth import GroundTruthDataset, GroundTruthEvent
from level_crossing.evaluation.matcher import EventMatcher
from level_crossing.evaluation.metrics import compute_safety_metrics, SafetySystemMetrics
from level_crossing.pipeline.replay_pipeline import ReplayPipeline
from level_crossing.detection.detector import BaseDetector, MockDetector


@dataclass
class AblationStudyResult:
    config_name: str
    description: str
    metrics: SafetySystemMetrics


class AblationStudyRunner:
    """Runs 4 ablation configurations:
    A: Raw detection + zone check
    B: Detection + tracking
    C: Detection + tracking + dwell
    D: Full production pipeline (tracking + dwell + event manager + cooldown)
    """

    def __init__(self, base_config: SystemConfig):
        self.base_config = base_config

    def run_ablation(
        self,
        video_path: str | Path,
        ground_truth_path: str | Path,
        detector: Optional[BaseDetector] = None,
        crossing_state: Optional[CrossingState] = None,
    ) -> Dict[str, SafetySystemMetrics]:
        gt_dataset = GroundTruthDataset(ground_truth_path)
        video_id = Path(video_path).stem
        gt_events = gt_dataset.get_events_for_video(video_id)
        if not gt_events:
            gt_events = gt_dataset.events  # fallback if all events in one file

        target_state = crossing_state or (gt_events[0].crossing_state if gt_events else CrossingState.OPEN)
        state_timeline = lambda t: target_state

        matcher = EventMatcher(tolerance_seconds=2.0)
        results: Dict[str, SafetySystemMetrics] = {}

        # ----------------------------------------------------
        # Config D: Full System (Benchmark)
        # ----------------------------------------------------
        cfg_d = self.base_config.model_copy(deep=True)
        pipeline_d = ReplayPipeline(config=cfg_d, detector=detector, save_to_db=False)
        summary_d = pipeline_d.run(video_path, crossing_state_timeline=state_timeline)
        preds_d = list(pipeline_d.event_manager.closed_events) + list(pipeline_d.event_manager.active_events.values())
        report_d = matcher.match(gt_events, preds_d, pipeline_d.alert_engine.alerts_history)
        results["D_full_system"] = compute_safety_metrics(report_d, summary_d.duration_seconds)

        # ----------------------------------------------------
        # Config C: No Cooldown / Immediate Alerts
        # ----------------------------------------------------
        cfg_c = self.base_config.model_copy(deep=True)
        cfg_c.thresholds.event_manager.cooldown_seconds = 0.0
        pipeline_c = ReplayPipeline(config=cfg_c, detector=detector, save_to_db=False)
        summary_c = pipeline_c.run(video_path, crossing_state_timeline=state_timeline)
        preds_c = list(pipeline_c.event_manager.closed_events) + list(pipeline_c.event_manager.active_events.values())
        report_c = matcher.match(gt_events, preds_c, pipeline_c.alert_engine.alerts_history)
        results["C_dwell_no_cooldown"] = compute_safety_metrics(report_c, summary_c.duration_seconds)

        # ----------------------------------------------------
        # Config B: No Dwell Filter (Zero Dwell Confirmation)
        # ----------------------------------------------------
        cfg_b = self.base_config.model_copy(deep=True)
        for k in cfg_b.thresholds.event_manager.confirmation_dwell_seconds:
            cfg_b.thresholds.event_manager.confirmation_dwell_seconds[k] = 0.0
        pipeline_b = ReplayPipeline(config=cfg_b, detector=detector, save_to_db=False)
        summary_b = pipeline_b.run(video_path, crossing_state_timeline=state_timeline)
        preds_b = list(pipeline_b.event_manager.closed_events) + list(pipeline_b.event_manager.active_events.values())
        report_b = matcher.match(gt_events, preds_b, pipeline_b.alert_engine.alerts_history)
        results["B_tracking_zero_dwell"] = compute_safety_metrics(report_b, summary_b.duration_seconds)

        # ----------------------------------------------------
        # Config A: Raw Detection + Zone (No tracking identity / 1-frame grace)
        # ----------------------------------------------------
        cfg_a = self.base_config.model_copy(deep=True)
        cfg_a.thresholds.tracking.max_lost_frames = 0
        for k in cfg_a.thresholds.event_manager.confirmation_dwell_seconds:
            cfg_a.thresholds.event_manager.confirmation_dwell_seconds[k] = 0.0
        pipeline_a = ReplayPipeline(config=cfg_a, detector=detector, save_to_db=False)
        summary_a = pipeline_a.run(video_path, crossing_state_timeline=state_timeline)
        preds_a = list(pipeline_a.event_manager.closed_events) + list(pipeline_a.event_manager.active_events.values())
        report_a = matcher.match(gt_events, preds_a, pipeline_a.alert_engine.alerts_history)
        results["A_raw_detection_zone"] = compute_safety_metrics(report_a, summary_a.duration_seconds)

        return results

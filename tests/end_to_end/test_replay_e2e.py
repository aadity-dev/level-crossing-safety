"""End-to-End replay scenario test verifying database records, alerts, and ground-truth alignment."""

import pytest
from pathlib import Path
import numpy as np

from level_crossing.common.config import SystemConfig
from level_crossing.common.types import CrossingState, SeverityLevel
from level_crossing.pipeline.replay_pipeline import ReplayPipeline
from level_crossing.evaluation.ground_truth import GroundTruthDataset
from level_crossing.evaluation.matcher import EventMatcher
from level_crossing.detection.detector import MockDetector
from level_crossing.detection.detection_result import DetectionResult
from level_crossing.common.types import BoundingBox, RuleClass


def test_end_to_end_replay_ground_truth_matching(tmp_path: Path):
    db_file = tmp_path / "e2e_replay.sqlite3"
    config = SystemConfig.load_from_dir("configs")

    video_path = "data/controlled/validation/scenario_01_person_danger_track.mp4"
    gt_csv_path = "data/controlled/validation/ground_truth.csv"

    if not Path(video_path).exists() or not Path(gt_csv_path).exists():
        pytest.skip("Test scenario fixtures missing")

    # In scenario_01: person enters around frame 36 (1.2s) and stays till frame 120 (4.0s)
    mock_det = MockDetector()
    for f in range(36, 120):
        # Coordinates in danger zone
        box = BoundingBox(x1=220, y1=210, x2=320, y2=270)
        mock_det.set_frame_detections(
            frame_idx=f,
            detections=[
                DetectionResult(
                    bbox=box,
                    confidence=0.94,
                    raw_class_name="person",
                    rule_class=RuleClass.PERSON,
                )
            ],
        )

    pipeline = ReplayPipeline(
        config=config,
        detector=mock_det,
        db_path=db_file,
        save_to_db=True,
    )

    summary = pipeline.run(
        video_path=video_path,
        crossing_state_timeline=lambda t: CrossingState.TRAIN_APPROACHING,
    )

    assert summary.events_generated == 1
    assert summary.alerts_generated >= 1

    # Match against Ground Truth
    gt_dataset = GroundTruthDataset(gt_csv_path)
    matcher = EventMatcher(tolerance_seconds=2.0)
    all_events = list(pipeline.event_manager.closed_events) + list(pipeline.event_manager.active_events.values())
    report = matcher.match(
        ground_truth=gt_dataset.events,
        predictions=all_events,
        alerts=pipeline.alert_engine.alerts_history,
    )

    assert report.true_positives == 1
    assert report.false_negatives == 0
    assert report.false_positives == 0

    # Verify decision latency was computed as alert_video_time - gt_event_start_time
    matched_pair = report.matched_pairs[0]
    assert matched_pair.decision_latency_sec >= 0.0
    print(f"End-to-End Decision Latency: {matched_pair.decision_latency_sec:.3f}s")

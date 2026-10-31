"""Integration tests for deterministic replay pipeline."""

import pytest
from pathlib import Path

from level_crossing.common.config import SystemConfig
from level_crossing.common.types import CrossingState, SeverityLevel
from level_crossing.pipeline.replay_pipeline import ReplayPipeline
from level_crossing.detection.detector import MockDetector
from level_crossing.detection.detection_result import DetectionResult
from level_crossing.common.types import BoundingBox, RuleClass


def test_replay_pipeline_deterministic_execution(tmp_path: Path):
    db_file = tmp_path / "integration.sqlite3"
    config = SystemConfig.load_from_dir("configs")

    # Setup mock detector to simulate a person inside Danger Track from frame 10 to 40
    mock_det = MockDetector()
    for f in range(10, 45):
        # Danger track box
        box = BoundingBox(x1=250, y1=200, x2=350, y2=260)
        mock_det.set_frame_detections(
            frame_idx=f,
            detections=[
                DetectionResult(
                    bbox=box,
                    confidence=0.92,
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

    video_path = "data/controlled/validation/scenario_01_person_danger_track.mp4"
    if not Path(video_path).exists():
        pytest.skip(f"Validation video not found: {video_path}")

    summary = pipeline.run(
        video_path=video_path,
        crossing_state_timeline=lambda t: CrossingState.TRAIN_APPROACHING,
    )

    assert summary.total_frames_processed > 0
    assert summary.events_generated >= 1
    assert summary.alerts_generated >= 1
    assert summary.highest_severity_observed == SeverityLevel.CRITICAL

    # Verify SQLite records
    events = pipeline.event_repo.list_events()
    assert len(events) >= 1
    alerts = pipeline.alert_repo.list_alerts()
    assert len(alerts) >= 1
    assert alerts[0].severity == SeverityLevel.CRITICAL.value

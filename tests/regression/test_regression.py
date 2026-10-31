"""Regression tests safeguarding system invariants across versions."""

import pytest
from pathlib import Path
from level_crossing.common.types import CrossingState, ZoneType, RuleClass, SeverityLevel
from level_crossing.common.config import SystemConfig
from level_crossing.common.exceptions import ConfigurationError, VideoProcessingError
from level_crossing.video.video_reader import VideoReader


def test_severity_matrix_invariants():
    """Verify that the 64-rule V3.1 matrix preserves critical railway safety invariants."""
    config = SystemConfig.load_from_dir("configs")
    matrix = config.severity_matrix

    rule_map = {
        (r.crossing_state, r.zone_type, r.rule_class): r.severity
        for r in matrix.rules
    }

    # 1. Any person or vehicle in DANGER_TRACK with TRAIN_APPROACHING must be CRITICAL
    assert rule_map[(CrossingState.TRAIN_APPROACHING, ZoneType.DANGER_TRACK, RuleClass.PERSON)] == SeverityLevel.CRITICAL
    assert rule_map[(CrossingState.TRAIN_APPROACHING, ZoneType.DANGER_TRACK, RuleClass.VEHICLE)] == SeverityLevel.CRITICAL

    # 2. Any train in any zone must be IGNORE
    for s in CrossingState:
        for z in ZoneType:
            assert rule_map[(s, z, RuleClass.TRAIN)] == SeverityLevel.IGNORE

    # 3. Exactly 64 rules
    assert len(matrix.rules) == 64


def test_video_reader_nonexistent_file_raises_explicit_error():
    """Verify graceful and explicit failure when video source does not exist."""
    with pytest.raises(VideoProcessingError):
        VideoReader("non_existent_file_12345.mp4")


def test_missing_config_file_raises_configuration_error(tmp_path: Path):
    """Empty config directory must raise ConfigurationError, never silent defaults."""
    with pytest.raises(ConfigurationError):
        SystemConfig.load_from_dir(tmp_path)

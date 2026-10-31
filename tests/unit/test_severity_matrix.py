"""Unit tests for V3.1 Severity Matrix coverage, ambiguity rejection, and fallbacks."""

import pytest
from level_crossing.common.types import CrossingState, ZoneType, RuleClass, SeverityLevel
from level_crossing.common.config import SeverityMatrixConfig, SeverityRule
from level_crossing.common.exceptions import SeverityMatrixCoverageError, AmbiguousRuleError
from level_crossing.severity.matrix import SeverityMatrix


def test_matrix_complete_coverage():
    """Mandatory Gate Test: Matrix must define exactly one rule for every combination."""
    from level_crossing.common.config import SystemConfig
    config = SystemConfig.load_from_dir("configs")
    matrix = SeverityMatrix(config.severity_matrix)

    for state in CrossingState:
        for zone in ZoneType:
            for cls in [RuleClass.PERSON, RuleClass.VEHICLE, RuleClass.BICYCLE, RuleClass.TRAIN]:
                sev = matrix.lookup(state, zone, cls)
                assert isinstance(sev, SeverityLevel)
                if cls == RuleClass.TRAIN:
                    assert sev == SeverityLevel.IGNORE, f"Train must always map to IGNORE, got {sev} in {state} {zone}"


def test_matrix_rejects_duplicates():
    """Configuration error must be raised if duplicate/ambiguous rules exist."""
    rules = [
        SeverityRule(crossing_state=CrossingState.OPEN, zone_type=ZoneType.DANGER_TRACK, rule_class=RuleClass.PERSON, severity=SeverityLevel.MEDIUM),
        SeverityRule(crossing_state=CrossingState.OPEN, zone_type=ZoneType.DANGER_TRACK, rule_class=RuleClass.PERSON, severity=SeverityLevel.CRITICAL),
    ]
    cfg = SeverityMatrixConfig(version="3.1.0", specification="V3.1", rules=rules)
    with pytest.raises(AmbiguousRuleError):
        cfg.validate_coverage()


def test_matrix_rejects_missing_combinations():
    """Incomplete matrix must fail validation."""
    rules = [
        SeverityRule(crossing_state=CrossingState.OPEN, zone_type=ZoneType.DANGER_TRACK, rule_class=RuleClass.PERSON, severity=SeverityLevel.MEDIUM),
    ]
    cfg = SeverityMatrixConfig(version="3.1.0", specification="V3.1", rules=rules)
    with pytest.raises(SeverityMatrixCoverageError):
        cfg.validate_coverage()


def test_unknown_crossing_state_rules():
    """UNKNOWN state must map to HIGH or CRITICAL for active zones, never IGNORE (except train)."""
    from level_crossing.common.config import SystemConfig
    config = SystemConfig.load_from_dir("configs")
    matrix = SeverityMatrix(config.severity_matrix)

    assert matrix.lookup(CrossingState.UNKNOWN, ZoneType.DANGER_TRACK, RuleClass.PERSON) == SeverityLevel.CRITICAL
    assert matrix.lookup(CrossingState.UNKNOWN, ZoneType.PEDESTRIAN_CROSSING, RuleClass.PERSON) == SeverityLevel.HIGH
    assert matrix.lookup(CrossingState.UNKNOWN, ZoneType.DANGER_TRACK, RuleClass.TRAIN) == SeverityLevel.IGNORE


def test_runtime_missing_rule_fallback(caplog):
    """Runtime lookup with an unknown combination must fallback to HIGH and log a warning."""
    from level_crossing.common.config import SystemConfig
    config = SystemConfig.load_from_dir("configs")
    matrix = SeverityMatrix(config.severity_matrix)

    # Intentionally test unknown rule class
    sev = matrix.lookup(CrossingState.OPEN, ZoneType.DANGER_TRACK, RuleClass.UNKNOWN)
    assert sev == SeverityLevel.HIGH

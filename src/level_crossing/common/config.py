"""Configuration loader and schema validator for Level Crossing Safety System."""

import os
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import yaml
from pydantic import BaseModel, Field, field_validator

from level_crossing.common.types import (
    CrossingState,
    ZoneType,
    RuleClass,
    SeverityLevel,
)
from level_crossing.common.exceptions import (
    ConfigurationError,
    SeverityMatrixCoverageError,
    AmbiguousRuleError,
)


class ZoneConfig(BaseModel):
    id: str
    name: str
    zone_type: ZoneType
    description: str
    polygon: List[List[float]]
    color_rgb: List[int] = Field(default_factory=lambda: [255, 0, 0])
    criticality: int = 1

    @field_validator("polygon")
    @classmethod
    def validate_polygon(cls, v: List[List[float]]) -> List[List[float]]:
        if len(v) < 3:
            raise ValueError("Zone polygon must have at least 3 vertices")
        for pt in v:
            if len(pt) != 2:
                raise ValueError(f"Vertex {pt} must be 2D [x, y]")
        return v


class ZonesFileConfig(BaseModel):
    version: str
    coordinate_space: str = "normalized"
    zones: List[ZoneConfig]


class SeverityRule(BaseModel):
    crossing_state: CrossingState
    zone_type: ZoneType
    rule_class: RuleClass
    severity: SeverityLevel


class SeverityMatrixConfig(BaseModel):
    version: str
    specification: str
    fallback_severity: SeverityLevel = SeverityLevel.HIGH
    log_missing_rule_fallback: bool = True
    rules: List[SeverityRule]

    def validate_coverage(self) -> None:
        """Validates that exactly one rule exists for every (state, zone, rule_class) combination."""
        expected_states = [s for s in CrossingState]
        expected_zones = [z for z in ZoneType]
        expected_classes = [RuleClass.PERSON, RuleClass.VEHICLE, RuleClass.BICYCLE, RuleClass.TRAIN]

        seen: Dict[Tuple[CrossingState, ZoneType, RuleClass], SeverityLevel] = {}
        duplicates: List[str] = []

        for rule in self.rules:
            key = (rule.crossing_state, rule.zone_type, rule.rule_class)
            if key in seen:
                duplicates.append(f"{rule.crossing_state} x {rule.zone_type} x {rule.rule_class}")
            seen[key] = rule.severity

        if duplicates:
            raise AmbiguousRuleError(f"Duplicate/ambiguous rules detected in severity matrix: {duplicates}")

        missing: List[str] = []
        for state in expected_states:
            for zone in expected_zones:
                for cls in expected_classes:
                    if (state, zone, cls) not in seen:
                        missing.append(f"{state.value} x {zone.value} x {cls.value}")

        if missing:
            raise SeverityMatrixCoverageError(
                f"Severity matrix coverage incomplete. Missing {len(missing)} combinations: {missing[:5]}..."
            )


class DetectionThresholds(BaseModel):
    confidence_thresholds: Dict[str, float] = Field(
        default_factory=lambda: {"person": 0.35, "vehicle": 0.40, "bicycle": 0.35, "train": 0.45, "default": 0.35}
    )
    iou_nms_threshold: float = 0.45
    model_weights: str = "yolov8n.pt"
    input_resolution: List[int] = Field(default_factory=lambda: [640, 640])
    device: str = "mps"


class TrackingThresholds(BaseModel):
    iou_threshold: float = 0.30
    max_lost_frames: int = 30
    min_hits: int = 3
    distance_metric: str = "iou"


class SceneStateThresholds(BaseModel):
    reference_point: str = "bottom_center"
    boundary_hysteresis_pixels: float = 8.0
    boundary_hysteresis_normalized: float = 0.015
    velocity_smoothing_alpha: float = 0.3


class EventManagerThresholds(BaseModel):
    confirmation_dwell_seconds: Dict[str, float] = Field(
        default_factory=lambda: {
            "DANGER_TRACK": 0.8,
            "PEDESTRIAN_CROSSING": 2.0,
            "ISLAND": 2.5,
            "APPROACH_ROAD": 3.0,
            "default": 1.5,
        }
    )
    escalation_seconds: float = 3.0
    cooldown_seconds: float = 5.0
    track_lost_timeout_seconds: float = 2.0


class TrainSuppressionThresholds(BaseModel):
    enabled: bool = True
    overlap_iou_threshold: float = 0.25
    area_ratio_threshold: float = 0.35


class ThresholdsConfig(BaseModel):
    version: str
    detection: DetectionThresholds = Field(default_factory=DetectionThresholds)
    tracking: TrackingThresholds = Field(default_factory=TrackingThresholds)
    scene_state: SceneStateThresholds = Field(default_factory=SceneStateThresholds)
    event_manager: EventManagerThresholds = Field(default_factory=EventManagerThresholds)
    train_suppression: TrainSuppressionThresholds = Field(default_factory=TrainSuppressionThresholds)


class SystemConfig(BaseModel):
    """Aggregate validated configuration."""
    zones: ZonesFileConfig
    severity_matrix: SeverityMatrixConfig
    thresholds: ThresholdsConfig

    @classmethod
    def load_from_dir(cls, config_dir: str | Path) -> "SystemConfig":
        config_path = Path(config_dir)
        zones_file = config_path / "zones.yaml"
        matrix_file = config_path / "severity_matrix.yaml"
        thresholds_file = config_path / "thresholds.yaml"

        if not zones_file.exists():
            raise ConfigurationError(f"Missing configuration file: {zones_file}")
        if not matrix_file.exists():
            raise ConfigurationError(f"Missing configuration file: {matrix_file}")
        if not thresholds_file.exists():
            raise ConfigurationError(f"Missing configuration file: {thresholds_file}")

        with open(zones_file, "r") as f:
            zones_data = yaml.safe_load(f)
        with open(matrix_file, "r") as f:
            matrix_data = yaml.safe_load(f)
        with open(thresholds_file, "r") as f:
            thresholds_data = yaml.safe_load(f)

        zones = ZonesFileConfig(**zones_data)
        severity_matrix = SeverityMatrixConfig(**matrix_data)
        severity_matrix.validate_coverage()  # Strict coverage check
        thresholds = ThresholdsConfig(**thresholds_data)

        return cls(zones=zones, severity_matrix=severity_matrix, thresholds=thresholds)

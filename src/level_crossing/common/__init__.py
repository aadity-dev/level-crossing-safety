"""Common foundational utilities, types, logging and configuration."""

from level_crossing.common.types import (
    CrossingState,
    ZoneType,
    RuleClass,
    SeverityLevel,
    EventStatus,
    AlertType,
    AlertStatus,
    HealthStatus,
    MovementStatus,
    Point2D,
    BoundingBox,
)
from level_crossing.common.exceptions import (
    LevelCrossingError,
    ConfigurationError,
    SeverityMatrixCoverageError,
    AmbiguousRuleError,
    VideoProcessingError,
    DetectionError,
    DatabaseError,
)
from level_crossing.common.logger import get_logger
from level_crossing.common.config import SystemConfig

__all__ = [
    "CrossingState",
    "ZoneType",
    "RuleClass",
    "SeverityLevel",
    "EventStatus",
    "AlertType",
    "AlertStatus",
    "HealthStatus",
    "MovementStatus",
    "Point2D",
    "BoundingBox",
    "LevelCrossingError",
    "ConfigurationError",
    "SeverityMatrixCoverageError",
    "AmbiguousRuleError",
    "VideoProcessingError",
    "DetectionError",
    "DatabaseError",
    "get_logger",
    "SystemConfig",
]

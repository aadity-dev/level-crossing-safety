"""Core domain types and enumerations for the Level Crossing Safety System."""

from enum import Enum
from typing import NamedTuple, Tuple, List, Optional
from pydantic import BaseModel, Field


class CrossingState(str, Enum):
    """Railway level crossing operational states."""
    OPEN = "OPEN"
    TRAIN_APPROACHING = "TRAIN_APPROACHING"
    TRAIN_PASSING = "TRAIN_PASSING"
    UNKNOWN = "UNKNOWN"


class ZoneType(str, Enum):
    """Crossing zone classification."""
    APPROACH_ROAD = "APPROACH_ROAD"
    DANGER_TRACK = "DANGER_TRACK"
    ISLAND = "ISLAND"
    PEDESTRIAN_CROSSING = "PEDESTRIAN_CROSSING"


class RuleClass(str, Enum):
    """Normalized rule classes mapped from object detector classes."""
    PERSON = "person"
    VEHICLE = "vehicle"
    BICYCLE = "bicycle"
    TRAIN = "train"
    UNKNOWN = "unknown"


class SeverityLevel(str, Enum):
    """Contextual hazard severity levels."""
    IGNORE = "IGNORE"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

    @property
    def rank(self) -> int:
        ranks = {
            SeverityLevel.IGNORE: 0,
            SeverityLevel.LOW: 1,
            SeverityLevel.MEDIUM: 2,
            SeverityLevel.HIGH: 3,
            SeverityLevel.CRITICAL: 4,
        }
        return ranks[self]

    def __ge__(self, other: "SeverityLevel") -> bool:
        if self.__class__ is other.__class__:
            return self.rank >= other.rank
        return NotImplemented

    def __gt__(self, other: "SeverityLevel") -> bool:
        if self.__class__ is other.__class__:
            return self.rank > other.rank
        return NotImplemented

    def __le__(self, other: "SeverityLevel") -> bool:
        if self.__class__ is other.__class__:
            return self.rank <= other.rank
        return NotImplemented

    def __lt__(self, other: "SeverityLevel") -> bool:
        if self.__class__ is other.__class__:
            return self.rank < other.rank
        return NotImplemented


class EventStatus(str, Enum):
    """Lifecycle status of a safety event."""
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    ESCALATED = "ESCALATED"
    RECOVERED = "RECOVERED"
    CLOSED = "CLOSED"


class AlertType(str, Enum):
    """Classification of generated alert."""
    INITIAL = "INITIAL"
    ESCALATION = "ESCALATION"
    RECOVERY = "RECOVERY"


class AlertStatus(str, Enum):
    """Alert delivery status."""
    GENERATED = "GENERATED"
    DISPATCHED = "DISPATCHED"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    SUPPRESSED = "SUPPRESSED"


class HealthStatus(str, Enum):
    """System health state."""
    HEALTHY = "HEALTHY"
    DEGRADED = "DEGRADED"
    FAILED = "FAILED"


class MovementStatus(str, Enum):
    """Kinematic movement state of an entity."""
    STATIONARY = "STATIONARY"
    SLOW = "SLOW"
    FAST = "FAST"
    STOPPED = "STOPPED"


class Point2D(NamedTuple):
    x: float
    y: float


class BoundingBox(NamedTuple):
    x1: float
    y1: float
    x2: float
    y2: float

    @property
    def width(self) -> float:
        return max(0.0, self.x2 - self.x1)

    @property
    def height(self) -> float:
        return max(0.0, self.y2 - self.y1)

    @property
    def area(self) -> float:
        return self.width * self.height

    @property
    def bottom_center(self) -> Point2D:
        """Standardized reference point for zone intersection."""
        return Point2D(x=(self.x1 + self.x2) / 2.0, y=self.y2)

    @property
    def center(self) -> Point2D:
        return Point2D(x=(self.x1 + self.x2) / 2.0, y=(self.y1 + self.y2) / 2.0)

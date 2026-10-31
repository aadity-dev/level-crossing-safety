"""Domain exceptions for Level Crossing Safety Monitoring System."""


class LevelCrossingError(Exception):
    """Base exception for all domain errors."""
    pass


class ConfigurationError(LevelCrossingError):
    """Raised when configuration validation fails."""
    pass


class SeverityMatrixCoverageError(ConfigurationError):
    """Raised when the severity matrix fails completeness or coverage validation."""
    pass


class AmbiguousRuleError(ConfigurationError):
    """Raised when duplicate or conflicting rules match the same state-zone-class."""
    pass


class VideoProcessingError(LevelCrossingError):
    """Raised when frame capture, decoding, or stream reading encounters a fatal error."""
    pass


class DetectionError(LevelCrossingError):
    """Raised when the detector fails inference or receives corrupt input."""
    pass


class DatabaseError(LevelCrossingError):
    """Raised when a persistence or transaction operation fails."""
    pass

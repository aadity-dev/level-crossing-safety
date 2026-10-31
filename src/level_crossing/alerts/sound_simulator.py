"""Local auditory alert warning simulation."""

from typing import Optional
from level_crossing.common.types import SeverityLevel
from level_crossing.common.logger import get_logger

logger = get_logger("sound_simulator")


class SoundSimulator:
    """Simulates localized acoustic alarms based on alert severity."""

    PATTERNS = {
        SeverityLevel.MEDIUM: {"frequency_hz": 800, "duration_ms": 250, "pulses": 2},
        SeverityLevel.HIGH: {"frequency_hz": 1200, "duration_ms": 400, "pulses": 3},
        SeverityLevel.CRITICAL: {"frequency_hz": 2000, "duration_ms": 600, "pulses": 5},
    }

    def __init__(self, enable_audio: bool = False):
        self.enable_audio = enable_audio

    def play_alert(self, severity: SeverityLevel) -> None:
        pattern = self.PATTERNS.get(severity)
        if not pattern:
            return

        logger.info(
            f"AUDIO ALARM TRIGGERED [{severity.value}]: {pattern['frequency_hz']}Hz, "
            f"{pattern['pulses']} pulses x {pattern['duration_ms']}ms"
        )

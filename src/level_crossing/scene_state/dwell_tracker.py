"""Continuous zone dwell time tracking using the active clock."""

from typing import Dict, Tuple, Optional
from dataclasses import dataclass


@dataclass
class DwellRecord:
    zone_id: str
    entry_timestamp: float
    last_update_timestamp: float

    @property
    def dwell_seconds(self) -> float:
        return max(0.0, self.last_update_timestamp - self.entry_timestamp)


class DwellTracker:
    """Maintains active continuous dwell duration per track ID inside zones."""

    def __init__(self):
        # Maps track_id -> DwellRecord
        self._active_dwells: Dict[int, DwellRecord] = {}

    def update(self, track_id: int, current_zone_id: Optional[str], timestamp: float) -> float:
        """Updates dwell status for a track and returns current dwell seconds."""
        if current_zone_id is None:
            # Track is outside any monitored safety zone -> reset dwell
            self._active_dwells.pop(track_id, None)
            return 0.0

        existing = self._active_dwells.get(track_id)
        if existing is None or existing.zone_id != current_zone_id:
            # Entered new zone -> start fresh dwell timer
            self._active_dwells[track_id] = DwellRecord(
                zone_id=current_zone_id,
                entry_timestamp=timestamp,
                last_update_timestamp=timestamp,
            )
            return 0.0
        else:
            # Still in same zone -> advance update timestamp
            existing.last_update_timestamp = timestamp
            return existing.dwell_seconds

    def get_dwell(self, track_id: int) -> float:
        rec = self._active_dwells.get(track_id)
        return rec.dwell_seconds if rec else 0.0

    def get_entry_time(self, track_id: int) -> Optional[float]:
        rec = self._active_dwells.get(track_id)
        return rec.entry_timestamp if rec else None

    def reset(self) -> None:
        self._active_dwells.clear()

"""Ground truth annotation parser with dual-timestamp hazard formula."""

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict, Optional
from level_crossing.common.types import CrossingState, RuleClass, ZoneType


@dataclass
class GroundTruthEvent:
    video_id: str
    event_id: str
    start_time: float             # Calculated: max(zone_entry_time, unsafe_state_start_time)
    end_time: float
    event_type: str
    object_type: RuleClass
    crossing_state: CrossingState
    zone_entry_time: float
    unsafe_state_start_time: float

    @classmethod
    def from_row(cls, row: Dict[str, str]) -> "GroundTruthEvent":
        z_entry = float(row["zone_entry_time"])
        unsafe_start = float(row["unsafe_state_start_time"])
        # Official Specification Formula:
        # GT start_time = max(zone_entry_time, unsafe_state_start_time)
        computed_start = max(z_entry, unsafe_start)
        end_t = float(row["end_time"])

        return cls(
            video_id=row["video_id"],
            event_id=row["event_id"],
            start_time=computed_start,
            end_time=end_t,
            event_type=row["event_type"],
            object_type=RuleClass(row["object_type"].lower()),
            crossing_state=CrossingState(row["crossing_state"]),
            zone_entry_time=z_entry,
            unsafe_state_start_time=unsafe_start,
        )


class GroundTruthDataset:
    """Loads and indexes ground truth events from standard CSV format."""

    def __init__(self, csv_path: str | Path):
        self.csv_path = Path(csv_path)
        self.events: List[GroundTruthEvent] = []
        self._load()

    def _load(self) -> None:
        if not self.csv_path.exists():
            return
        with open(self.csv_path, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if not row.get("event_id"):
                    continue
                self.events.append(GroundTruthEvent.from_row(row))

    def get_events_for_video(self, video_id: str) -> List[GroundTruthEvent]:
        return [e for e in self.events if e.video_id == video_id]

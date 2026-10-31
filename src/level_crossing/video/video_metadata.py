"""Metadata descriptor for video streams and files."""

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class VideoMetadata:
    width: int
    height: int
    fps: float
    total_frames: int
    duration_sec: float
    codec: Optional[str] = None
    file_path: Optional[str] = None

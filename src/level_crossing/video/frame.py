"""Video frame representation with timestamp metadata."""

from dataclasses import dataclass
import numpy as np


@dataclass
class Frame:
    """A single decoded video frame with explicit timing."""
    image: np.ndarray
    frame_idx: int
    timestamp_sec: float
    width: int
    height: int

    @classmethod
    def from_numpy(cls, image: np.ndarray, frame_idx: int, timestamp_sec: float) -> "Frame":
        h, w = image.shape[:2]
        return cls(
            image=image,
            frame_idx=frame_idx,
            timestamp_sec=timestamp_sec,
            width=w,
            height=h,
        )

"""Video frame ingestion supporting deterministic replay and live streaming modes."""

import cv2
import time
from pathlib import Path
from typing import Generator, Optional, Tuple
import numpy as np

from level_crossing.common.exceptions import VideoProcessingError
from level_crossing.common.logger import get_logger
from level_crossing.video.frame import Frame
from level_crossing.video.video_metadata import VideoMetadata

logger = get_logger("video_reader")


class VideoReader:
    """Reads video files or synthetic sequences with strict timing control."""

    def __init__(self, source: str | int | Path, realtime_mode: bool = False, max_fps: Optional[float] = None):
        self.source = str(source)
        self.realtime_mode = realtime_mode
        self.max_fps = max_fps
        self._cap: Optional[cv2.VideoCapture] = None
        self._metadata: Optional[VideoMetadata] = None
        self._open()

    def _open(self) -> None:
        src = int(self.source) if str(self.source).isdigit() else str(self.source)
        self._cap = cv2.VideoCapture(src)
        if not self._cap.isOpened():
            raise VideoProcessingError(f"Failed to open video source: {self.source}")

        width = int(self._cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(self._cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = float(self._cap.get(cv2.CAP_PROP_FPS))
        if fps <= 0.0 or np.isnan(fps):
            fps = 30.0  # Sensible fallback
        total_frames = int(self._cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = total_frames / fps if total_frames > 0 else 0.0

        fourcc_int = int(self._cap.get(cv2.CAP_PROP_FOURCC))
        codec = "".join([chr((fourcc_int >> 8 * i) & 0xFF) for i in range(4)])

        self._metadata = VideoMetadata(
            width=width,
            height=height,
            fps=fps,
            total_frames=total_frames,
            duration_sec=duration,
            codec=codec,
            file_path=str(self.source),
        )
        logger.info(f"Opened video {self.source}: {width}x{height} @ {fps:.1f}fps, {total_frames} frames ({duration:.1f}s)")

    @property
    def metadata(self) -> VideoMetadata:
        if self._metadata is None:
            raise VideoProcessingError("Video source not opened")
        return self._metadata

    def frames(self) -> Generator[Frame, None, None]:
        """Yields frames. In replay mode, timestamps are exact video time. In realtime mode, wall-clock."""
        if not self._cap or not self._cap.isOpened():
            self._open()

        fps = self.metadata.fps
        frame_interval = 1.0 / fps if fps > 0 else 0.033
        start_wall_time = time.time()
        frame_idx = 0

        try:
            while True:
                ret, img = self._cap.read()
                if not ret or img is None:
                    break

                if self.realtime_mode:
                    timestamp_sec = time.time() - start_wall_time
                    if self.max_fps and self.max_fps > 0:
                        elapsed = time.time() - start_wall_time
                        expected = frame_idx * (1.0 / self.max_fps)
                        if elapsed < expected:
                            time.sleep(expected - elapsed)
                else:
                    # Replay mode: pure deterministic video clock
                    timestamp_sec = frame_idx / fps

                yield Frame.from_numpy(img, frame_idx=frame_idx, timestamp_sec=timestamp_sec)
                frame_idx += 1
        finally:
            self.close()

    def close(self) -> None:
        if self._cap is not None:
            self._cap.release()
            self._cap = None

"""Annotated video generator with safety zones, tracks, and status telemetry."""

import cv2
import numpy as np
from pathlib import Path
from typing import List, Optional, Tuple, Dict, Any

from level_crossing.common.types import CrossingState, SeverityLevel
from level_crossing.common.logger import get_logger

logger = get_logger("video_writer")


class VideoAnnotator:
    """Renders crisp safety telemetry overlays onto video frames."""

    SEVERITY_COLORS = {
        SeverityLevel.IGNORE: (128, 128, 128),
        SeverityLevel.LOW: (34, 197, 94),      # Green (BGR)
        SeverityLevel.MEDIUM: (0, 165, 255),   # Orange
        SeverityLevel.HIGH: (0, 69, 255),      # Red-Orange
        SeverityLevel.CRITICAL: (0, 0, 255),   # Bright Red
    }

    STATE_COLORS = {
        CrossingState.OPEN: (34, 197, 94),              # Green
        CrossingState.TRAIN_APPROACHING: (0, 140, 255), # Amber
        CrossingState.TRAIN_PASSING: (0, 0, 255),       # Red
        CrossingState.UNKNOWN: (128, 128, 128),         # Gray
    }

    @classmethod
    def draw_zones(cls, image: np.ndarray, zones: List[Any], alpha: float = 0.25) -> np.ndarray:
        """Draws filled polygon zones with transparency."""
        overlay = image.copy()
        h, w = image.shape[:2]

        for z in zones:
            pts = np.array(z.pixel_polygon(w, h), dtype=np.int32)
            color_bgr = (int(z.color_rgb[2]), int(z.color_rgb[1]), int(z.color_rgb[0]))
            cv2.fillPoly(overlay, [pts], color_bgr)
            cv2.polylines(image, [pts], isClosed=True, color=color_bgr, thickness=2)

            # Zone label
            centroid_x = int(np.mean(pts[:, 0]))
            centroid_y = int(np.mean(pts[:, 1]))
            cv2.putText(
                image,
                z.name,
                (max(10, centroid_x - 40), max(20, centroid_y)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.45,
                (255, 255, 255),
                1,
                cv2.LINE_AA,
            )

        return cv2.addWeighted(overlay, alpha, image, 1 - alpha, 0)

    @classmethod
    def draw_tracks(cls, image: np.ndarray, tracks_state: List[Dict[str, Any]]) -> np.ndarray:
        """Draws bounding boxes, track IDs, rule classes, dwell times, and severity."""
        for t in tracks_state:
            bbox = t["bbox"]
            x1, y1, x2, y2 = int(bbox.x1), int(bbox.y1), int(bbox.x2), int(bbox.y2)
            sev = t.get("severity", SeverityLevel.LOW)
            color = cls.SEVERITY_COLORS.get(sev, (255, 255, 255))

            # Bounding box
            cv2.rectangle(image, (x1, y1), (x2, y2), color, 2)

            # Reference point marker (bottom-center)
            ref_x, ref_y = int((x1 + x2) / 2), y2
            cv2.circle(image, (ref_x, ref_y), 4, (0, 255, 255), -1)

            # Label text
            track_id = t["track_id"]
            rule_cls = t["rule_class"]
            dwell = t.get("dwell_sec", 0.0)
            zone_name = t.get("zone_type", "OUTSIDE")

            label = f"ID:{track_id} {rule_cls} | {zone_name} | {dwell:.1f}s | {sev.value}"
            (lw, lh), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.42, 1)

            # Background pill
            cv2.rectangle(image, (x1, max(0, y1 - lh - 8)), (x1 + lw + 6, max(0, y1)), color, -1)
            cv2.putText(
                image,
                label,
                (x1 + 3, max(12, y1 - 4)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.42,
                (0, 0, 0) if sev == SeverityLevel.LOW else (255, 255, 255),
                1,
                cv2.LINE_AA,
            )
        return image

    @classmethod
    def draw_telemetry_banner(
        cls,
        image: np.ndarray,
        frame_idx: int,
        timestamp_sec: float,
        crossing_state: CrossingState,
        highest_severity: SeverityLevel,
        active_alert_count: int,
        fps: float = 0.0,
    ) -> np.ndarray:
        """Renders top status dashboard banner."""
        h, w = image.shape[:2]
        banner_h = 36
        banner = np.zeros((banner_h, w, 3), dtype=np.uint8)

        # Background color based on highest severity
        b_color = cls.SEVERITY_COLORS.get(highest_severity, (30, 30, 30))
        cv2.rectangle(banner, (0, 0), (w, banner_h), (25, 25, 25), -1)

        # Status text elements
        state_color = cls.STATE_COLORS.get(crossing_state, (200, 200, 200))
        cv2.putText(
            banner,
            f"STATE: {crossing_state.value}",
            (12, 24),
            cv2.FONT_HERSHEY_DUPLEX,
            0.6,
            state_color,
            1,
            cv2.LINE_AA,
        )

        cv2.putText(
            banner,
            f"MAX RISK: {highest_severity.value}",
            (260, 24),
            cv2.FONT_HERSHEY_DUPLEX,
            0.55,
            b_color,
            1,
            cv2.LINE_AA,
        )

        cv2.putText(
            banner,
            f"ALERTS: {active_alert_count}",
            (480, 24),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (0, 165, 255) if active_alert_count > 0 else (180, 180, 180),
            1,
            cv2.LINE_AA,
        )

        time_str = f"T: {timestamp_sec:.2f}s (F#{frame_idx})"
        if fps > 0:
            time_str += f" | {fps:.1f} FPS"
        cv2.putText(
            banner,
            time_str,
            (max(10, w - 240), 24),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (220, 220, 220),
            1,
            cv2.LINE_AA,
        )

        return np.vstack([banner, image])


class VideoWriter:
    """Encodes annotated video stream to MP4."""

    def __init__(self, output_path: str | Path, fps: float, width: int, height: int):
        self.output_path = Path(output_path)
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        self.fps = fps
        self.width = width
        self.height = height
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        self._writer = cv2.VideoWriter(str(self.output_path), fourcc, fps, (width, height))

    def write_frame(self, frame: np.ndarray) -> None:
        if frame.shape[1] != self.width or frame.shape[0] != self.height:
            frame = cv2.resize(frame, (self.width, self.height))
        self._writer.write(frame)

    def close(self) -> None:
        if self._writer is not None:
            self._writer.release()
            self._writer = None

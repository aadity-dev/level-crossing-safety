"""Spatial hazard density analytics and trajectory heatmap generator."""

import cv2
import numpy as np
from pathlib import Path
from typing import List, Tuple, Dict, Any, Optional

from level_crossing.common.logger import get_logger

logger = get_logger("hazard_heatmap")


class HazardHeatmapGenerator:
    """Accumulates entity foot-point coordinates and synthesizes thermal hazard density heatmaps."""

    def __init__(self, width: int = 640, height: int = 480, kernel_size: int = 35, sigma: float = 15.0):
        self.width = width
        self.height = height
        self.kernel_size = kernel_size if kernel_size % 2 == 1 else kernel_size + 1
        self.sigma = sigma
        self.accumulator = np.zeros((height, width), dtype=np.float32)
        self.total_points = 0
        self.danger_points = 0
        self.trajectory_points: List[Tuple[int, int, float, bool]] = []

    def add_point(self, x: int | float, y: int | float, weight: float = 1.0, in_danger: bool = False) -> None:
        """Adds a single foot ground-contact coordinate to the spatial density buffer."""
        xi = int(np.clip(round(x), 0, self.width - 1))
        yi = int(np.clip(round(y), 0, self.height - 1))

        self.accumulator[yi, xi] += float(weight)
        self.total_points += 1
        if in_danger:
            self.danger_points += 1
        self.trajectory_points.append((xi, yi, float(weight), in_danger))

    def add_bbox(self, bbox: Any, weight: float = 1.0, in_danger: bool = False) -> None:
        """Adds the bottom-center foot coordinate of a bounding box."""
        # bbox can be BoundingBox or tuple/list [x1, y1, x2, y2]
        if hasattr(bbox, "x1"):
            foot_x = (bbox.x1 + bbox.x2) / 2.0
            foot_y = float(bbox.y2)
        else:
            foot_x = (bbox[0] + bbox[2]) / 2.0
            foot_y = float(bbox[3])
        self.add_point(foot_x, foot_y, weight=weight, in_danger=in_danger)

    def generate_heatmap(
        self,
        background_rgb: Optional[np.ndarray] = None,
        alpha: float = 0.55,
        colormap: int = cv2.COLORMAP_JET,
        threshold_ratio: float = 0.04,
    ) -> np.ndarray:
        """Applies Gaussian smoothing, colormapping, and alpha-blends onto a background frame.
        
        Returns an RGB image ready for display.
        """
        if background_rgb is None:
            # Default dark neutral canvas
            bg = np.full((self.height, self.width, 3), 30, dtype=np.uint8)
        else:
            bg = cv2.resize(background_rgb, (self.width, self.height)).copy()

        if self.total_points == 0 or np.max(self.accumulator) == 0:
            return bg

        # 1. 2D Gaussian Kernel Density Smoothing
        smoothed = cv2.GaussianBlur(
            self.accumulator,
            (self.kernel_size, self.kernel_size),
            self.sigma,
        )

        max_val = np.max(smoothed)
        if max_val <= 0:
            return bg

        # 2. Normalize to 0..255
        norm_density = (smoothed / max_val * 255.0).astype(np.uint8)

        # 3. Threshold mask to keep background transparent where density is negligible
        min_cutoff = int(threshold_ratio * 255)
        active_mask = (norm_density > min_cutoff).astype(np.uint8)

        # 4. Apply false-color thermal palette (Blue -> Cyan -> Yellow -> Red)
        colored_heat = cv2.applyColorMap(norm_density, colormap)
        # Convert BGR from OpenCV to RGB
        colored_heat_rgb = cv2.cvtColor(colored_heat, cv2.COLOR_BGR2RGB)

        # 5. Non-linear alpha blending using density intensity
        alpha_map = (norm_density.astype(np.float32) / 255.0 * alpha)[:, :, np.newaxis]
        alpha_map = np.clip(alpha_map * active_mask[:, :, np.newaxis], 0.0, 1.0)

        blended = (colored_heat_rgb.astype(np.float32) * alpha_map + bg.astype(np.float32) * (1.0 - alpha_map)).astype(np.uint8)

        # Draw contour highlights around peak danger clusters
        contours, _ = cv2.findContours(active_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        cv2.drawContours(blended, contours, -1, (255, 255, 255), 1)

        return blended

    def get_analytics(self) -> Dict[str, Any]:
        """Calculates quantitative spatial metrics for urban planners and safety directors."""
        danger_pct = (self.danger_points / self.total_points * 100.0) if self.total_points > 0 else 0.0
        
        # Peak hotspot coordinate
        smoothed = cv2.GaussianBlur(self.accumulator, (self.kernel_size, self.kernel_size), self.sigma)
        peak_idx = np.unravel_index(np.argmax(smoothed), smoothed.shape)
        peak_y, peak_x = int(peak_idx[0]), int(peak_idx[1])

        return {
            "total_foot_samples": self.total_points,
            "danger_zone_samples": self.danger_points,
            "danger_zone_percentage": round(danger_pct, 1),
            "safe_zone_samples": self.total_points - self.danger_points,
            "peak_hotspot_coordinate": {"x": peak_x, "y": peak_y},
            "peak_density_intensity": float(np.max(smoothed)) if self.total_points > 0 else 0.0,
        }

    def reset(self) -> None:
        """Clears the accumulation buffer."""
        self.accumulator.fill(0.0)
        self.total_points = 0
        self.danger_points = 0
        self.trajectory_points.clear()

"""Spatial safety zone models based on Shapely geometric polygons."""

from typing import List, Tuple
import numpy as np
from shapely.geometry import Polygon, Point

from level_crossing.common.types import ZoneType, Point2D
from level_crossing.common.config import ZoneConfig


class Zone:
    """Geometric polygon zone representation."""

    def __init__(self, config: ZoneConfig):
        self.id = config.id
        self.name = config.name
        self.zone_type = config.zone_type
        self.description = config.description
        self.color_rgb = config.color_rgb
        self.criticality = config.criticality
        self.normalized_polygon = [tuple(p) for p in config.polygon]
        self._poly = Polygon(self.normalized_polygon)

    def contains_point_normalized(self, point: Point2D) -> bool:
        """Point-in-polygon test in normalized [0, 1] space."""
        return self._poly.contains(Point(point.x, point.y))

    def distance_to_point_normalized(self, point: Point2D) -> float:
        """Distance from normalized point to polygon boundary."""
        return self._poly.distance(Point(point.x, point.y))

    def pixel_polygon(self, frame_width: int, frame_height: int) -> List[Tuple[int, int]]:
        """Converts normalized polygon to absolute pixel coordinates."""
        return [
            (int(round(x * frame_width)), int(round(y * frame_height)))
            for x, y in self.normalized_polygon
        ]

    def contains_point_pixels(self, px: float, py: float, frame_width: int, frame_height: int) -> bool:
        """Point-in-polygon test with pixel coordinates."""
        norm_x = px / frame_width
        norm_y = py / frame_height
        return self.contains_point_normalized(Point2D(norm_x, norm_y))

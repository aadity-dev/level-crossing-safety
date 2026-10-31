"""Zone membership evaluation with bottom-center reference point and boundary hysteresis."""

from typing import List, Optional, Tuple, Dict
from level_crossing.common.types import Point2D, BoundingBox, ZoneType
from level_crossing.scene_state.zone import Zone


class ZoneMembershipEvaluator:
    """Evaluates spatial inclusion with boundary hysteresis to avoid border jitter."""

    def __init__(self, zones: List[Zone], hysteresis_normalized: float = 0.015):
        # Sort zones by criticality (lower number = higher criticality, e.g. DANGER_TRACK first)
        self.zones = sorted(zones, key=lambda z: z.criticality)
        self.hysteresis = hysteresis_normalized

    def evaluate(
        self,
        bbox: BoundingBox,
        frame_width: int,
        frame_height: int,
        previous_zone: Optional[Zone] = None,
    ) -> Optional[Zone]:
        """Determines the primary zone for a bounding box using bottom-center reference point."""
        ref_pt = bbox.bottom_center
        norm_pt = Point2D(x=ref_pt.x / frame_width, y=ref_pt.y / frame_height)

        # First check current containing zones
        containing_zones: List[Zone] = []
        for zone in self.zones:
            if zone.contains_point_normalized(norm_pt):
                containing_zones.append(zone)

        if containing_zones:
            # If the previously occupied zone is among the containing zones, stick to it (stability)
            if previous_zone in containing_zones:
                return previous_zone
            # Otherwise pick highest criticality (first in sorted list)
            return containing_zones[0]

        # Boundary hysteresis: if object was in previous_zone and is within hysteresis margin, retain it
        if previous_zone is not None:
            dist = previous_zone.distance_to_point_normalized(norm_pt)
            if dist <= self.hysteresis:
                return previous_zone

        return None

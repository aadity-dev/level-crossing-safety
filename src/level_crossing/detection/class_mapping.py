"""Mapping raw detector class labels to domain safety rule classes."""

from typing import Dict
from level_crossing.common.types import RuleClass

# COCO dataset class name mappings to safety RuleClass
COCO_TO_RULE_CLASS: Dict[str, RuleClass] = {
    "person": RuleClass.PERSON,
    "pedestrian": RuleClass.PERSON,
    "bicycle": RuleClass.BICYCLE,
    "car": RuleClass.VEHICLE,
    "motorcycle": RuleClass.BICYCLE,
    "bus": RuleClass.VEHICLE,
    "truck": RuleClass.VEHICLE,
    "train": RuleClass.TRAIN,
    "locomotive": RuleClass.TRAIN,
    "rail_vehicle": RuleClass.TRAIN,
}


class ClassMapper:
    """Translates detector-specific class labels into domain rule classes."""

    def __init__(self, custom_mapping: Dict[str, RuleClass] | None = None):
        self.mapping = dict(COCO_TO_RULE_CLASS)
        if custom_mapping:
            self.mapping.update(custom_mapping)

    def map_class(self, class_name: str) -> RuleClass:
        """Maps a detector string label to a normalized RuleClass."""
        normalized = class_name.strip().lower()
        return self.mapping.get(normalized, RuleClass.UNKNOWN)

"""V3.1 Severity matrix lookup and rule completeness verification."""

from typing import Dict, Tuple, Optional
from level_crossing.common.types import (
    CrossingState,
    ZoneType,
    RuleClass,
    SeverityLevel,
)
from level_crossing.common.config import SeverityMatrixConfig
from level_crossing.common.logger import get_logger

logger = get_logger("severity_matrix")


class SeverityMatrix:
    """Stateless lookup table for (state, zone, rule_class) -> SeverityLevel."""

    def __init__(self, config: SeverityMatrixConfig):
        self.config = config
        self.fallback_severity = config.fallback_severity
        self.log_fallback = config.log_missing_rule_fallback
        self._lookup: Dict[Tuple[CrossingState, ZoneType, RuleClass], SeverityLevel] = {}
        self._build_lookup()

    def _build_lookup(self) -> None:
        self.config.validate_coverage()
        for rule in self.config.rules:
            key = (rule.crossing_state, rule.zone_type, rule.rule_class)
            self._lookup[key] = rule.severity

    def lookup(
        self,
        crossing_state: CrossingState,
        zone_type: Optional[ZoneType],
        rule_class: RuleClass,
    ) -> SeverityLevel:
        """Evaluates severity for a single object in a zone and crossing state."""
        # Train objects are ignored from intrusion alerting
        if rule_class == RuleClass.TRAIN:
            return SeverityLevel.IGNORE

        # Objects outside of monitored zones are IGNORE
        if zone_type is None:
            return SeverityLevel.IGNORE

        key = (crossing_state, zone_type, rule_class)
        sev = self._lookup.get(key)

        if sev is None:
            if self.log_fallback:
                logger.warning(
                    f"Missing rule for combination ({crossing_state.value}, {zone_type.value}, {rule_class.value}). "
                    f"Applying fallback severity: {self.fallback_severity.value}"
                )
            return self.fallback_severity

        return sev

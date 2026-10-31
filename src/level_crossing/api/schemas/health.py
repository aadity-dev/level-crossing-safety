"""Health check API schemas."""

from pydantic import BaseModel
from typing import Dict, Any, Optional
from level_crossing.common.types import HealthStatus, CrossingState


class HealthResponse(BaseModel):
    status: HealthStatus
    crossing_state: CrossingState
    database_connected: bool
    model_loaded: bool
    details: Dict[str, Any]

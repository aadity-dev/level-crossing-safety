"""Health and operational diagnostic endpoints."""

from fastapi import APIRouter, Depends, Request
from level_crossing.api.schemas.health import HealthResponse

router = APIRouter(prefix="/health", tags=["Health"])


@router.get("", response_model=HealthResponse)
def get_health(request: Request) -> HealthResponse:
    service = request.app.state.safety_service
    health_data = service.check_health()
    return HealthResponse(**health_data)

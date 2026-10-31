"""Auditable alerts endpoints."""

from fastapi import APIRouter, Request, Query
from typing import List
from level_crossing.api.schemas.alerts import AlertItemResponse

router = APIRouter(prefix="/alerts", tags=["Alerts"])


@router.get("", response_model=List[AlertItemResponse])
def list_alerts(request: Request, limit: int = Query(50, ge=1, le=500)) -> List[AlertItemResponse]:
    service = request.app.state.safety_service
    records = service.list_alerts(limit=limit)
    return [
        AlertItemResponse(
            alert_id=r.alert_id,
            event_id=r.event_id,
            alert_type=r.alert_type,
            severity=r.severity,
            timestamp=r.timestamp,
            wall_clock_time=r.wall_clock_time,
            status=r.status,
            message=r.message,
            snapshot_path=r.snapshot_path,
        )
        for r in records
    ]

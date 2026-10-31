"""Safety events querying endpoints."""

from fastapi import APIRouter, HTTPException, Request, Query
from typing import List, Optional
from level_crossing.api.schemas.events import EventResponse, EventDetailResponse, AlertResponse

router = APIRouter(prefix="/events", tags=["Events"])


@router.get("", response_model=List[EventResponse])
def list_events(request: Request, limit: int = Query(50, ge=1, le=500)) -> List[EventResponse]:
    service = request.app.state.safety_service
    records = service.list_events(limit=limit)
    return [
        EventResponse(
            event_id=r.event_id,
            track_id=r.track_id,
            rule_class=r.rule_class,
            zone_type=r.zone_type,
            initial_severity=r.initial_severity,
            current_severity=r.current_severity,
            crossing_state=r.crossing_state,
            start_time=r.start_time,
            end_time=r.end_time,
            status=r.status,
            unsafe_duration=r.unsafe_duration,
            escalation_count=r.escalation_count,
            created_at=r.created_at,
        )
        for r in records
    ]


@router.get("/{event_id}", response_model=EventDetailResponse)
def get_event(event_id: str, request: Request) -> EventDetailResponse:
    service = request.app.state.safety_service
    record = service.get_event(event_id)
    if not record:
        raise HTTPException(status_code=404, detail=f"Event {event_id} not found")

    alerts = service.get_event_alerts(event_id)
    alert_responses = [
        AlertResponse(
            alert_id=a.alert_id,
            event_id=a.event_id,
            alert_type=a.alert_type,
            severity=a.severity,
            timestamp=a.timestamp,
            wall_clock_time=a.wall_clock_time,
            status=a.status,
            message=a.message,
            snapshot_path=a.snapshot_path,
        )
        for a in alerts
    ]

    return EventDetailResponse(
        event_id=record.event_id,
        track_id=record.track_id,
        rule_class=record.rule_class,
        zone_type=record.zone_type,
        initial_severity=record.initial_severity,
        current_severity=record.current_severity,
        crossing_state=record.crossing_state,
        start_time=record.start_time,
        end_time=record.end_time,
        status=record.status,
        unsafe_duration=record.unsafe_duration,
        escalation_count=record.escalation_count,
        created_at=record.created_at,
        alerts=alert_responses,
    )

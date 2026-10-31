"""Telegram Emergency Dispatcher status and verification endpoints."""

import os
from typing import Dict, Any, Optional
from pathlib import Path
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from level_crossing.alerts.telegram_dispatcher import TelegramDispatcher

router = APIRouter(prefix="/telegram", tags=["Telegram Dispatcher"])


class TestAlertRequest(BaseModel):
    snapshot_filename: Optional[str] = None
    custom_message: Optional[str] = None


def mask_chat_id(cid: str) -> str:
    if not cid:
        return "None"
    if len(cid) <= 4:
        return "****"
    return f"{cid[:3]}***{cid[-3:]}"


@router.get("/status")
def get_telegram_status() -> Dict[str, Any]:
    """Returns Telegram dispatcher health and delivery telemetry without exposing the token."""
    dispatcher = TelegramDispatcher()

    # Find latest dispatched alert record if any
    sample_snaps = sorted(list(Path("data/snapshots").glob("*.jpg")), key=lambda p: p.stat().st_mtime, reverse=True)
    latest_snap = sample_snaps[0].name if sample_snaps else None

    return {
        "configured": dispatcher.is_configured,
        "bot_username": "@MyRailwaySafety_bot" if dispatcher.is_configured else "Unconfigured",
        "target_chat_id": mask_chat_id(dispatcher.chat_id),
        "location": dispatcher.location,
        "delivery_mode": "LIVE_PUSH" if dispatcher.is_configured else "SIMULATION_MODE",
        "total_dispatched": dispatcher.stats["dispatched"],
        "total_failed": dispatcher.stats["failed"],
        "total_suppressed": dispatcher.stats["suppressed"],
        "latest_evidence_snapshot": latest_snap,
    }


@router.post("/test")
def send_test_telegram_alert(req: TestAlertRequest = None) -> Dict[str, Any]:
    """Dispatches a verified emergency test alert with photographic evidence."""
    dispatcher = TelegramDispatcher()

    if not dispatcher.is_configured:
        raise HTTPException(
            status_code=400,
            detail="Telegram Bot Token or Chat ID not configured on backend (.env).",
        )

    # Resolve snapshot
    snap_dir = Path("data/snapshots")
    target_snap = None
    if req and req.snapshot_filename:
        p = snap_dir / req.snapshot_filename
        if p.exists():
            target_snap = p

    if not target_snap:
        sample_snaps = sorted(list(snap_dir.glob("*.jpg")), key=lambda p: p.stat().st_mtime, reverse=True)
        if sample_snaps:
            target_snap = sample_snaps[0]

    if not target_snap:
        raise HTTPException(
            status_code=404,
            detail="No CCTV evidence snapshot found in data/snapshots/ to attach.",
        )

    res = dispatcher.send_emergency_alert(
        image_path=target_snap,
        location=f"{dispatcher.location} (OPERATOR VERIFICATION TEST)",
        danger_level="CRITICAL",
        confidence=98.6,
        event_id="EVT-VERIFY-TEST",
        object_type="Person",
    )

    return {
        "success": res.get("success", False),
        "status_code": res.get("status_code", -1),
        "message_id": res.get("message_id"),
        "error": res.get("error"),
        "timestamp": res.get("timestamp"),
        "evidence_used": target_snap.name,
    }

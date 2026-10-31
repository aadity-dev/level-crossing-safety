"""Video scenario management, streaming, and replay triggers."""

from pathlib import Path
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Request, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from pydantic import BaseModel

from level_crossing.common.config import SystemConfig
from level_crossing.common.logger import get_logger
from level_crossing.pipeline.replay_pipeline import ReplayPipeline
from level_crossing.api.websocket_manager import ws_manager

logger = get_logger("videos_route")

router = APIRouter(prefix="/videos", tags=["Videos"])


class ReplayRequest(BaseModel):
    video_path: str
    output_path: Optional[str] = None
    enable_telegram: bool = True
    max_frames: Optional[int] = 300


class ReplayResponse(BaseModel):
    status: str
    message: str
    video_path: str
    frames_processed: Optional[int] = None
    alerts_generated: Optional[int] = None


@router.get("/scenarios")
def list_scenarios() -> List[Dict[str, Any]]:
    """Lists available validation scenario videos."""
    candidates = [
        {
            "id": "scenario_01",
            "title": "Scenario 01: Single Intruder Walking on Danger Track",
            "description": "Pedestrian crosses boundary into DANGER_TRACK while crossing is active.",
            "path": "data/controlled/validation/scenario_01_person_danger_track.mp4",
            "annotated_path": "data/controlled/validation/annotated_scenario_01.mp4",
        },
        {
            "id": "scenario_02",
            "title": "Scenario 02: Multi-Person Intrusion",
            "description": "Multiple pedestrians simultaneously traversing hazardous track sectors.",
            "path": "data/controlled/validation/scenario_02_multi_person_intrusion.mp4",
            "annotated_path": "data/annotated_runs/annotated_scenario_02.mp4",
        },
    ]

    results = []
    for c in candidates:
        has_orig = Path(c["path"]).exists()
        has_annotated = Path(c.get("annotated_path", "")).exists()
        results.append({
            **c,
            "available": has_orig,
            "has_annotated": has_annotated,
            "stream_url": f"/api/v1/videos/stream/{Path(c['annotated_path']).name}" if has_annotated else (f"/api/v1/videos/stream/{Path(c['path']).name}" if has_orig else None),
        })

    return results


@router.get("/stream/{filename}")
def stream_video_file(filename: str):
    """Serves video file with HTTP range headers for HTML5 video playback."""
    clean_name = Path(filename).name

    search_paths = [
        Path("data/controlled/validation") / clean_name,
        Path("data/annotated_runs") / clean_name,
        Path("data/uploads") / clean_name,
        Path("data") / clean_name,
    ]

    target = None
    for p in search_paths:
        if p.exists() and p.is_file():
            target = p
            break

    if not target:
        raise HTTPException(status_code=404, detail=f"Video file '{clean_name}' not found")

    return FileResponse(
        path=str(target),
        media_type="video/mp4",
        filename=clean_name,
    )


@router.post("/replay", response_model=ReplayResponse)
def trigger_replay(req: ReplayRequest, request: Request) -> ReplayResponse:
    """Verifies and triggers replay pipeline."""
    path = Path(req.video_path)
    if not path.exists():
        raise HTTPException(status_code=400, detail=f"Video file does not exist: {req.video_path}")

    return ReplayResponse(
        status="ready",
        message="Replay scenario verified and accessible",
        video_path=str(path),
    )


@router.post("/run-replay")
def run_replay_execution(req: ReplayRequest, background_tasks: BackgroundTasks) -> Dict[str, Any]:
    """Executes a replay run in the background, streaming events over WebSocket."""
    path = Path(req.video_path)
    if not path.exists():
        raise HTTPException(status_code=400, detail=f"Video file does not exist: {req.video_path}")

    def execute_in_bg():
        try:
            config = SystemConfig.load_from_dir("configs")
            pipeline = ReplayPipeline(
                config=config,
                enable_telegram=req.enable_telegram,
                save_to_db=True,
            )

            def on_frame(data):
                # Broadcast real-time telemetry over WebSocket
                ws_manager.broadcast_sync("telemetry_frame", {
                    "frame_idx": data.get("frame_idx", 0),
                    "timestamp": data.get("timestamp", 0.0),
                    "crossing_state": str(data.get("crossing_state")),
                    "highest_severity": str(data.get("highest_severity")),
                    "active_events_count": len(data.get("active_events", [])),
                })

            summary = pipeline.run(
                video_path=str(path),
                max_frames=req.max_frames,
                on_frame_callback=on_frame,
            )

            # Broadcast completion
            ws_manager.broadcast_sync("replay_completed", {
                "total_frames": summary.total_frames_processed,
                "events_generated": summary.events_generated,
                "alerts_generated": summary.alerts_generated,
                "average_fps": summary.average_fps,
            })
        except Exception as e:
            logger.error(f"Error in background replay execution: {e}")
            ws_manager.broadcast_sync("replay_error", {"error": str(e)})

    background_tasks.add_task(execute_in_bg)

    return {
        "status": "PROCESSING",
        "message": f"Scenario execution started for {path.name}",
        "video": path.name,
    }

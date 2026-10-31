"""Video scenario management, streaming, custom uploads, link resolution, and replay execution."""

import os
import urllib.parse
import urllib.request
import hashlib
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
from fastapi import APIRouter, Request, HTTPException, BackgroundTasks, UploadFile, File
from fastapi.responses import FileResponse
from pydantic import BaseModel

from level_crossing.common.config import SystemConfig
from level_crossing.common.types import CrossingState
from level_crossing.common.logger import get_logger
from level_crossing.pipeline.replay_pipeline import ReplayPipeline
from level_crossing.api.websocket_manager import ws_manager

logger = get_logger("videos_route")

router = APIRouter(prefix="/videos", tags=["Videos"])

UPLOAD_DIR = Path("data/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

ANNOTATED_DIR = Path("data/annotated_runs")
ANNOTATED_DIR.mkdir(parents=True, exist_ok=True)


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


class ResolveLinkRequest(BaseModel):
    url: str


class ExecuteInferenceRequest(BaseModel):
    video_source: str
    crossing_state: str = "TRAIN_APPROACHING"
    max_frames: Optional[int] = 300
    autonomous_train: bool = False
    enable_telegram: bool = True


def resolve_or_download_video(source_str: str) -> Tuple[str, Optional[str], bool]:
    """Resolves local paths, direct links, or YouTube videos using yt-dlp."""
    if not source_str:
        return "", "Please enter a valid video link or path.", False

    # 1. Local file path
    p = Path(source_str)
    if p.exists() and p.is_file():
        return str(p.resolve()), None, False

    # 2. Live RTSP / RTSPS stream
    if source_str.startswith(("rtsp://", "rtsps://")):
        return source_str, None, True

    # 3. HTTP / HTTPS link
    if source_str.startswith(("http://", "https://")):
        if ".m3u8" in source_str.lower():
            return source_str, None, True

        parsed_path = urllib.parse.urlparse(source_str).path
        ext = Path(parsed_path).suffix.lower()
        if ext in [".mp4", ".mov", ".avi", ".mkv"]:
            hashed = hashlib.md5(source_str.encode()).hexdigest()[:8]
            target_file = UPLOAD_DIR / f"web_{hashed}{ext}"
            if not target_file.exists():
                try:
                    urllib.request.urlretrieve(source_str, str(target_file))
                except Exception as e:
                    return "", f"Failed to download direct video URL: {e}", False
            return str(target_file.resolve()), None, False

        # YouTube, Vimeo, etc. using yt-dlp
        try:
            import yt_dlp

            hashed = hashlib.md5(source_str.encode()).hexdigest()[:8]
            out_tmpl = str(UPLOAD_DIR / f"yt_{hashed}.%(ext)s")
            ydl_opts = {
                "format": "bestvideo[ext=mp4][height<=720]+bestaudio[ext=m4a]/best[ext=mp4]/best",
                "outtmpl": out_tmpl,
                "quiet": True,
                "no_warnings": True,
                "noplaylist": True,
                "max_filesize": 100 * 1024 * 1024,
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(source_str, download=True)
                filename = ydl.prepare_filename(info)
                fpath = Path(filename)
                if not fpath.exists():
                    mp4_p = fpath.with_suffix(".mp4")
                    if mp4_p.exists():
                        filename = str(mp4_p)
            return str(Path(filename).resolve()), None, False
        except Exception as e:
            return "", f"Failed to resolve video stream from URL: {e}", False

    return "", f"Path or stream URL not found: {source_str}", False


@router.get("/scenarios")
def list_scenarios() -> List[Dict[str, Any]]:
    """Lists all available validation scenarios and custom uploaded video footage."""
    results = []

    # 1. Preset scenarios in validation folder
    preset_dir = Path("data/controlled/validation")
    if preset_dir.exists():
        for p in sorted(list(preset_dir.glob("*.mp4"))):
            if not p.name.startswith("annotated_"):
                results.append({
                    "id": p.stem,
                    "title": f"Preset: {p.name}",
                    "description": f"Standard Level Crossing scenario fixture ({p.name})",
                    "path": str(p),
                    "category": "PRESET",
                    "available": True,
                    "stream_url": f"/api/v1/videos/stream/{p.name}",
                })

    # 2. Uploaded videos
    if UPLOAD_DIR.exists():
        for u in sorted(list(UPLOAD_DIR.glob("*.*")), key=lambda f: f.stat().st_mtime, reverse=True):
            if u.suffix.lower() in [".mp4", ".mov", ".avi", ".mkv"]:
                results.append({
                    "id": u.stem,
                    "title": f"Custom: {u.name}",
                    "description": f"Custom uploaded crossing video ({u.stat().st_size / (1024*1024):.1f} MB)",
                    "path": str(u),
                    "category": "CUSTOM",
                    "available": True,
                    "stream_url": f"/api/v1/videos/stream/{u.name}",
                })

    return results


@router.post("/upload")
async def upload_custom_video(file: UploadFile = File(...)) -> Dict[str, Any]:
    """Uploads a custom video file (.mp4, .mov, .avi) for safety analysis."""
    safe_name = Path(file.filename).name
    target_path = UPLOAD_DIR / safe_name

    try:
        content = await file.read()
        target_path.write_bytes(content)
        size_mb = len(content) / (1024 * 1024)
        logger.info(f"Uploaded custom video: {safe_name} ({size_mb:.2f} MB)")
        return {
            "success": True,
            "filename": safe_name,
            "path": str(target_path.resolve()),
            "size_mb": round(size_mb, 2),
            "stream_url": f"/api/v1/videos/stream/{safe_name}",
        }
    except Exception as e:
        logger.error(f"Failed to upload video: {e}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {e}")


@router.post("/resolve-link")
def resolve_link(req: ResolveLinkRequest) -> Dict[str, Any]:
    """Resolves an arbitrary YouTube link, RTSP stream, or URL to a playable video."""
    resolved, err, is_stream = resolve_or_download_video(req.url)
    if err:
        return {"success": False, "error": err}
    return {
        "success": True,
        "resolved_path": resolved,
        "filename": Path(resolved).name,
        "is_stream": is_stream,
        "stream_url": f"/api/v1/videos/stream/{Path(resolved).name}",
    }


@router.post("/execute-inference")
def execute_inference_replay(req: ExecuteInferenceRequest) -> Dict[str, Any]:
    """Executes full YOLOv8 + ByteTrack + Heatmap safety inference over the selected video."""
    resolved_path, err, is_stream = resolve_or_download_video(req.video_source)
    if err or not resolved_path:
        raise HTTPException(status_code=400, detail=err or "Invalid video source")

    # Map crossing state
    try:
        crossing_enum = CrossingState(req.crossing_state)
    except ValueError:
        crossing_enum = CrossingState.TRAIN_APPROACHING

    video_stem = Path(resolved_path).stem
    annotated_output_path = ANNOTATED_DIR / f"annotated_{video_stem}.mp4"

    config = SystemConfig.load_from_dir("configs")
    pipeline = ReplayPipeline(
        config=config,
        save_to_db=True,
        enable_telegram=req.enable_telegram,
    )

    def on_frame(data):
        ws_manager.broadcast_sync("telemetry_frame", {
            "frame_idx": data.get("frame_idx", 0),
            "timestamp": data.get("timestamp", 0.0),
            "crossing_state": str(data.get("crossing_state")),
            "highest_severity": str(data.get("highest_severity")),
            "active_events_count": len(data.get("active_events", [])),
        })

    summary = pipeline.run(
        video_path=resolved_path,
        crossing_state_timeline=lambda t: crossing_enum,
        output_video_path=str(annotated_output_path),
        max_frames=req.max_frames,
        autonomous_train_sensing=req.autonomous_train,
        on_frame_callback=on_frame,
    )

    heatmap_filename = Path(summary.heatmap_path).name if summary.heatmap_path else None

    return {
        "success": True,
        "video_source": resolved_path,
        "total_frames_processed": summary.total_frames_processed,
        "duration_seconds": round(summary.duration_seconds, 2),
        "events_generated": summary.events_generated,
        "alerts_generated": summary.alerts_generated,
        "highest_severity_observed": summary.highest_severity_observed.value,
        "average_fps": round(summary.average_fps, 1),
        "elapsed_wall_time_sec": round(summary.elapsed_wall_time_sec, 2),
        "annotated_video_url": f"/api/v1/videos/stream/{annotated_output_path.name}",
        "heatmap_url": f"/api/v1/videos/heatmap/{heatmap_filename}" if heatmap_filename else None,
        "heatmap_analytics": summary.heatmap_analytics,
    }


@router.get("/heatmap/{filename}")
def get_heatmap_image(filename: str):
    """Serves the generated Spatial Hazard Density Heatmap PNG image."""
    clean_name = Path(filename).name
    p = ANNOTATED_DIR / clean_name
    if not p.exists() or not p.is_file():
        raise HTTPException(status_code=404, detail=f"Heatmap file '{clean_name}' not found")

    return FileResponse(path=str(p), media_type="image/png", filename=clean_name)


@router.get("/stream/{filename}")
def stream_video_file(filename: str):
    """Serves video file with HTTP range headers for HTML5 video playback."""
    clean_name = Path(filename).name

    search_paths = [
        ANNOTATED_DIR / clean_name,
        UPLOAD_DIR / clean_name,
        Path("data/controlled/validation") / clean_name,
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

            summary = pipeline.run(
                video_path=str(path),
                max_frames=req.max_frames,
            )

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

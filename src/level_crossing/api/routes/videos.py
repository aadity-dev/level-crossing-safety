"""Video and scenario replay triggers."""

from fastapi import APIRouter, Request, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional
from pathlib import Path

from level_crossing.pipeline.replay_pipeline import ReplayPipeline

router = APIRouter(prefix="/videos", tags=["Videos"])


class ReplayRequest(BaseModel):
    video_path: str
    output_path: Optional[str] = None


class ReplayResponse(BaseModel):
    status: str
    message: str
    video_path: str


@router.post("/replay", response_model=ReplayResponse)
def trigger_replay(req: ReplayRequest, request: Request) -> ReplayResponse:
    path = Path(req.video_path)
    if not path.exists():
        raise HTTPException(status_code=400, detail=f"Video file does not exist: {req.video_path}")

    return ReplayResponse(
        status="ready",
        message="Replay scenario verified and accessible",
        video_path=str(path),
    )

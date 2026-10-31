"""CCTV forensic snapshot image delivery and evidence endpoints."""

from pathlib import Path
from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

router = APIRouter(prefix="/evidence", tags=["Forensic Evidence"])

SNAPSHOT_DIR = Path("data/snapshots")


@router.get("")
def list_evidence_snapshots(limit: int = 50) -> List[Dict[str, Any]]:
    """Lists available forensic CCTV snapshots captured by the safety engine."""
    if not SNAPSHOT_DIR.exists():
        return []

    files = sorted(list(SNAPSHOT_DIR.glob("*.jpg")), key=lambda p: p.stat().st_mtime, reverse=True)[:limit]
    return [
        {
            "filename": f.name,
            "url": f"/api/v1/evidence/{f.name}",
            "size_bytes": f.stat().st_size,
            "modified_time": f.stat().st_mtime,
        }
        for f in files
    ]


@router.get("/{filename}")
def get_evidence_image(filename: str):
    """Serves the raw JPEG evidence snapshot captured during hazard confirmation."""
    # Sanitize filename against directory traversal
    clean_name = Path(filename).name
    file_path = SNAPSHOT_DIR / clean_name

    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail=f"Evidence image '{clean_name}' not found")

    return FileResponse(path=str(file_path), media_type="image/jpeg", filename=clean_name)

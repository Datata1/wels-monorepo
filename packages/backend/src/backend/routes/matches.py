import logging
from pathlib import Path

import cv2
from fastapi import APIRouter, HTTPException, Response

from backend.config import settings
from backend.db import query_duckdb
from backend.status import all_statuses, read_status
from backend.types import MatchMeta

THUMBNAIL_FRAME_INDEX = 42

logger = logging.getLogger(__name__)
router = APIRouter()


def get_absolute_video_path(db_path: str) -> Path:
    """Helper: Löst den absoluten Pfad des Videos auf."""
    video_path = Path(db_path)
    if not video_path.is_absolute():
        video_path = Path(settings.video_input_dir) / video_path
    return video_path


def extract_frame_as_jpeg(video_path: Path, frame_index: int) -> bytes:
    """Helper: Extrahiert sicher einen Frame aus einem Video via OpenCV."""
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise HTTPException(status_code=500, detail="Could not open video file")

    try:
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_index)
        ret, frame = cap.read()
        if not ret:
            raise ValueError("Konnte Frame nicht lesen")

        success, buffer = cv2.imencode(".jpg", frame)
        if not success:
            raise HTTPException(status_code=500, detail="Could not encode frame to JPEG")

        return buffer.tobytes()
    finally:
        cap.release()


@router.get("/matches", response_model=list[MatchMeta])
def list_matches():
    """Returns all matches — both completed (from DuckDB) and in-progress (from status files)."""
    rows = list(query_duckdb("SELECT * FROM matches"))
    result: list[MatchMeta] = []
    seen_ids: set[str] = set()

    for row in rows:
        video_path = get_absolute_video_path(row["video_path"])

        if not video_path.exists():
            logger.debug("Video file missing for match_id %s at %s", row["match_id"], video_path)
            continue

        fps = row.get("fps") or 1.0
        total_seconds = int(row.get("total_frames", 0) / fps)
        mins, secs = divmod(total_seconds, 60)

        date_str = row["ingested_at"].isoformat() if row.get("ingested_at") else None
        status = read_status(row["match_id"])

        seen_ids.add(row["match_id"])
        result.append(
            MatchMeta(
                match_id=row["match_id"],
                file_name=video_path.name,
                video_path=str(video_path),
                fps=row["fps"],
                total_frames=row["total_frames"],
                duration=f"{mins:02d}:{secs:02d}",
                ingested_at=date_str,
                status=status,
            )
        )

    # Surface matches that have a status file but aren't in DuckDB yet
    # (e.g. still processing, or failed before DuckDB write)
    for match_id, status in all_statuses().items():
        if match_id in seen_ids:
            continue
        result.append(
            MatchMeta(
                match_id=match_id,
                file_name="",
                video_path="",
                fps=0.0,
                total_frames=0,
                status=status,
            )
        )

    return result


@router.get("/matches/{match_id}/thumbnail")
def get_match_thumbnail(match_id: str):
    """Extracts a specific frame from the video and returns it as a JPEG image."""

    query = "SELECT video_path FROM matches WHERE match_id = ?"
    rows = list(query_duckdb(query, [match_id]))

    if not rows:
        raise HTTPException(status_code=404, detail="Match not found")

    video_path = get_absolute_video_path(rows[0]["video_path"])

    if not video_path.exists():
        raise HTTPException(status_code=404, detail="Video file not found")

    image_bytes = extract_frame_as_jpeg(video_path, THUMBNAIL_FRAME_INDEX)

    return Response(content=image_bytes, media_type="image/jpeg")

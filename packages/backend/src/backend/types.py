"""
Pydantic model for match/video metadata.
"""

from pydantic import BaseModel


class MatchMeta(BaseModel):
    match_id: str
    file_name: str
    video_path: str
    fps: float
    total_frames: int
    date: str | None = None
    duration: str | None = None
    ingested_at: str | None = None

"""
Pydantic model for match/video metadata.
"""

from typing import Literal

from pydantic import BaseModel

type MatchStatus = Literal["processing", "done", "failed", "unknown"]


class MatchMeta(BaseModel):
    match_id: str
    file_name: str
    video_path: str
    fps: float
    total_frames: int
    status: MatchStatus = "unknown"
    date: str | None = None
    duration: str | None = None
    ingested_at: str | None = None

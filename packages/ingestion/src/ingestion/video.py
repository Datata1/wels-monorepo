from collections.abc import Iterator
from pathlib import Path
from typing import NamedTuple

import cv2
import numpy as np


class VideoFrame(NamedTuple):
    frame_id: int
    frame: np.ndarray  # type: ignore[type-arg]
    timestamp_s: float
    fps: float
    total_frames: int


def iter_frames(video_path: Path) -> Iterator[VideoFrame]:
    """
    Yield one VideoFrame per frame in display order.

    Uses a try/finally so the VideoCapture is always released, even if the
    caller breaks out of the loop early.
    """
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise ValueError(f"Cannot open video: {video_path}")

    fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    frame_id = 0

    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            yield VideoFrame(
                frame_id=frame_id,
                frame=frame,
                timestamp_s=frame_id / fps,
                fps=fps,
                total_frames=total_frames,
            )
            frame_id += 1
    finally:
        cap.release()

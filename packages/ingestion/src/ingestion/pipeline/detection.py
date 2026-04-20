"""
Person detector.

Port target: CV-POC-Wels/pipeline/detector.py
Key decisions made vs. POC:
  - Returns typed Detection dataclasses instead of raw dicts
  - track_id is assigned by ByteTrack (built into ultralytics); this class does not
    implement its own tracker
  - Ball detection is a separate stage (see ball.py)
"""

from __future__ import annotations

import numpy as np

from ingestion.types import Detection

try:
    import ultralytics as _ultralytics  # noqa: F401
    AVAILABLE: bool = True
except ImportError:
    AVAILABLE = False


class PersonDetector:
    """YOLO11 + ByteTrack player detector."""

    def __init__(
        self,
        model_path: str,
        confidence: float,
        max_persons: int,
        device: str,
    ) -> None:
        # TODO: port from CV-POC-Wels/pipeline/detector.py
        #   - load ultralytics YOLO model at model_path
        #   - store thresholds and device
        raise NotImplementedError

    def detect(self, frame: np.ndarray) -> list[Detection]:  # type: ignore[type-arg]
        """
        Run YOLO11 + ByteTrack on one frame.

        Returns:
            Tracked player detections sorted by confidence (track_id is stable
            across frames via ByteTrack).
        """
        # TODO: port from CV-POC-Wels/pipeline/detector.py — detect_and_track
        #   1. Run YOLO inference with tracker="bytetrack.yaml", classes=[0] (person)
        #   2. Parse boxes → Detection dataclasses
        #   3. Sort by confidence descending, cap at max_persons
        raise NotImplementedError

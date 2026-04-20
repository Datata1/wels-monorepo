"""
Ball detector.

Port target: CV-POC-Wels/pipeline/detector.py
Key decisions made vs. POC:
  - Separate class from PersonDetector so both can be developed independently
  - Returns a single Detection (the highest-confidence ball) or None
  - Supports two model modes:
      Generic YOLO (COCO) — uses class 32 (sports ball)
      Custom ball model   — single-class model, uses class 0
"""

from __future__ import annotations

import numpy as np

from ingestion.types import Detection

try:
    import ultralytics as _ultralytics  # noqa: F401
    AVAILABLE: bool = True
except ImportError:
    AVAILABLE = False


class BallDetector:
    """YOLO-based handball detector."""

    def __init__(
        self,
        model_path: str,
        confidence: float,
        device: str,
    ) -> None:
        # TODO: port from CV-POC-Wels/pipeline/detector.py
        #   - load YOLO model at model_path
        #   - if custom single-class ball model: target class 0
        #   - if generic COCO model: target class 32 (sports ball)
        #   - store confidence threshold and device
        raise NotImplementedError

    def detect(self, frame: np.ndarray) -> Detection | None:  # type: ignore[type-arg]
        """
        Run YOLO on one frame and return the highest-confidence ball detection.

        Returns None if no ball is visible above the confidence threshold.
        track_id is set to -1 (ball tracking is not required for analytics).
        """
        # TODO: port from CV-POC-Wels/pipeline/detector.py — detect_and_track (balls branch)
        #   1. Run YOLO on frame (no tracker needed for ball)
        #   2. Filter to ball class, take highest-confidence detection
        #   3. Return Detection or None
        raise NotImplementedError

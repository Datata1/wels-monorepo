"""
Player and ball detector.

Port target: CV-POC-Wels/pipeline/detector.py
Key decisions made vs. POC:
  - Returns typed Detection dataclasses instead of raw dicts
  - Ball detection is part of this class (not separate), selecting the highest-confidence
    `sports ball` class detection from the same YOLO pass
  - track_id is assigned by ByteTrack (built into ultralytics); this class does not
    implement its own tracker
"""

from __future__ import annotations

import numpy as np

from ingestion.types import Detection


class Detector:
    """YOLO11 + ByteTrack player and ball detector."""

    def __init__(
        self,
        model_path: str,
        ball_model_path: str | None,
        confidence: float,
        ball_confidence: float,
        max_persons: int,
        device: str,
    ) -> None:
        # TODO: port from CV-POC-Wels/pipeline/detector.py
        #   - load ultralytics YOLO model at model_path
        #   - load optional custom ball model at ball_model_path (or reuse main model)
        #   - store thresholds and device
        raise NotImplementedError

    def detect(self, frame: np.ndarray) -> tuple[list[Detection], Detection | None]:
        """
        Run detection + ByteTrack on one frame.

        Returns:
            players: tracked player detections (track_id is stable across frames)
            ball:    highest-confidence ball detection, or None if not visible
        """
        # TODO: port from CV-POC-Wels/pipeline/detector.py — Detector.process_frame
        #   1. Run YOLO inference on frame (person class)
        #   2. Apply ByteTrack to get stable track_ids
        #   3. Run ball model (or same model, sports ball class)
        #   4. Convert raw results → Detection dataclasses
        raise NotImplementedError

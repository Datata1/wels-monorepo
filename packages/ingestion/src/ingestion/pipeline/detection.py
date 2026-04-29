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

from typing import Any

import numpy as np

from ingestion.types import BoundingBox, Detection

try:
    import ultralytics

    AVAILABLE: bool = True
except ImportError:
    AVAILABLE = False

_PERSON_CLASS = 0  # COCO class ID


class PersonDetector:
    """YOLO11 + ByteTrack player detector."""

    _model: Any  # ultralytics.YOLO — imported lazily to respect AVAILABLE guard

    def __init__(
        self,
        model_path: str,
        confidence: float,
        max_persons: int,
        device: str,
        imgsz: int = 1280,
        half: bool = False,
    ) -> None:
        self._model = ultralytics.YOLO(model_path)
        self._model.to(device)
        self._confidence = confidence
        self._max_persons = max_persons
        self._imgsz = imgsz
        # FP16 only makes sense on CUDA; ultralytics raises if half=True on CPU
        self._half = half and device != "cpu"

    def detect(self, frame: np.ndarray) -> list[Detection]:  # type: ignore[type-arg]
        """
        Run YOLO11 + ByteTrack on one frame.

        Returns tracked player detections sorted by confidence descending.
        track_id is stable across frames via ByteTrack; -1 if tracking is lost.
        """
        results = self._model.track(
            frame,
            classes=[_PERSON_CLASS],
            conf=self._confidence,
            imgsz=self._imgsz,
            half=self._half,
            persist=True,
            tracker="bytetrack.yaml",
            verbose=False,
        )
        detections: list[Detection] = []
        for r in results:
            if r.boxes is None:
                continue
            for box in r.boxes:
                xyxy = box.xyxy[0].cpu().numpy().astype(int)
                x1, y1, x2, y2 = int(xyxy[0]), int(xyxy[1]), int(xyxy[2]), int(xyxy[3])
                track_id = int(box.id[0]) if box.id is not None else -1
                detections.append(
                    Detection(
                        track_id=track_id,
                        bbox=BoundingBox(x1, y1, x2, y2),
                        confidence=float(box.conf[0]),
                    )
                )
        detections.sort(key=lambda d: d.confidence, reverse=True)
        return detections[: self._max_persons]

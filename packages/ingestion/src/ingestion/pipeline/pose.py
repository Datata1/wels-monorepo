"""
Pose estimator.

Port target: CV-POC-Wels/pipeline/pose.py
Key decisions made vs. POC:
  - Batch processes all player detections in a single forward pass
  - Matches pose results back to detections by center-distance (same as POC)
  - Returns None for a detection if no pose could be matched (below distance threshold)
"""

from __future__ import annotations

import numpy as np

from ingestion.types import Detection, Keypoint


class PoseEstimator:
    """YOLO11-pose batch pose estimator."""

    def __init__(self, model_path: str, device: str) -> None:
        # TODO: port from CV-POC-Wels/pipeline/pose.py — PoseEstimator.__init__
        #   - load ultralytics YOLO pose model
        raise NotImplementedError

    def estimate(
        self,
        frame: np.ndarray,
        detections: list[Detection],
    ) -> list[list[Keypoint] | None]:
        """
        Estimate pose for each detection in one GPU forward pass.

        Returns one entry per detection in the same order as the input list.
        Returns None for detections where no matching pose was found.

        Each pose is a list of 17 COCO keypoints (nose → right ankle).
        """
        # TODO: port from CV-POC-Wels/pipeline/pose.py — PoseEstimator.estimate
        #   1. Crop player regions (or run on full frame with person crops)
        #   2. Single forward pass on GPU
        #   3. Match results back to input detections via center distance
        #   4. Convert to list[Keypoint]
        raise NotImplementedError

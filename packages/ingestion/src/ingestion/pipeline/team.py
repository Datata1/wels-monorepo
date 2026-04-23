"""
Team classifier.

Port target: CV-POC-Wels/pipeline/team.py
Key decisions made vs. POC:
  - Explicit warm-up phase: collect() → fit() → classify()
    This makes the state machine clear instead of implicit in the POC
  - n_teams=2 covers the normal case; referees are classified as "unknown"
    after fitting and can be post-processed by the orchestrator
  - Team label assignment ("A" vs "B") is consistent within a match but
    arbitrary across matches — the backend layer assigns real team names
"""

from __future__ import annotations

import numpy as np

from ingestion.types import BoundingBox

AVAILABLE: bool = True  # scikit-learn and opencv are core deps

_UNKNOWN = "unknown"


class TeamClassifier:
    """
    Jersey-color K-Means team classifier.

    Usage:
        classifier = TeamClassifier(n_teams=2)

        # Warm-up: collect samples from the first N frames
        for frame, detections in warmup_frames:
            for det in detections:
                classifier.collect(frame, det.bbox)

        classifier.fit()

        # Classification: one call per player per frame
        team = classifier.classify(frame, detection.bbox)  # "A" | "B" | "unknown"
    """

    def __init__(self, n_teams: int = 2) -> None:
        self._n_teams = n_teams
        self._fitted = False
        # TODO: port from CV-POC-Wels/pipeline/team.py — TeamClassifier.__init__
        #   - initialise sample buffer (list of HSV histograms)
        #   - store KMeans instance (scikit-learn)

    @property
    def is_fitted(self) -> bool:
        return self._fitted

    def collect(self, frame: np.ndarray, bbox: BoundingBox) -> None:
        """
        Accumulate one jersey color histogram sample.
        Call this for every player detection during the warm-up phase.
        """
        # TODO: port from CV-POC-Wels/pipeline/team.py
        #   1. Crop torso region from frame using bbox (upper ~40% of box)
        #   2. Convert BGR→HSV
        #   3. Compute HSV histogram (hue channel, 16 bins)
        #   4. Append to sample buffer
        raise NotImplementedError

    def fit(self) -> None:
        """
        Fit K-Means on the accumulated samples.
        Raises RuntimeError if fewer than 2 * n_teams samples were collected.
        """
        # TODO: port from CV-POC-Wels/pipeline/team.py
        #   1. Stack sample buffer into array
        #   2. Fit KMeans(n_clusters=n_teams)
        #   3. Assign stable labels ("A"/"B") — e.g. sort cluster centers by mean hue
        #   4. Set self._fitted = True
        raise NotImplementedError

    def classify(self, frame: np.ndarray, bbox: BoundingBox) -> str:
        """
        Classify one player as "A", "B", or "unknown".
        Returns "unknown" if the classifier has not been fitted yet.
        """
        if not self._fitted:
            return _UNKNOWN
        # TODO: port from CV-POC-Wels/pipeline/team.py
        #   1. Extract HSV histogram from torso crop (same as collect)
        #   2. Predict cluster label with fitted KMeans
        #   3. Map cluster index to "A" / "B"
        raise NotImplementedError

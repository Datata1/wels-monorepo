"""
Court mapper — pixel coordinates → real-world court coordinates.

Port target: CV-POC-Wels/pipeline/court.py
Key decisions made vs. POC:
  - CourtMapper is immutable after construction (calibration is fixed per match)
  - transform() returns None instead of raising when a point is outside the court
    region, so the orchestrator can set court_pos=None cleanly
  - Calibration is loaded from a JSON file with the format used in the POC:
      {"src": [[px, py], ...], "dst": [[cx, cy], ...]}
    where dst coordinates are in metres on the standard 40m x 20m court
"""

from __future__ import annotations

import json
from pathlib import Path

AVAILABLE: bool = True  # opencv is a core dep


class CourtMapper:
    """Homography-based pixel-to-court coordinate transformer."""

    def __init__(self, src_points: list[list[float]], dst_points: list[list[float]]) -> None:
        # TODO: port from CV-POC-Wels/pipeline/court.py — CourtMapper.__init__
        #   - call cv2.findHomography(src_points, dst_points)
        #   - store the 3x3 homography matrix
        raise NotImplementedError

    @classmethod
    def from_file(cls, path: Path) -> CourtMapper:
        """Load calibration from a JSON file produced by calibrate.py."""
        data = json.loads(path.read_text())
        return cls(data["src"], data["dst"])

    def transform(self, pixel_pos: tuple[float, float]) -> tuple[float, float] | None:
        """
        Map a pixel coordinate to court coordinates (metres).

        Returns None if the transformed point falls outside the valid court
        boundaries (0-40m x 0-20m), which happens when the camera is zoomed in
        on a region that cannot be reliably mapped.
        """
        # TODO: port from CV-POC-Wels/pipeline/court.py — CourtMapper.to_court
        #   1. Apply homography matrix to pixel_pos
        #   2. Check if result is within [0,40] x [0,20]
        #   3. Return (x, y) or None
        raise NotImplementedError

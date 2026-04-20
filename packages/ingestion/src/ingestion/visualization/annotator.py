"""
Frame annotator — draws pipeline output onto raw video frames.

Uses only cv2 + numpy (core deps, no GPU required).
"""

from __future__ import annotations

import cv2
import numpy as np

from ingestion.types import BallState, FrameState, PlayerState

_FONT = cv2.FONT_HERSHEY_SIMPLEX
_TEAM_COLORS: dict[str, tuple[int, int, int]] = {
    "A": (255, 100, 0),
    "B": (0, 100, 255),
    "unknown": (180, 180, 180),
}
_BALL_COLOR: tuple[int, int, int] = (0, 255, 255)


class FrameAnnotator:
    """Draws bounding boxes, team labels, ball, and HUD onto a copy of each frame."""

    def annotate(self, frame: np.ndarray, state: FrameState) -> np.ndarray:  # type: ignore[type-arg]
        out: np.ndarray = frame.copy()  # type: ignore[type-arg]
        for player in state.players:
            _draw_player(out, player)
        if state.ball is not None:
            _draw_ball(out, state.ball)
        _draw_hud(out, state)
        return out


def _draw_player(frame: np.ndarray, p: PlayerState) -> None:  # type: ignore[type-arg]
    b = p.bbox
    color = _TEAM_COLORS.get(p.team, _TEAM_COLORS["unknown"])
    cv2.rectangle(frame, (b.x1, b.y1), (b.x2, b.y2), color, 2)
    label = f"#{p.track_id} {p.team} {p.confidence:.0%}"
    cv2.putText(frame, label, (b.x1, max(b.y1 - 6, 10)), _FONT, 0.45, color, 1, cv2.LINE_AA)


def _draw_ball(frame: np.ndarray, ball: BallState) -> None:  # type: ignore[type-arg]
    cx = int(ball.bbox.center[0])
    cy = int(ball.bbox.center[1])
    r = max(ball.bbox.width // 2, 8)
    cv2.circle(frame, (cx, cy), r, _BALL_COLOR, 2)


def _draw_hud(frame: np.ndarray, state: FrameState) -> None:  # type: ignore[type-arg]
    lines = [
        f"Frame {state.frame_id} | {state.timestamp_s:.1f}s",
        f"Players: {state.on_court_count}/{state.player_count}",
    ]
    for i, line in enumerate(lines):
        y = 22 + i * 20
        cv2.putText(frame, line, (8, y), _FONT, 0.5, (255, 255, 255), 1, cv2.LINE_AA)

"""Pipeline status tracking via simple text files on disk.

Each match gets a file at ``data/output/status/<match_id>.status`` containing one
of: ``processing``, ``done``, ``failed``.  This is the single source of truth for
pipeline state — independent of DuckDB (which is locked while the pipeline runs).
"""

from pathlib import Path
from typing import Literal

type PipelineStatus = Literal["processing", "done", "failed", "unknown"]

# Resolve monorepo root the same way upload.py does
_MONOREPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent
STATUS_DIR = _MONOREPO_ROOT / "data" / "output" / "status"


def write_status(match_id: str, status: PipelineStatus) -> None:
    """Persist *status* for *match_id* to disk."""
    STATUS_DIR.mkdir(parents=True, exist_ok=True)
    (STATUS_DIR / f"{match_id}.status").write_text(status)


def read_status(match_id: str) -> PipelineStatus:
    """Return the current pipeline status for *match_id*."""
    path = STATUS_DIR / f"{match_id}.status"
    if not path.exists():
        return "unknown"
    text = path.read_text().strip()
    if text == "processing":
        return "processing"
    if text == "done":
        return "done"
    if text == "failed":
        return "failed"
    return "unknown"


def all_statuses() -> dict[str, PipelineStatus]:
    """Return ``{match_id: status}`` for every status file on disk."""
    if not STATUS_DIR.exists():
        return {}
    result: dict[str, PipelineStatus] = {}
    for p in STATUS_DIR.glob("*.status"):
        match_id = p.stem
        result[match_id] = read_status(match_id)
    return result

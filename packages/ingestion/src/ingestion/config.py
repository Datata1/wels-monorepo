from pathlib import Path

from pydantic_settings import BaseSettings

# Anchor to repo root regardless of the working directory the CLI is invoked from.
# packages/ingestion/src/ingestion/config.py → go up 4 levels → repo root
_REPO_ROOT = Path(__file__).resolve().parents[4]


class IngestionSettings(BaseSettings):
    model_config = {"env_prefix": "WELS_"}

    # Model identifiers — resolved against models_dir if not absolute paths
    detection_model: str = "yolo26m.pt"
    ball_model: str = "yolo11m.pt"  # generic COCO model (class 32) or a custom ball model

    # Detection thresholds
    detection_confidence: float = 0.3
    ball_confidence: float = 0.25
    max_persons: int = 20
    n_teams: int = 2

    # Inference performance
    # imgsz: larger = more accurate on small/distant players, slower.
    #   1280 — high quality (original default)
    #    960 — good balance; ~1.7x faster than 1280
    #    640 — fastest; may miss distant players on wide-angle shots
    detection_imgsz: int = 1280
    # half: FP16 inference — ~1.5-2x faster on RTX 30xx/40xx, no quality loss.
    # Automatically disabled when device="cpu" (CPU doesn't support FP16 YOLO).
    half: bool = True

    device: str = "cuda"  # set to "cpu" on machines without a GPU

    # Storage — absolute paths anchored to repo root
    duckdb_path: Path = _REPO_ROOT / "data/output/duckdb/matches.duckdb"
    models_dir: Path = _REPO_ROOT / "data/input/models"

    # Court calibration JSON file (optional — no court mapping if unset)
    calibration_path: Path | None = None

    # How many frames to accumulate before fitting the team classifier
    team_warmup_frames: int = 150


settings = IngestionSettings()

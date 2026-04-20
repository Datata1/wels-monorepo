"""
CLI entry point: wels-ingest

Usage:
    wels-ingest <video_path> <match_id> [options]

Examples:
    wels-ingest match.mp4 2026-04-13_wels_vs_linz
    wels-ingest match.mp4 2026-04-13_wels_vs_linz --no-pose --device cpu
    wels-ingest match.mp4 2026-04-13_wels_vs_linz --calibration court.json
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from ingestion.config import IngestionSettings
from ingestion.orchestrator import IngestionOrchestrator


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="wels-ingest",
        description="Process a handball match video into the WELS DuckDB database.",
    )
    p.add_argument("video", type=Path, help="Path to the match video file")
    p.add_argument("match_id", help="Unique match identifier (e.g. 2026-04-13_wels_vs_linz)")
    p.add_argument("--device", default=None, help="Inference device: 'cuda' or 'cpu'")
    p.add_argument("--calibration", type=Path, default=None, help="Court calibration JSON file")
    p.add_argument("--db", type=Path, default=None, help="Override DuckDB path")
    p.add_argument(
        "--output-video",
        type=Path,
        default=None,
        metavar="PATH",
        help="Write annotated video with bounding boxes to this path (e.g. out.mp4)",
    )
    p.add_argument("--verbose", "-v", action="store_true")
    return p


def main(argv: list[str] | None = None) -> None:
    args = _build_parser().parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s  %(levelname)-8s  %(message)s",
        datefmt="%H:%M:%S",
    )

    if not args.video.exists():
        print(f"Error: video file not found: {args.video}", file=sys.stderr)
        sys.exit(1)

    # Override settings from CLI flags where provided
    overrides: dict[str, object] = {}
    if args.device:
        overrides["device"] = args.device
    if args.calibration:
        overrides["calibration_path"] = args.calibration
    if args.db:
        overrides["duckdb_path"] = args.db

    settings = IngestionSettings(**overrides)  # type: ignore[arg-type]
    orchestrator = IngestionOrchestrator(settings)

    try:
        orchestrator.run(args.video, args.match_id, output_video_path=args.output_video)
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

import logging
import os
import subprocess
import sys
import threading
import uuid
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse

from backend.status import write_status

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["api"])

# Configure paths - absolute paths from monorepo root
# upload.py is at: packages/backend/src/backend/routes/upload.py
# Need 6 parents to get to monorepo root: routes -> backend -> src -> backend -> packages -> root
MONOREPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent.parent
DATA_INPUT_VIDEOS = MONOREPO_ROOT / "data" / "input" / "videos"
DATA_OUTPUT_VIDEOS = MONOREPO_ROOT / "data" / "output" / "videos"


def run_ingestion_pipeline(match_id: str, video_path: str) -> None:
    """Run the wels-ingest pipeline in a background thread, streaming output live."""
    DATA_OUTPUT_VIDEOS.mkdir(parents=True, exist_ok=True)
    output_video = DATA_OUTPUT_VIDEOS / f"{match_id}_annotated.mp4"
    ingestion_dir = MONOREPO_ROOT / "packages" / "ingestion"

    cmd = [
        "uv",
        "run",
        "--extra",
        "cv",
        "wels-ingest",
        video_path,
        match_id,
        "--output-video",
        str(output_video),
        "--imgsz",
        "640",
    ]
    if sys.platform == "darwin":
        cmd += ["--device", "cpu"]

    try:
        env = os.environ.copy()
        env.pop("VIRTUAL_ENV", None)

        proc = subprocess.Popen(
            cmd,
            cwd=str(ingestion_dir),
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        assert proc.stdout is not None
        for line in proc.stdout:
            logger.info("[ingest %s] %s", match_id, line.rstrip())

        returncode = proc.wait()
        if returncode != 0:
            logger.error("Ingestion failed for %s (exit code %d)", match_id, returncode)
            write_status(match_id, "failed")
        else:
            write_status(match_id, "done")
    except Exception as e:
        logger.error("Error running ingestion for %s: %s", match_id, e)
        write_status(match_id, "failed")


# Module-level singleton for FastAPI File default
_file_default = File()


@router.post("/videos/upload")
async def upload_video(
    file: UploadFile = _file_default,
) -> JSONResponse:
    """Upload a video file to the input videos directory and start processing."""
    # Ensure directory exists
    DATA_INPUT_VIDEOS.mkdir(parents=True, exist_ok=True)

    # Validate file type
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    file_ext = file.filename.split(".")[-1].lower()
    if file_ext not in ["mp4", "avi", "mov", "mkv"]:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file format: {file_ext}. Supported: mp4, avi, mov, mkv",
        )

    # Generate unique match_id and save file
    match_id = str(uuid.uuid4())[:8]
    safe_filename = f"{match_id}_{file.filename}"
    file_path = DATA_INPUT_VIDEOS / safe_filename

    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)

    # Mark as processing before spawning the worker thread
    write_status(match_id, "processing")

    # Start ingestion pipeline in a background thread
    thread = threading.Thread(target=run_ingestion_pipeline, args=(match_id, str(file_path)))
    thread.start()

    return JSONResponse(
        content={
            "match_id": match_id,
            "filename": safe_filename,
            "status": "processing",
            "message": "Video uploaded successfully. Processing has started.",
        }
    )


@router.get("/videos/{match_id}/output")
async def get_output_video(match_id: str) -> JSONResponse:
    """Get the output video status for a match, based on the status file."""
    from backend.status import read_status

    status = read_status(match_id)
    output_video = DATA_OUTPUT_VIDEOS / f"{match_id}_annotated.mp4"

    if status == "done" and output_video.exists():
        return JSONResponse(
            content={
                "match_id": match_id,
                "video_path": str(output_video),
                "status": "ready",
            }
        )

    # Map status file values to API response values
    api_status = "processing" if status == "processing" else status
    return JSONResponse(
        content={
            "match_id": match_id,
            "video_path": None,
            "status": api_status,
        }
    )


@router.get("/videos/{match_id}/output/video")
async def stream_output_video(match_id: str):
    """Stream the annotated output video file."""
    from fastapi.responses import FileResponse

    annotated = DATA_OUTPUT_VIDEOS / f"{match_id}_annotated.mp4"
    if annotated.exists():
        return FileResponse(
            path=str(annotated), media_type="video/mp4", filename=f"{match_id}_annotated.mp4"
        )

    raise HTTPException(status_code=404, detail="Output video not found")

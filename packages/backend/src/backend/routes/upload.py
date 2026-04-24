import subprocess
import threading
import uuid
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import FileResponse, JSONResponse

router = APIRouter(prefix="/api/v1", tags=["api"])

# Configure paths - absolute paths from monorepo root
MONOREPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent
DATA_INPUT_VIDEOS = MONOREPO_ROOT / "data" / "videos"
DATA_OUTPUT_VIDEOS = MONOREPO_ROOT / "data" / "output" / "videos"


def run_ingestion_pipeline(match_id: str, video_path: str) -> None:
    """Run the wels-ingest pipeline in a background thread."""
    # Ensure output directory exists
    DATA_OUTPUT_VIDEOS.mkdir(parents=True, exist_ok=True)

    # Output video path
    output_video = DATA_OUTPUT_VIDEOS / f"{match_id}_annotated.mp4"

    try:
        # Run wels-ingest from the ingestion package
        result = subprocess.run(
            [
                "uv",
                "run",
                "-p",
                "wels-ingestion",
                "wels-ingest",
                video_path,
                match_id,
                "--output-video",
                str(output_video),
            ],
            cwd=str(MONOREPO_ROOT),
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            # Log error but don't fail the request
            print(f"Ingestion failed for {match_id}: {result.stderr}")
    except Exception as e:
        print(f"Error running ingestion for {match_id}: {e}")


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
    """Get the output video path for a match."""
    output_video = DATA_OUTPUT_VIDEOS / f"{match_id}_annotated.mp4"

    if output_video.exists():
        return JSONResponse(
            content={
                "match_id": match_id,
                "video_path": str(output_video),
                "status": "ready",
            }
        )
    else:
        return JSONResponse(
            content={
                "match_id": match_id,
                "video_path": None,
                "status": "processing",
            }
        )


@router.get("/videos/{match_id}/output/video")
async def stream_output_video(match_id: str):
    """Stream the output video file."""
    output_video = DATA_OUTPUT_VIDEOS / f"{match_id}_annotated.mp4"

    if output_video.exists():
        return FileResponse(
            path=str(output_video),
            media_type="video/mp4",
            filename=f"{match_id}_annotated.mp4",
        )
    else:
        raise HTTPException(status_code=404, detail="Output video not found")

import shutil

from fastapi import APIRouter, BackgroundTasks, File, Form, HTTPException, UploadFile, status

from app.core.config import settings
from app.models.clip import ClipJobResponse, CreateClipJobRequest
from app.services.coordinator import (
    create_new_job,
    get_job_state,
    list_all_jobs,
    run_pipeline_for_job,
)

router = APIRouter()


@router.post(
    "/jobs",
    response_model=ClipJobResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Create a new clip job with a YouTube URL or video link",
)
def create_job(request: CreateClipJobRequest, background_tasks: BackgroundTasks):
    if not request.video_url:
        raise HTTPException(
            status_code=400, detail="video_url is required to start a link-based job"
        )

    job = create_new_job(
        video_source=request.video_url,
        video_url=request.video_url,
        webhook_url=request.webhook_url,
    )
    background_tasks.add_task(
        run_pipeline_for_job,
        job.job_id,
        None,
        request.video_url,
        request.min_duration_seconds,
        request.max_duration_seconds,
    )
    return job


@router.post(
    "/upload",
    response_model=ClipJobResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Upload a video file for clipping and agent processing",
)
async def upload_video(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(..., description="Video file (MP4, MKV, MOV, WebM)"),
    target_aspect_ratio: str = Form(default="9:16"),
    min_duration_seconds: int = Form(default=15),
    max_duration_seconds: int = Form(default=60),
    generate_subtitles: bool = Form(default=True),
    webhook_url: str | None = Form(default=None),
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="Missing file name")

    settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    destination_path = settings.UPLOAD_DIR / file.filename

    # Save uploaded file safely
    with destination_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    job = create_new_job(
        video_source=file.filename,
        video_filename=file.filename,
        webhook_url=webhook_url,
    )

    background_tasks.add_task(
        run_pipeline_for_job,
        job.job_id,
        destination_path,
        None,
        min_duration_seconds,
        max_duration_seconds,
    )
    return job


@router.get(
    "/jobs/{job_id}",
    response_model=ClipJobResponse,
    summary="Get status and details of a clip job",
)
def get_job(job_id: str):
    job = get_job_state(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.get(
    "/jobs",
    response_model=list[ClipJobResponse],
    summary="List all jobs",
)
def list_jobs():
    return list_all_jobs()

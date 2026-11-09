import uuid
from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status
from app.models.clip import ClipJobResponse, CreateClipJobRequest, JobStatus

router = APIRouter()

# In-memory job registry for development/starter template
JOBS: dict[str, ClipJobResponse] = {}


@router.post(
    "/jobs",
    response_model=ClipJobResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Create a new clip extraction job",
)
def create_job(request: CreateClipJobRequest):
    job_id = str(uuid.uuid4())
    job = ClipJobResponse(
        job_id=job_id,
        status=JobStatus.PENDING,
        message=f"Job queued for target aspect ratio {request.target_aspect_ratio}",
    )
    JOBS[job_id] = job
    return job


@router.post(
    "/upload",
    response_model=ClipJobResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Upload a video file for clipping",
)
async def upload_video(
    file: UploadFile = File(..., description="Video file (MP4, MKV, MOV)"),
    target_aspect_ratio: str = Form(default="9:16"),
    max_duration_seconds: int = Form(default=60),
    generate_subtitles: bool = Form(default=True),
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="Missing file name")

    job_id = str(uuid.uuid4())
    job = ClipJobResponse(
        job_id=job_id,
        status=JobStatus.PENDING,
        message=f"Received video '{file.filename}'. Ready for processing.",
    )
    JOBS[job_id] = job
    return job


@router.get(
    "/jobs/{job_id}",
    response_model=ClipJobResponse,
    summary="Get status and details of a clip job",
)
def get_job(job_id: str):
    if job_id not in JOBS:
        raise HTTPException(status_code=404, detail="Job not found")
    return JOBS[job_id]


@router.get(
    "/jobs",
    response_model=list[ClipJobResponse],
    summary="List all jobs",
)
def list_jobs():
    return list(JOBS.values())

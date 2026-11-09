import shutil
import time
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, File, Form, HTTPException, UploadFile, status
from fastapi.responses import FileResponse

from app.core.config import settings
from app.models.clip import (
    CaptionStylePreset,
    ClipHighlight,
    ClipJobResponse,
    CreateClipJobRequest,
    RerenderClipRequest,
)
from app.services.caption_agent import CaptionAgent
from app.services.coordinator import (
    create_new_job,
    get_job_state,
    list_all_jobs,
    run_pipeline_for_job,
)
from app.services.hook_generator_agent import HookGeneratorAgent
from app.services.video_editing_agent import VideoEditingAgent

router = APIRouter()


@router.get(
    "/caption-styles",
    response_model=list[CaptionStylePreset],
    summary="List all available animated caption styles and their visual properties",
)
def get_caption_styles():
    return CaptionAgent.list_styles()


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
        request.caption_style,
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
    caption_style: str = Form(default="hormozi_glow"),
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
        caption_style,
    )
    return job


@router.post(
    "/jobs/{job_id}/clips/{clip_id}/rerender",
    response_model=ClipHighlight,
    summary="Re-render an existing clip with an updated caption style or hook layout",
)
def rerender_clip(job_id: str, clip_id: str, request: RerenderClipRequest):
    job = get_job_state(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    clip: ClipHighlight | None = None
    for c in job.highlights:
        if c.id == clip_id:
            clip = c
            break

    if not clip:
        raise HTTPException(status_code=404, detail=f"Clip {clip_id} not found in job {job_id}")

    # Determine input video source
    source_path: Path | None = None
    if job.video_filename:
        cand = settings.UPLOAD_DIR / job.video_filename
        if cand.exists():
            source_path = cand

    if not source_path:
        # Check files in upload dir
        files = list(settings.UPLOAD_DIR.glob("*"))
        if files:
            source_path = files[0]

    if not source_path or not source_path.exists():
        raise HTTPException(
            status_code=400,
            detail="Original video file is not available on disk for re-rendering.",
        )

    # 1. Update Hook selection or visual style if requested
    if request.hook_variant_id:
        for h in clip.hooks:
            if h.id == request.hook_variant_id:
                clip.selected_hook = h
                clip.headline = h.headline
                clip.hook_text = h.spoken_hook
                break

    if request.hook_style and clip.selected_hook:
        clip.selected_hook.visual_style = request.hook_style
        hg = HookGeneratorAgent()
        clip.selected_hook.ffmpeg_drawtext = hg._build_ffmpeg_drawtext(
            clip.selected_hook.headline, request.hook_style
        )

    # 2. Re-cut 9:16 video using VideoEditingAgent
    editor = VideoEditingAgent()
    base_cut_path = editor.render_single_clip(source_path, clip, job.metadata)
    clip.rendered_video_path = str(base_cut_path)

    # 3. Re-generate ASS subtitles and burn with selected caption style
    caption_agent = CaptionAgent()
    ass_path, word_count = caption_agent.generate_ass_file(
        clip=clip,
        transcription=job.transcription,
        style_id=request.caption_style,
    )
    clip.subtitles_ass_path = str(ass_path)
    clip.caption_word_count = word_count
    clip.caption_style = request.caption_style

    final_rendered_path = caption_agent.burn_captions_into_video(
        video_path=base_cut_path,
        ass_path=ass_path,
        clip_id=clip.id,
    )
    clip.rendered_video_path = str(final_rendered_path)
    # Append timestamp parameter to bust browser video cache
    clip.rendered_url = f"/api/v1/clips/downloads/{clip.id}?t={int(time.time())}"

    hook_style_name = clip.selected_hook.visual_style if clip.selected_hook else "top_neon_pill"
    clip.editing_effects = [
        "9:16 smart vertical crop",
        "opening pattern interrupt punch-in",
        "loudness normalized audio",
        f"opening hook card ({hook_style_name})",
        f"animated captions ({request.caption_style})",
    ]

    job.logs.append(
        f"Re-rendered clip {clip.id} with caption style '{request.caption_style}' and hook '{hook_style_name}'."
    )
    return clip


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


@router.get(
    "/downloads/{clip_id}",
    summary="Download or stream a rendered vertical 9:16 video clip",
)
def download_clip(clip_id: str):
    clip_path = settings.PROCESSED_DIR / f"{clip_id}.mp4"
    if not clip_path.exists():
        raise HTTPException(status_code=404, detail="Rendered clip not found")
    return FileResponse(
        path=clip_path,
        media_type="video/mp4",
        filename=f"venticut_short_{clip_id}.mp4",
    )

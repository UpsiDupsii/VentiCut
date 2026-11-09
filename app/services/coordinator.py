import asyncio
import logging
import uuid
from pathlib import Path

from app.core.config import settings
from app.models.clip import ClipJobResponse, JobStatus
from app.services.caption_agent import CaptionAgent
from app.services.clip_finder_agent import ViralClipFinderAgent
from app.services.hook_generator_agent import HookGeneratorAgent
from app.services.media_tools import download_youtube_video, extract_audio, extract_video_metadata
from app.services.transcription_agent import TranscriptionAgent
from app.services.understanding_agent import VideoUnderstandingAgent
from app.services.video_editing_agent import VideoEditingAgent
from app.services.webhook import dispatch_webhook

logger = logging.getLogger(__name__)

# Global in-memory registry of active jobs
ACTIVE_JOBS: dict[str, ClipJobResponse] = {}


def get_job_state(job_id: str) -> ClipJobResponse | None:
    return ACTIVE_JOBS.get(job_id)


def list_all_jobs() -> list[ClipJobResponse]:
    return list(ACTIVE_JOBS.values())


def create_new_job(
    video_source: str,
    video_url: str | None = None,
    video_filename: str | None = None,
    webhook_url: str | None = None,
) -> ClipJobResponse:
    job_id = str(uuid.uuid4())
    job = ClipJobResponse(
        job_id=job_id,
        status=JobStatus.PENDING,
        message="Job queued for background processing",
        progress=5,
        video_url=video_url,
        video_filename=video_filename or video_source,
        webhook_url=webhook_url,
        logs=["Job registered into background pipeline."],
    )
    ACTIVE_JOBS[job_id] = job
    return job


async def run_pipeline_for_job(
    job_id: str,
    local_video_path: Path | None = None,
    youtube_url: str | None = None,
    min_duration: int = 15,
    max_duration: int = 60,
    caption_style: str = "hormozi_glow",
):
    """Executes the full pipeline through ingestion, transcription, understanding, viral clip detection, hook generation, video editing, and synchronized captioning."""
    job = ACTIVE_JOBS.get(job_id)
    if not job:
        return

    async def update_job(
        status: JobStatus,
        message: str,
        progress: int,
        log_entry: str | None = None,
        event_name: str | None = None,
        payload: dict | None = None,
    ):
        job.status = status
        job.message = message
        job.progress = progress
        if log_entry:
            job.logs.append(log_entry)
            logger.info(f"[{job_id}] {log_entry}")

        if job.webhook_url and event_name:
            await dispatch_webhook(
                webhook_url=job.webhook_url,
                event=event_name,
                job_id=job.job_id,
                status=status.value,
                progress=progress,
                message=message,
                payload=payload or {},
            )

    try:
        # Step 1: Ingestion
        video_path: Path
        if youtube_url:
            await update_job(
                JobStatus.DOWNLOADING,
                "Downloading YouTube video using yt-dlp...",
                12,
                f"Fetching YouTube video from {youtube_url}",
                event_name="ingestion_started",
            )
            video_path, metadata = await asyncio.to_thread(
                download_youtube_video,
                youtube_url,
                settings.UPLOAD_DIR,
            )
            job.metadata = metadata
            job.video_filename = video_path.name
        elif local_video_path and local_video_path.exists():
            video_path = local_video_path
            await update_job(
                JobStatus.PENDING,
                "Extracting video metadata with ffprobe...",
                15,
                f"Analyzing uploaded video file: {video_path.name}",
                event_name="ingestion_started",
            )
            metadata = await asyncio.to_thread(extract_video_metadata, video_path)
            job.metadata = metadata
            job.video_filename = video_path.name
        else:
            raise ValueError("No valid video source or file found.")

        # Step 2: Audio extraction
        await update_job(
            JobStatus.EXTRACTING_AUDIO,
            "Extracting high-clarity 16kHz mono audio via FFmpeg...",
            25,
            "FFmpeg extracting audio track for Whisper transcription...",
            event_name="audio_extraction_started",
        )
        audio_path = settings.TEMP_DIR / f"{job_id}_audio.mp3"
        await asyncio.to_thread(extract_audio, video_path, audio_path)
        job.logs.append(f"Audio extracted successfully: {audio_path.name}")

        # Step 3: Transcription Agent
        await update_job(
            JobStatus.TRANSCRIBING,
            "Transcription Agent: Generating timestamps and speech transcript via Groq Whisper...",
            42,
            "Calling Groq Whisper API for word-level timestamps...",
            event_name="transcription_started",
        )
        transcriber = TranscriptionAgent()
        transcript = await asyncio.to_thread(transcriber.transcribe, audio_path)
        job.transcription = transcript
        job.logs.append(
            f"Transcription complete: {len(transcript.segments)} segments, language={transcript.language}."
        )

        # Step 4: Video Understanding Agent
        await update_job(
            JobStatus.UNDERSTANDING,
            "Video Understanding Agent: Analyzing content, tone, pacing, and hooks...",
            56,
            "Calling Video Understanding Agent to analyze context and narrative arc...",
            event_name="understanding_started",
        )
        understander = VideoUnderstandingAgent()
        understanding = await asyncio.to_thread(understander.analyze, transcript, job.metadata)
        job.understanding = understanding
        job.logs.append(
            f"Video understanding complete: Tone={understanding.tone}, Topics={len(understanding.topics)}."
        )

        # Step 5: Viral Clip Finder Agent
        await update_job(
            JobStatus.DETECTING_HIGHLIGHTS,
            "Viral Clip Finder Agent: Identifying optimal 15-60s candidate segments...",
            70,
            "Running Viral Clip Finder Agent to score retention and viral moments...",
            event_name="clip_detection_started",
        )
        clip_finder = ViralClipFinderAgent()
        clips = await asyncio.to_thread(
            clip_finder.find_viral_clips,
            transcript=transcript,
            understanding=understanding,
            metadata=job.metadata,
            min_duration=min_duration,
            max_duration=max_duration,
        )
        job.highlights = clips
        job.logs.append(f"Viral clip detection complete: Found {len(clips)} candidate clips.")

        # Step 6: Hook Generator Agent
        await update_job(
            JobStatus.GENERATING_HOOKS,
            "Hook Generator Agent: Creating viral opening title cards and teaser overlays...",
            80,
            "Hook Generator Agent crafting multi-archetype visual hooks and FFmpeg overlays...",
            event_name="hook_generation_started",
        )
        hook_generator = HookGeneratorAgent()
        clips_with_hooks = await asyncio.to_thread(
            hook_generator.generate_hooks_for_clips,
            clips=clips,
            understanding=understanding,
        )
        job.highlights = clips_with_hooks
        total_hooks = sum(len(c.hooks) for c in clips_with_hooks)
        job.logs.append(
            f"Hook generation complete: Generated {total_hooks} hook variations across {len(clips_with_hooks)} clips."
        )

        # Step 7: Video Editing Agent
        await update_job(
            JobStatus.RENDERING,
            "Video Editing Agent: Rendering 9:16 vertical video with punch-in hooks and audio normalization...",
            88,
            "FFmpeg executing smart 9:16 vertical crop, opening punch-in zoom, and title banner...",
            event_name="rendering_started",
        )
        editor = VideoEditingAgent()
        rendered_clips = await asyncio.to_thread(
            editor.render_clips,
            input_video_path=video_path,
            clips=clips_with_hooks,
            metadata=job.metadata,
        )
        job.highlights = rendered_clips
        output_files = [c.rendered_video_path for c in rendered_clips if c.rendered_video_path]
        job.output_files = output_files
        job.logs.append(
            f"Video Editing complete: Rendered {len(output_files)} polished vertical 9:16 cuts."
        )

        # Step 8: Caption Agent
        await update_job(
            JobStatus.CAPTIONING,
            f"Caption Agent: Generating synchronized animated captions ({caption_style})...",
            95,
            f"Caption Agent generating frame-accurate ASS subtitles ({caption_style}) and burning onto clips...",
            event_name="captioning_started",
        )
        caption_agent = CaptionAgent()
        captioned_clips = await asyncio.to_thread(
            caption_agent.caption_clips,
            clips=rendered_clips,
            transcription=job.transcription,
            default_style=caption_style,
        )
        job.highlights = captioned_clips
        final_files = [c.rendered_video_path for c in captioned_clips if c.rendered_video_path]
        job.output_files = final_files
        job.logs.append(
            f"Caption Agent complete: Burned animated subtitles across {len(final_files)} clips using '{caption_style}' preset."
        )

        # Step 9: Mark pipeline stage as completed
        await update_job(
            JobStatus.COMPLETED,
            f"Pipeline complete! {len(final_files)} viral vertical shorts rendered with visual hooks and animated captions.",
            100,
            "Pipeline processing finished successfully.",
            event_name="job_completed",
            payload={"clip_count": len(captioned_clips), "rendered_count": len(final_files)},
        )

    except Exception as e:
        logger.exception(f"Pipeline error for job {job_id}: {e}")
        job.status = JobStatus.FAILED
        job.message = f"Pipeline error: {str(e)}"
        job.error = str(e)
        job.logs.append(f"ERROR: {str(e)}")
        if job.webhook_url:
            await dispatch_webhook(
                webhook_url=job.webhook_url,
                event="job_failed",
                job_id=job.job_id,
                status=JobStatus.FAILED.value,
                progress=job.progress,
                message=str(e),
                payload={"error": str(e)},
            )

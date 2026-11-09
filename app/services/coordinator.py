import asyncio
import logging
import uuid
from pathlib import Path

from app.core.config import settings
from app.models.clip import ClipJobResponse, JobStatus
from app.services.media_tools import download_youtube_video, extract_audio, extract_video_metadata
from app.services.transcription_agent import TranscriptionAgent
from app.services.understanding_agent import VideoUnderstandingAgent

logger = logging.getLogger(__name__)

# Global registry of active jobs
ACTIVE_JOBS: dict[str, ClipJobResponse] = {}


def get_job_state(job_id: str) -> ClipJobResponse | None:
    return ACTIVE_JOBS.get(job_id)


def list_all_jobs() -> list[ClipJobResponse]:
    return list(ACTIVE_JOBS.values())


def create_new_job(
    video_source: str,
    video_url: str | None = None,
    video_filename: str | None = None,
) -> ClipJobResponse:
    job_id = str(uuid.uuid4())
    job = ClipJobResponse(
        job_id=job_id,
        status=JobStatus.PENDING,
        message="Job queued for processing",
        progress=5,
        video_url=video_url,
        video_filename=video_filename or video_source,
        logs=["Job registered into pipeline."],
    )
    ACTIVE_JOBS[job_id] = job
    return job


async def run_pipeline_for_job(
    job_id: str, local_video_path: Path | None = None, youtube_url: str | None = None
):
    """Executes the pipeline through ingestion, transcription, and understanding."""
    job = ACTIVE_JOBS.get(job_id)
    if not job:
        return

    def update_job(status: JobStatus, message: str, progress: int, log_entry: str | None = None):
        job.status = status
        job.message = message
        job.progress = progress
        if log_entry:
            job.logs.append(log_entry)
            logger.info(f"[{job_id}] {log_entry}")

    try:
        # Step 1: Ingestion
        video_path: Path
        if youtube_url:
            update_job(
                JobStatus.DOWNLOADING,
                "Downloading YouTube video using yt-dlp...",
                15,
                f"Fetching YouTube video from {youtube_url}",
            )
            # Run yt-dlp in a thread pool so it does not block async event loop
            video_path, metadata = await asyncio.to_thread(
                download_youtube_video,
                youtube_url,
                settings.UPLOAD_DIR,
            )
            job.metadata = metadata
            job.video_filename = video_path.name
        elif local_video_path and local_video_path.exists():
            video_path = local_video_path
            update_job(
                JobStatus.PENDING,
                "Extracting video metadata with ffprobe...",
                20,
                f"Analyzing uploaded video file: {video_path.name}",
            )
            metadata = await asyncio.to_thread(extract_video_metadata, video_path)
            job.metadata = metadata
            job.video_filename = video_path.name
        else:
            raise ValueError("No valid video source or file found.")

        # Step 2: Audio extraction
        update_job(
            JobStatus.EXTRACTING_AUDIO,
            "Extracting high-clarity 16kHz mono audio via FFmpeg...",
            35,
            "FFmpeg extracting audio track for Whisper transcription...",
        )
        audio_path = settings.TEMP_DIR / f"{job_id}_audio.mp3"
        await asyncio.to_thread(extract_audio, video_path, audio_path)
        job.logs.append(f"Audio extracted successfully: {audio_path.name}")

        # Step 3: Transcription Agent
        update_job(
            JobStatus.TRANSCRIBING,
            "Transcription Agent: Generating timestamps and speech transcript via Groq Whisper...",
            60,
            "Calling Groq Whisper API for word-level timestamps...",
        )
        transcriber = TranscriptionAgent()
        transcript = await asyncio.to_thread(transcriber.transcribe, audio_path)
        job.transcription = transcript
        job.logs.append(
            f"Transcription complete: {len(transcript.segments)} segments, language={transcript.language}."
        )

        # Step 4: Video Understanding Agent
        update_job(
            JobStatus.UNDERSTANDING,
            "Video Understanding Agent: Analyzing content, tone, pacing, and hooks via Gemini...",
            85,
            "Calling Google Gemini API to analyze context and narrative arc...",
        )
        understander = VideoUnderstandingAgent()
        understanding = await asyncio.to_thread(understander.analyze, transcript, job.metadata)
        job.understanding = understanding
        job.logs.append(
            f"Video understanding complete: Tone={understanding.tone}, Topics={len(understanding.topics)}."
        )

        # Step 5: Complete initial agent stage
        update_job(
            JobStatus.COMPLETED,
            "Ingestion, Transcription, and Video Understanding complete!",
            100,
            "Pipeline stage 1 finished successfully.",
        )

    except Exception as e:
        logger.exception(f"Pipeline error for job {job_id}: {e}")
        job.status = JobStatus.FAILED
        job.message = f"Pipeline error: {str(e)}"
        job.error = str(e)
        job.logs.append(f"ERROR: {str(e)}")

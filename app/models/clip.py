from enum import StrEnum

from pydantic import BaseModel, Field


class JobStatus(StrEnum):
    PENDING = "pending"
    EXTRACTING_AUDIO = "extracting_audio"
    TRANSCRIBING = "transcribing"
    DETECTING_HIGHLIGHTS = "detecting_highlights"
    CROPPING = "cropping"
    RENDERING = "rendering"
    COMPLETED = "completed"
    FAILED = "failed"


class ClipHighlight(BaseModel):
    id: str
    start_time: float = Field(..., description="Start time in seconds")
    end_time: float = Field(..., description="End time in seconds")
    duration: float = Field(..., description="Duration in seconds")
    headline: str = Field(..., description="Suggested viral title/hook")
    virality_score: float = Field(
        ..., ge=0.0, le=100.0, description="Estimated virality score 0-100"
    )
    summary: str | None = None


class CreateClipJobRequest(BaseModel):
    video_url: str | None = Field(default=None, description="Direct URL or YouTube link to video")
    target_aspect_ratio: str = Field(
        default="9:16", description="Target aspect ratio for the short"
    )
    max_duration_seconds: int = Field(default=60, description="Maximum length per short in seconds")
    generate_subtitles: bool = Field(
        default=True, description="Whether to burn animated subtitles into clip"
    )


class ClipJobResponse(BaseModel):
    job_id: str
    status: JobStatus
    message: str
    highlights: list[ClipHighlight] = []
    output_files: list[str] = []

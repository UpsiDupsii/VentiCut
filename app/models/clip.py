from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class JobStatus(StrEnum):
    PENDING = "pending"
    DOWNLOADING = "downloading"
    EXTRACTING_AUDIO = "extracting_audio"
    TRANSCRIBING = "transcribing"
    UNDERSTANDING = "understanding"
    DETECTING_HIGHLIGHTS = "detecting_highlights"
    CROPPING = "cropping"
    RENDERING = "rendering"
    COMPLETED = "completed"
    FAILED = "failed"


class VideoMetadata(BaseModel):
    title: str = "Uploaded Video"
    duration: float = 0.0
    width: int = 1920
    height: int = 1080
    fps: float = 30.0
    aspect_ratio: str = "16:9"
    format: str = "mp4"
    file_size_mb: float = 0.0


class WordTimestamp(BaseModel):
    word: str
    start: float
    end: float


class TranscriptionSegment(BaseModel):
    id: int
    start: float
    end: float
    text: str
    words: list[WordTimestamp] = []


class TranscriptionResult(BaseModel):
    language: str = "en"
    duration: float = 0.0
    full_text: str = ""
    segments: list[TranscriptionSegment] = []


class VideoUnderstandingResult(BaseModel):
    summary: str = ""
    topics: list[str] = []
    tone: str = "informative"
    pacing: str = "moderate"
    target_audience: str = "General audience"
    potential_hooks: list[str] = []
    speaker_insights: list[str] = []


class ClipHighlight(BaseModel):
    id: str
    start_time: float = Field(..., description="Start time in seconds")
    end_time: float = Field(..., description="End time in seconds")
    duration: float = Field(..., description="Duration in seconds")
    headline: str = Field(..., description="Suggested viral title")
    hook_text: str = Field(default="", description="First 3-5 seconds opening hook words")
    virality_score: float = Field(..., ge=0.0, le=100.0, description="Overall virality score 0-100")
    hook_score: float = Field(
        default=85.0, ge=0.0, le=100.0, description="Opening hook strength 0-100"
    )
    retention_score: float = Field(
        default=80.0, ge=0.0, le=100.0, description="Predicted viewer retention 0-100"
    )
    reasoning: str = Field(default="", description="Why this clip is predicted to perform well")
    summary: str | None = None


class CreateClipJobRequest(BaseModel):
    video_url: str | None = Field(default=None, description="Direct URL or YouTube link to video")
    target_aspect_ratio: str = Field(
        default="9:16", description="Target aspect ratio for the short"
    )
    max_duration_seconds: int = Field(default=60, description="Maximum length per short in seconds")
    min_duration_seconds: int = Field(default=15, description="Minimum length per short in seconds")
    generate_subtitles: bool = Field(
        default=True, description="Whether to burn animated subtitles into clip"
    )
    webhook_url: str | None = Field(
        default=None, description="Optional webhook URL for progress callbacks"
    )


class ClipJobResponse(BaseModel):
    job_id: str
    status: JobStatus
    message: str
    progress: int = 0
    video_filename: str | None = None
    video_url: str | None = None
    webhook_url: str | None = None
    metadata: VideoMetadata | None = None
    transcription: TranscriptionResult | None = None
    understanding: VideoUnderstandingResult | None = None
    highlights: list[ClipHighlight] = []
    output_files: list[str] = []
    error: str | None = None
    logs: list[str] = []
    extra: dict[str, Any] = {}

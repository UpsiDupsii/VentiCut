from enum import StrEnum

from pydantic import BaseModel, Field


class JobStatus(StrEnum):
    PENDING = "pending"
    DOWNLOADING = "downloading"
    EXTRACTING_AUDIO = "extracting_audio"
    TRANSCRIBING = "transcribing"
    UNDERSTANDING = "understanding"
    DETECTING_HIGHLIGHTS = "detecting_highlights"
    GENERATING_HOOKS = "generating_hooks"
    CROPPING = "cropping"
    RENDERING = "rendering"
    CAPTIONING = "captioning"
    QUALITY_REVIEW = "quality_review"
    PACKAGING = "packaging"
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


class HookVariant(BaseModel):
    id: str
    headline: str = Field(..., description="Short, punchy visual headline (3-6 words)")
    spoken_hook: str = Field(..., description="Opening spoken teaser text")
    hook_type: str = Field(
        default="Curiosity Gap",
        description="Archetype: Curiosity Gap, Contrarian, Problem-Agitation, Direct Value",
    )
    hook_score: float = Field(
        default=90.0, ge=0.0, le=100.0, description="Predicted 3-second retention score 0-100"
    )
    visual_style: str = Field(
        default="top_neon_pill",
        description="Visual style: top_neon_pill, center_punch_title, lower_third_bar, floating_frosted_card",
    )
    ffmpeg_drawtext: str = Field(
        default="",
        description="FFmpeg drawtext filter syntax ready for burning into video",
    )


class CaptionStylePreset(BaseModel):
    id: str
    name: str
    description: str
    font_name: str
    primary_color: str
    highlight_color: str
    badge_style: str


class QualityCheckItem(BaseModel):
    name: str = Field(
        ..., description="Name of the quality check (e.g. Audio Normalization, Subtitle Sync)"
    )
    status: str = Field(default="pass", description="Result status: pass, warn, fail")
    score: float = Field(default=100.0, ge=0.0, le=100.0, description="Score for this check 0-100")
    details: str = Field(default="", description="Explanatory notes or diagnostic message")


class QualityReviewResult(BaseModel):
    overall_score: float = Field(
        default=90.0, ge=0.0, le=100.0, description="Overall Publish Readiness Score (0-100)"
    )
    status: str = Field(
        default="passed", description="Status: passed (>=80), warning (65-79), failed (<65)"
    )
    checks: list[QualityCheckItem] = Field(
        default=[], description="Individual automated audit checks"
    )
    suggestions: list[str] = Field(
        default=[], description="Actionable recommendations to maximize viewer engagement"
    )
    safety_flags: list[str] = Field(
        default=[], description="Identified brand safety or moderation flags"
    )


class PlatformPostCopy(BaseModel):
    title: str = Field(default="", description="Optimized headline or video title for platform")
    caption: str = Field(default="", description="Complete social post copy / caption")
    hashtags: list[str] = Field(
        default=[], description="High-performing, algorithm-aligned hashtags"
    )
    pinned_comment: str = Field(
        default="", description="High-converting first comment to drive engagement"
    )
    call_to_action: str = Field(default="", description="Platform-specific call to action")


class SocialDistributionMetadata(BaseModel):
    youtube_shorts: PlatformPostCopy = Field(default_factory=PlatformPostCopy)
    tiktok: PlatformPostCopy = Field(default_factory=PlatformPostCopy)
    instagram_reels: PlatformPostCopy = Field(default_factory=PlatformPostCopy)


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
    hooks: list[HookVariant] = Field(
        default=[], description="Creative hook variants generated by Hook Generator Agent"
    )
    selected_hook: HookVariant | None = Field(
        default=None, description="Currently selected hook variant for rendering"
    )
    rendered_video_path: str | None = Field(
        default=None, description="Local file path to rendered vertical short video"
    )
    rendered_url: str | None = Field(
        default=None, description="Streaming and download API endpoint for rendered clip"
    )
    caption_style: str = Field(
        default="hormozi_glow",
        description="Active animated caption style applied to this clip",
    )
    available_caption_styles: list[str] = Field(
        default=[
            "hormozi_glow",
            "mrbeast_yellow",
            "karaoke_fill",
            "tiktok_badge",
            "minimal_clean",
        ],
        description="List of all selectable caption styles for re-rendering",
    )
    subtitles_ass_path: str | None = Field(
        default=None, description="Path to generated ASS subtitle file"
    )
    caption_word_count: int = Field(
        default=0, description="Total spoken word count synchronized in clip captions"
    )
    editing_effects: list[str] = Field(
        default=[], description="List of visual and audio effects applied by Video Editing Agent"
    )
    layout_mode: str = Field(
        default="smart_crop_center",
        description="Layout mode: smart_crop_center, blurred_background_stack, original",
    )
    thumbnail_path: str | None = Field(
        default=None, description="Local file path to extracted 9:16 vertical cover frame"
    )
    thumbnail_url: str | None = Field(
        default=None, description="Direct URL endpoint to view and download vertical cover frame"
    )
    thumbnail_timestamp: float = Field(
        default=0.0, description="Exact timestamp (seconds) where cover frame was captured"
    )
    quality_review: QualityReviewResult | None = Field(
        default=None, description="Audit report generated by Quality Review Agent"
    )
    readiness_score: float = Field(
        default=0.0, ge=0.0, le=100.0, description="Overall publish readiness score 0-100"
    )
    social_metadata: SocialDistributionMetadata | None = Field(
        default=None, description="Platform-tailored packaging generated by Social Metadata Agent"
    )


class CreateClipJobRequest(BaseModel):
    video_url: str | None = Field(default=None, description="Direct URL or YouTube link to video")
    target_aspect_ratio: str = Field(
        default="9:16", description="Target aspect ratio for the short"
    )
    max_duration_seconds: int = Field(default=60, description="Maximum length per short in seconds")
    min_duration_seconds: int = Field(default=15, description="Minimum length per short in seconds")
    caption_style: str = Field(
        default="hormozi_glow",
        description="Selected caption style: hormozi_glow, mrbeast_yellow, karaoke_fill, tiktok_badge, minimal_clean",
    )
    generate_subtitles: bool = Field(
        default=True, description="Whether to burn animated subtitles into clip"
    )
    webhook_url: str | None = Field(
        default=None, description="Optional webhook URL for progress callbacks"
    )


class RerenderClipRequest(BaseModel):
    caption_style: str = Field(
        default="hormozi_glow",
        description="Target caption style: hormozi_glow, mrbeast_yellow, karaoke_fill, tiktok_badge, minimal_clean",
    )
    hook_variant_id: str | None = Field(
        default=None,
        description="Optional ID of hook variant to select for this clip",
    )
    hook_style: str | None = Field(
        default=None,
        description="Optional visual hook layout override: top_neon_pill, center_punch_title, lower_third_bar, floating_frosted_card",
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

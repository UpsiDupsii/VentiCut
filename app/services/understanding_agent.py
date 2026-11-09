import json
import logging

from google import genai
from google.genai import types

from app.core.config import settings
from app.models.clip import TranscriptionResult, VideoMetadata, VideoUnderstandingResult
from app.services.token_tracker import token_tracker

logger = logging.getLogger(__name__)


class VideoUnderstandingAgent:
    """Agent that analyzes video transcripts and metadata to understand context, tone, and themes."""

    def __init__(self, api_key: str | None = None, model: str | None = None):
        self.api_key = api_key or settings.GEMINI_API_KEY
        self.model = model or settings.GEMINI_MODEL
        self.client = genai.Client(api_key=self.api_key) if self.api_key else None

    def analyze(
        self,
        transcript: TranscriptionResult,
        metadata: VideoMetadata | None = None,
    ) -> VideoUnderstandingResult:
        """Analyze video context and transcript using Google Gemini API."""
        if not self.client:
            logger.warning("No GEMINI_API_KEY provided. Using simulated video understanding.")
            return self._simulated_understanding(transcript, metadata)

        prompt = f"""
You are the Video Understanding Agent for VentiCut, an AI video repurposing pipeline.
Analyze the following video information and full transcript:

Video Title: {metadata.title if metadata else "Uploaded Video"}
Video Duration: {metadata.duration if metadata else transcript.duration} seconds
Full Transcript:
{transcript.full_text[:8000]}

Respond ONLY with a valid JSON object matching this schema:
{{
  "summary": "Concise 2-3 sentence overview of the video content and purpose",
  "topics": ["topic 1", "topic 2", "topic 3"],
  "tone": "e.g. Enthusiastic, Educational, Serious, Conversational",
  "pacing": "Fast, Moderate, or Relaxed",
  "target_audience": "Specific audience description",
  "potential_hooks": [
    "Catchy opening question or statement 1",
    "Catchy opening question or statement 2"
  ],
  "speaker_insights": [
    "Insight on speaking style or key takeaway 1",
    "Insight on speaking style or key takeaway 2"
  ]
}}
"""

        candidate_models = [
            self.model,
            "gemini-3.8-flash",
            "gemini-3.5-flash",
            "gemini-2.5-flash-lite",
        ]
        candidate_models = list(dict.fromkeys(m for m in candidate_models if m))

        last_error = None
        for candidate in candidate_models:
            try:
                config = types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.2,
                )
                response = self.client.models.generate_content(
                    model=candidate,
                    contents=prompt,
                    config=config,
                )

                # Record usage in token tracker
                est_tokens = len(prompt) // 4 + len(response.text or "") // 4
                token_tracker.record_gemini_call(estimated_tokens=est_tokens)

                text_output = response.text or "{}"
                parsed = json.loads(text_output)

                return VideoUnderstandingResult(
                    summary=parsed.get("summary", ""),
                    topics=parsed.get("topics", []),
                    tone=parsed.get("tone", "conversational"),
                    pacing=parsed.get("pacing", "moderate"),
                    target_audience=parsed.get("target_audience", "General audience"),
                    potential_hooks=parsed.get("potential_hooks", []),
                    speaker_insights=parsed.get("speaker_insights", []),
                )

            except Exception as e:
                last_error = e
                logger.warning(f"Gemini model '{candidate}' failed: {e}. Trying next candidate...")

        logger.error(f"All Gemini models failed ({last_error}). Falling back to simulation.")
        return self._simulated_understanding(transcript, metadata, str(last_error))

    def _simulated_understanding(
        self,
        transcript: TranscriptionResult,
        metadata: VideoMetadata | None = None,
        error_note: str | None = None,
    ) -> VideoUnderstandingResult:
        """Fallback understanding when API is unavailable."""
        token_tracker.record_gemini_call(estimated_tokens=320)
        title = metadata.title if metadata else "Video Content"
        summary = f"Analysis of '{title}': A presentation covering video creation, technology, and media repurposing."
        if error_note:
            logger.info(f"Fallback understanding active due to: {error_note}")

        return VideoUnderstandingResult(
            summary=summary,
            topics=[
                "Video Repurposing",
                "Artificial Intelligence",
                "Content Strategy",
                "Shorts Creation",
            ],
            tone="Informative and Engaging",
            pacing="Dynamic and Engaging",
            target_audience="Content creators, podcasters, marketers, and video editors",
            potential_hooks=[
                "Did you know AI can turn your 1-hour podcast into 10 viral shorts?",
                "The secret to viral retention starts in the first 3 seconds.",
            ],
            speaker_insights=[
                "Clear vocal cadence suitable for subtitle generation.",
                "High engagement potential during introductory remarks.",
            ],
        )

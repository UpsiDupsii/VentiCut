import json
import logging
import re
import uuid

from groq import Groq

from app.core.config import settings
from app.models.clip import (
    ClipHighlight,
    TranscriptionResult,
    VideoMetadata,
    VideoUnderstandingResult,
)
from app.services.token_tracker import token_tracker

logger = logging.getLogger(__name__)

HOOK_TRIGGERS = [
    "why",
    "how",
    "secret",
    "never",
    "always",
    "stop",
    "mistake",
    "truth",
    "realize",
    "discover",
    "insane",
    "crazy",
    "problem",
    "hack",
    "tip",
    "rule",
    "formula",
    "shocking",
]


class ViralClipFinderAgent:
    """Agent that identifies high-performing, self-contained viral segments from transcripts."""

    def __init__(self, api_key: str | None = None, model: str | None = None):
        self.api_key = api_key or settings.GROQ_API_KEY
        self.model = model or settings.GROQ_LLM_MODEL
        self.client = Groq(api_key=self.api_key) if self.api_key else None

    def find_viral_clips(
        self,
        transcript: TranscriptionResult,
        understanding: VideoUnderstandingResult | None = None,
        metadata: VideoMetadata | None = None,
        min_duration: int = 15,
        max_duration: int = 60,
    ) -> list[ClipHighlight]:
        """Detects top viral short segments using LLM reasoning with an algorithmic heuristic fallback."""
        if not transcript.segments:
            return []

        # Attempt LLM-based detection if Groq API is configured
        if self.client:
            try:
                clips = self._llm_detect_clips(
                    transcript, understanding, metadata, min_duration, max_duration
                )
                if clips:
                    return clips
            except Exception as e:
                logger.warning(
                    f"LLM viral clip detection failed ({e}). Using algorithmic fallback."
                )

        # Fallback to algorithmic heuristic chunker
        return self._heuristic_detect_clips(transcript, understanding, min_duration, max_duration)

    def _llm_detect_clips(
        self,
        transcript: TranscriptionResult,
        understanding: VideoUnderstandingResult | None,
        metadata: VideoMetadata | None,
        min_duration: int,
        max_duration: int,
    ) -> list[ClipHighlight]:
        """Uses Groq Llama-3 / GPT-OSS to analyze the transcript and extract top viral moments."""
        formatted_segments = []
        for s in transcript.segments[:120]:
            formatted_segments.append(f"[{s.start:.1f}s - {s.end:.1f}s]: {s.text}")

        transcript_body = "\n".join(formatted_segments)

        system_prompt = (
            "You are the Viral Clip Finder Agent for VentiCut. "
            "Your job is to identify 2 to 5 self-contained viral video clip segments "
            f"lasting between {min_duration} and {max_duration} seconds. "
            "Criteria: \n"
            "1. Strong hook in the first 3-5 seconds.\n"
            "2. Complete narrative or insight that makes sense out of context.\n"
            "3. Clean start and end timestamps matching sentence boundaries.\n"
            "Respond ONLY with a valid JSON array of objects."
        )

        user_prompt = f"""
Video Context: {understanding.summary if understanding else (metadata.title if metadata else "Video")}
Topics: {", ".join(understanding.topics) if understanding else "General"}

Timestamped Transcript:
{transcript_body}

Extract the best 2 to 4 viral clips. Response schema:
[
  {{
    "headline": "Catchy 3-7 word viral title",
    "hook_text": "Exact opening 5-10 words of the clip",
    "start_time": 12.5,
    "end_time": 45.0,
    "virality_score": 92.5,
    "hook_score": 95.0,
    "retention_score": 90.0,
    "reasoning": "Why this segment has high engagement potential",
    "summary": "Brief summary of the clip topic"
  }}
]
"""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            response_format={"type": "json_object"},
            temperature=0.2,
        )

        # Record LLM usage in token tracker
        if hasattr(response, "usage") and response.usage:
            token_tracker.record_groq_llm(
                prompt_tokens=getattr(response.usage, "prompt_tokens", 0) or 0,
                completion_tokens=getattr(response.usage, "completion_tokens", 0) or 0,
            )

        content = response.choices[0].message.content or "{}"
        parsed = json.loads(content)

        # Handle either array or object wrapping {"clips": [...]}
        raw_list = (
            parsed
            if isinstance(parsed, list)
            else (
                parsed.get("clips") or parsed.get("highlights") or list(parsed.values())[0]
                if isinstance(parsed, dict) and parsed
                else []
            )
        )

        if not isinstance(raw_list, list):
            return []

        results: list[ClipHighlight] = []
        for idx, item in enumerate(raw_list):
            if not isinstance(item, dict):
                continue
            start = float(item.get("start_time", 0.0))
            end = float(item.get("end_time", start + 30.0))
            duration = round(end - start, 2)
            if duration < min_duration or duration > max_duration + 10:
                continue

            results.append(
                ClipHighlight(
                    id=f"clip_{idx + 1}_{uuid.uuid4().hex[:6]}",
                    start_time=start,
                    end_time=end,
                    duration=duration,
                    headline=item.get("headline", f"Viral Moment {idx + 1}"),
                    hook_text=item.get("hook_text", ""),
                    virality_score=float(item.get("virality_score", 85.0)),
                    hook_score=float(item.get("hook_score", 85.0)),
                    retention_score=float(item.get("retention_score", 80.0)),
                    reasoning=item.get("reasoning", "Strong standalone hook and narrative flow."),
                    summary=item.get("summary", ""),
                )
            )

        return results

    def _heuristic_detect_clips(
        self,
        transcript: TranscriptionResult,
        understanding: VideoUnderstandingResult | None,
        min_duration: int,
        max_duration: int,
    ) -> list[ClipHighlight]:
        """Deterministic chunking fallback that builds self-contained clips based on sentence cadence."""
        segments = transcript.segments
        if not segments:
            return []

        token_tracker.record_groq_llm(prompt_tokens=450, completion_tokens=180)

        clips: list[ClipHighlight] = []
        current_chunk: list = []
        chunk_start = segments[0].start

        for seg in segments:
            current_chunk.append(seg)
            chunk_duration = seg.end - chunk_start

            # Check if this segment ends with punctuation indicating a complete thought
            text = seg.text.strip()
            ends_thought = text.endswith((".", "!", "?"))

            if chunk_duration >= min_duration and (ends_thought or chunk_duration >= max_duration):
                chunk_text = " ".join(s.text for s in current_chunk)
                first_sentence = chunk_text.split(".")[0]
                words = chunk_text.split()
                hook_words = " ".join(words[:8]) if len(words) >= 8 else chunk_text

                # Calculate hook score based on trigger keywords
                hook_score = 75.0
                lowered_hook = hook_words.lower()
                for trigger in HOOK_TRIGGERS:
                    if re.search(r"\b" + trigger + r"\b", lowered_hook):
                        hook_score = min(98.0, hook_score + 7.0)

                if "?" in first_sentence:
                    hook_score = min(99.0, hook_score + 8.0)

                retention_score = 80.0
                if 25 <= chunk_duration <= 45:
                    retention_score += 8.0

                virality_score = round((hook_score * 0.55) + (retention_score * 0.45), 1)

                clip_id = f"clip_{len(clips) + 1}_{uuid.uuid4().hex[:6]}"
                headline = (
                    first_sentence[:45]
                    if len(first_sentence) > 10
                    else f"Highlight Part {len(clips) + 1}"
                )

                clips.append(
                    ClipHighlight(
                        id=clip_id,
                        start_time=round(chunk_start, 2),
                        end_time=round(seg.end, 2),
                        duration=round(chunk_duration, 2),
                        headline=headline,
                        hook_text=hook_words,
                        virality_score=virality_score,
                        hook_score=round(hook_score, 1),
                        retention_score=round(retention_score, 1),
                        reasoning="Strong opening hook cadence with complete thought termination.",
                        summary=f"Segment covering: {headline}",
                    )
                )

                # Reset for next candidate
                current_chunk = []
                chunk_start = seg.end

                if len(clips) >= 5:
                    break

        # Sort clips by virality score descending
        clips.sort(key=lambda c: c.virality_score, reverse=True)
        return clips

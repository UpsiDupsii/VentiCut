import json
import logging
import re
import uuid

from groq import Groq

from app.core.config import settings
from app.models.clip import ClipHighlight, HookVariant, VideoUnderstandingResult
from app.services.token_tracker import token_tracker

logger = logging.getLogger(__name__)

HOOK_ARCHETYPES = [
    {
        "type": "Curiosity Gap",
        "style": "top_banner_yellow",
        "prefix": "WHY NOBODY TALKS ABOUT",
    },
    {
        "type": "Contrarian",
        "style": "center_glow_white",
        "prefix": "STOP DOING THIS WITH",
    },
    {
        "type": "Problem-Agitation",
        "style": "lower_third_punchy",
        "prefix": "THE NUMBER ONE MISTAKE IN",
    },
    {
        "type": "Direct Value",
        "style": "top_banner_yellow",
        "prefix": "THE UNTOLD SECRET OF",
    },
]


class HookGeneratorAgent:
    """Agent that generates attention-grabbing visual hooks and opening teaser overlays

    for viral short-form videos (TikTok, Instagram Reels, YouTube Shorts).
    """

    def __init__(self, api_key: str | None = None, model: str | None = None):
        self.api_key = api_key or settings.GROQ_API_KEY
        self.model = model or settings.GROQ_LLM_MODEL
        self.client = Groq(api_key=self.api_key) if self.api_key else None

    def generate_hooks_for_clips(
        self,
        clips: list[ClipHighlight],
        understanding: VideoUnderstandingResult | None = None,
    ) -> list[ClipHighlight]:
        """Generates multiple creative hook variations and FFmpeg visual overlay commands for each clip."""
        if not clips:
            return []

        for clip in clips:
            variants: list[HookVariant] = []
            if self.client:
                try:
                    variants = self._generate_with_llm(clip, understanding)
                except Exception as e:
                    logger.warning(
                        f"LLM hook generation failed for clip {clip.id}: {e}. Using rule-based fallback."
                    )
                    variants = self._generate_fallback(clip, understanding)
            else:
                variants = self._generate_fallback(clip, understanding)

            clip.hooks = variants
            if variants:
                # Select the highest scoring hook variant by default
                best_variant = max(variants, key=lambda v: v.hook_score)
                clip.selected_hook = best_variant
                clip.hook_score = best_variant.hook_score
                # Update top-level hook text and headline if refined
                clip.hook_text = best_variant.spoken_hook
                clip.headline = best_variant.headline

        return clips

    def _generate_with_llm(
        self,
        clip: ClipHighlight,
        understanding: VideoUnderstandingResult | None,
    ) -> list[HookVariant]:
        """Calls Groq LLM to craft 4 distinct viral hook variants based on viewer psychology."""
        topics = ", ".join(understanding.topics) if understanding else "General"
        tone = understanding.tone if understanding else "Engaging"

        prompt = f"""You are the VentiCut Hook Generator Agent, an expert short-form video copywriter specializing in TikTok, Instagram Reels, and YouTube Shorts.

Analyze the opening 3-5 seconds of this video clip and craft 4 viral hook variations designed to stop viewers from swiping in the critical opening 3 seconds.

Clip Context:
- Segment Duration: {clip.duration:.1f} seconds
- Identified Topics: {topics}
- Tone: {tone}
- Spoken Hook Words: "{clip.hook_text}"
- Current Headline: "{clip.headline}"

Requirements:
Create exactly 4 hook variations across these 4 distinct viral archetypes:
1. "Curiosity Gap": Poses an irresistible mystery, unspoken pattern, or cliffhanger.
2. "Contrarian": Challenges conventional wisdom or claims mainstream advice is wrong.
3. "Problem-Agitation": Highlights a frustrating mistake and promises immediate relief.
4. "Direct Value": Promises a high-value, actionable shortcut or framework.

For each variation, supply:
- headline: 3 to 6 words, all-caps, ultra-punchy for an on-screen title card.
- spoken_hook: A refined, high-impact spoken opening sentence.
- hook_type: The archetype name.
- hook_score: Estimated 3-second retention score between 80.0 and 99.0.
- visual_style: One of ["top_banner_yellow", "center_glow_white", "lower_third_punchy"].

Respond ONLY with valid JSON in this exact structure:
{{
  "hooks": [
    {{
      "headline": "THE FATAL REACH MISTAKE",
      "spoken_hook": "If you are not doing this in the first 3 seconds, your video is already dead.",
      "hook_type": "Curiosity Gap",
      "hook_score": 96.5,
      "visual_style": "top_banner_yellow"
    }}
  ]
}}"""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": "You are a specialized viral hook copywriter for vertical video. Always output raw JSON only.",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.7,
            max_tokens=800,
        )

        if response.usage:
            token_tracker.record_groq_tokens(response.usage.total_tokens)

        content = response.choices[0].message.content or "{}"
        match = re.search(r"\{.*\}", content, re.DOTALL)
        if match:
            data = json.loads(match.group(0))
        else:
            data = json.loads(content)

        raw_hooks = data.get("hooks", [])
        variants = []
        for h in raw_hooks:
            headline = str(h.get("headline", clip.headline)).upper().strip()
            spoken = str(h.get("spoken_hook", clip.hook_text)).strip()
            hook_type = str(h.get("hook_type", "Curiosity Gap"))
            score = float(h.get("hook_score", 90.0))
            style = str(h.get("visual_style", "top_banner_yellow"))

            drawtext = self._build_ffmpeg_drawtext(headline, style)

            variants.append(
                HookVariant(
                    id=str(uuid.uuid4())[:8],
                    headline=headline,
                    spoken_hook=spoken,
                    hook_type=hook_type,
                    hook_score=score,
                    visual_style=style,
                    ffmpeg_drawtext=drawtext,
                )
            )

        if not variants:
            raise ValueError("No valid hook variations parsed from LLM.")

        return variants

    def _generate_fallback(
        self,
        clip: ClipHighlight,
        understanding: VideoUnderstandingResult | None,
    ) -> list[HookVariant]:
        """Deterministic rule-based hook generation when LLM is unavailable."""
        base_headline = clip.headline.strip() if clip.headline else "VIRAL MOMENT"
        spoken = (
            clip.hook_text.strip() if clip.hook_text else "Listen closely to what happens next."
        )

        # Extract primary keyword from headline
        words = [w for w in re.findall(r"\b\w+\b", base_headline) if len(w) > 3]
        primary_topic = words[0].upper() if words else "CREATOR SECRETS"

        variants = []
        scores = [95.0, 92.5, 89.0, 94.0]

        templates = [
            (
                "Curiosity Gap",
                "top_banner_yellow",
                f"THE BRUTAL TRUTH ABOUT {primary_topic}",
                f"Almost nobody realizes what actually happens with {primary_topic.lower()}.",
            ),
            (
                "Contrarian",
                "center_glow_white",
                f"STOP DOING THIS WITH {primary_topic}",
                f"Everything you've been taught about {primary_topic.lower()} is backwards.",
            ),
            (
                "Problem-Agitation",
                "lower_third_punchy",
                f"THE BIGGEST {primary_topic} MISTAKE",
                f"If you keep ignoring this {primary_topic.lower()} mistake, you will get stuck.",
            ),
            (
                "Direct Value",
                "top_banner_yellow",
                f"THE UNTOLD {primary_topic} SECRET",
                spoken,
            ),
        ]

        for i, (hook_type, style, headline, spoken_teaser) in enumerate(templates):
            drawtext = self._build_ffmpeg_drawtext(headline, style)
            variants.append(
                HookVariant(
                    id=str(uuid.uuid4())[:8],
                    headline=headline,
                    spoken_hook=spoken_teaser,
                    hook_type=hook_type,
                    hook_score=scores[i],
                    visual_style=style,
                    ffmpeg_drawtext=drawtext,
                )
            )

        return variants

    def _build_ffmpeg_drawtext(self, headline: str, style: str) -> str:
        """Constructs deterministic FFmpeg drawtext parameters to burn the visual hook into the first 3 seconds of a 9:16 vertical video."""
        # Sanitize single quotes and colons for FFmpeg filter syntax
        sanitized = headline.replace("'", "").replace(":", "-").strip()

        if style == "top_banner_yellow":
            # Yellow banner with dark stroke near top of 9:16 screen (y=160)
            return (
                f"drawtext=text='{sanitized}':fontcolor=yellow:fontsize=48:font='Arial':"
                f"box=1:boxcolor=black@0.75:boxborderw=14:x=(w-text_w)/2:y=180:enable='between(t,0,3.5)'"
            )
        elif style == "center_glow_white":
            # Bold white text centered with solid backing
            return (
                f"drawtext=text='{sanitized}':fontcolor=white:fontsize=52:font='Arial':"
                f"box=1:boxcolor=black@0.85:boxborderw=18:x=(w-text_w)/2:y=(h-text_h)/2-100:enable='between(t,0,3.0)'"
            )
        else:
            # Lower third punchy style
            return (
                f"drawtext=text='{sanitized}':fontcolor=white:fontsize=44:font='Arial':"
                f"box=1:boxcolor=red@0.8:boxborderw=12:x=(w-text_w)/2:y=h-360:enable='between(t,0,3.5)'"
            )

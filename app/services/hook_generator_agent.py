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
        "style": "top_neon_pill",
        "prefix": "WHY NOBODY TALKS ABOUT",
    },
    {
        "type": "Contrarian",
        "style": "center_punch_title",
        "prefix": "STOP DOING THIS WITH",
    },
    {
        "type": "Problem-Agitation",
        "style": "lower_third_bar",
        "prefix": "THE NUMBER ONE MISTAKE IN",
    },
    {
        "type": "Direct Value",
        "style": "floating_frosted_card",
        "prefix": "THE UNTOLD SECRET OF",
    },
]


class HookGeneratorAgent:
    """Agent that generates attention-grabbing visual hooks and opening teaser overlays

    for viral short-form videos across multiple distinct copywriting archetypes and visual styles.
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

        for clip_idx, clip in enumerate(clips):
            variants: list[HookVariant] = []
            if self.client:
                try:
                    variants = self._generate_with_llm(clip, understanding, clip_idx)
                except Exception as e:
                    logger.warning(
                        f"LLM hook generation failed for clip {clip.id}: {e}. Using rule-based fallback."
                    )
                    variants = self._generate_fallback(clip, understanding, clip_idx)
            else:
                variants = self._generate_fallback(clip, understanding, clip_idx)

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
        clip_index: int = 0,
    ) -> list[HookVariant]:
        """Calls Groq LLM to craft 4 distinct viral hook variants based on viewer psychology."""
        topics = ", ".join(understanding.topics) if understanding else "General"
        tone = understanding.tone if understanding else "Engaging"

        prompt = f"""You are the VentiCut Hook Generator Agent, an expert short-form video copywriter specializing in TikTok, Instagram Reels, and YouTube Shorts.

Analyze the opening 3-5 seconds of this specific video clip (Clip #{clip_index + 1}) and craft 4 viral hook variations designed to stop viewers from swiping in the critical opening 3 seconds.

Clip Context:
- Segment Duration: {clip.duration:.1f} seconds
- Identified Topics: {topics}
- Tone: {tone}
- Spoken Hook Words: "{clip.hook_text}"
- Current Working Title: "{clip.headline}"

CRITICAL RULES:
1. Every headline MUST be completely unique and hyper-relevant to the exact words spoken in this segment.
2. DO NOT use repetitive cliches like "THE BRUTAL TRUTH", "NOBODY TALKS ABOUT", or "THE REAL REASON".
3. Use diverse psychological angles: Statistical Shock, Pattern Interrupt, Urgent Warning, or Counter-Intuitive Truth.
4. Keep headlines between 3 to 6 words, ALL CAPS, ultra-punchy.

Requirements:
Create exactly 4 hook variations across these 4 distinct viral archetypes and visual presentations:
1. "Curiosity Gap" with visual_style="top_neon_pill": Poses an irresistible mystery or unspoken pattern.
2. "Contrarian" with visual_style="center_punch_title": Challenges conventional wisdom during the opening pattern interrupt.
3. "Problem-Agitation" with visual_style="lower_third_bar": Highlights a frustrating mistake and promises immediate relief.
4. "Direct Value" with visual_style="floating_frosted_card": Delivers an immediate high-value framework or secret.

For each variation, supply:
- headline: 3 to 6 words, all-caps, ultra-punchy for an on-screen title card.
- spoken_hook: A refined, high-impact spoken opening sentence.
- hook_type: One of ["Curiosity Gap", "Contrarian", "Problem-Agitation", "Direct Value"].
- hook_score: Estimated 3-second retention score between 80.0 and 99.0.
- visual_style: One of ["top_neon_pill", "center_punch_title", "lower_third_bar", "floating_frosted_card"].

Respond ONLY with valid JSON in this exact structure:
{{
  "hooks": [
    {{
      "headline": "THE $4T MARKET SHOCKWAVE",
      "spoken_hook": "If you look at the raw data, this selloff was completely predictable.",
      "hook_type": "Curiosity Gap",
      "hook_score": 96.5,
      "visual_style": "top_neon_pill"
    }}
  ]
}}"""

        models_to_try = [self.model]
        if "qwen/qwen3.8-27b" not in models_to_try:
            models_to_try.append("qwen/qwen3.8-27b")

        response = None
        for m in models_to_try:
            try:
                response = self.client.chat.completions.create(
                    model=m,
                    messages=[
                        {
                            "role": "system",
                            "content": (
                                "You are a specialized viral hook copywriter for vertical video. "
                                "Never repeat cliche phrases. Always output raw JSON only."
                            ),
                        },
                        {"role": "user", "content": prompt},
                    ],
                    temperature=0.7,
                    max_tokens=800,
                )
                if response and response.choices and response.choices[0].message.content:
                    break
            except Exception as e:
                logger.warning(f"Groq model {m} failed: {e}. Trying fallback model if available.")

        if not response or not response.choices:
            raise ValueError("All Groq models failed to return hook variations.")

        if response.usage:
            token_tracker.record_groq_tokens(response.usage.total_tokens)

        content = response.choices[0].message.content or "{}"
        match = re.search(r"\{.*\}", content, re.DOTALL)
        raw_json = match.group(0) if match else content
        # Clean trailing commas
        cleaned_json = re.sub(r",\s*([\}\]])", r"", raw_json)

        raw_hooks = []
        try:
            data = json.loads(cleaned_json)
            raw_hooks = data.get("hooks", [])
        except Exception:
            # Fallback regex extraction if LLM JSON has minor syntax faults
            headline_matches = re.findall(r'"headline"\s*:\s*"([^"]+)"', content)
            spoken_matches = re.findall(r'"spoken_hook"\s*:\s*"([^"]+)"', content)
            visual_styles = [
                "top_neon_pill",
                "center_punch_title",
                "lower_third_bar",
                "floating_frosted_card",
            ]
            types = ["Curiosity Gap", "Contrarian", "Problem-Agitation", "Direct Value"]
            for idx, hl in enumerate(headline_matches):
                sp = spoken_matches[idx] if idx < len(spoken_matches) else clip.hook_text
                raw_hooks.append(
                    {
                        "headline": hl,
                        "spoken_hook": sp,
                        "hook_type": types[idx % len(types)],
                        "hook_score": 95.0 - (idx * 1.5),
                        "visual_style": visual_styles[idx % len(visual_styles)],
                    }
                )
        variants = []
        for h in raw_hooks:
            raw_headline = str(h.get("headline", clip.headline)).upper().strip()
            # Sanitize repetitive cliches
            sanitized_headline = re.sub(
                r"^THE BRUTAL TRUTH ABOUT\s*", "THE UNSEEN REALITY OF ", raw_headline
            )
            spoken = str(h.get("spoken_hook", clip.hook_text)).strip()
            hook_type = str(h.get("hook_type", "Curiosity Gap"))
            score = float(h.get("hook_score", 90.0))
            style = str(h.get("visual_style", "top_neon_pill"))

            drawtext = self._build_ffmpeg_drawtext(sanitized_headline, style)

            variants.append(
                HookVariant(
                    id=str(uuid.uuid4())[:8],
                    headline=sanitized_headline,
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
        clip_index: int = 0,
    ) -> list[HookVariant]:
        """Deterministic rule-based hook generation when LLM is unavailable."""
        base_headline = clip.headline.strip() if clip.headline else "VIRAL INSIGHT"
        spoken = (
            clip.hook_text.strip() if clip.hook_text else "Listen closely to what happens next."
        )

        stop_words = {
            "this",
            "that",
            "these",
            "those",
            "with",
            "from",
            "about",
            "what",
            "when",
            "where",
            "which",
            "could",
            "would",
            "should",
            "there",
            "their",
            "being",
            "having",
            "going",
            "because",
            "after",
            "before",
            "while",
            "highlight",
            "part",
            "clip",
            "video",
            "brutal",
            "truth",
            "almost",
            "nobody",
            "people",
            "really",
            "actually",
            "just",
            "very",
            "some",
            "other",
            "into",
            "over",
            "than",
            "then",
            "them",
            "they",
        }

        # Extract meaningful keywords from spoken hook, headline, or summary
        candidate_words = []
        for src in [clip.hook_text, base_headline, clip.summary]:
            if src:
                for w in re.findall(r"\b[A-Za-z]{4,}\b", src):
                    if w.lower() not in stop_words:
                        candidate_words.append(w.upper())

        kw1 = candidate_words[0] if len(candidate_words) > 0 else "MARKET TRENDS"
        kw2 = candidate_words[1] if len(candidate_words) > 1 else "HIDDEN PATTERNS"

        # Catalog of diverse dynamic viral headline patterns grouped by archetype
        template_pool = [
            # Set 0: Pattern Interrupt & Revelation
            [
                (
                    "Curiosity Gap",
                    "top_neon_pill",
                    f"WHY {kw1} CHANGED FOREVER",
                    f"Almost nobody caught what just happened with {kw1.lower()}.",
                ),
                (
                    "Contrarian",
                    "center_punch_title",
                    f"STOP IGNORING THIS {kw1} WARNING",
                    f"Everything you were told about {kw1.lower()} is backwards.",
                ),
                (
                    "Problem-Agitation",
                    "lower_third_bar",
                    f"THE FATAL {kw1} MISTAKE",
                    f"If you keep ignoring {kw1.lower()}, you will face the consequences.",
                ),
                ("Direct Value", "floating_frosted_card", f"HOW {kw2} ACTUALLY WORKS", spoken),
            ],
            # Set 1: High Stakes & Shock
            [
                (
                    "Curiosity Gap",
                    "top_neon_pill",
                    f"THE SECRET BEHIND {kw1}",
                    f"Here is the part about {kw1.lower()} that no one explains.",
                ),
                (
                    "Contrarian",
                    "center_punch_title",
                    f"WHY {kw1} IS NOT WHAT YOU THINK",
                    f"Most people assume {kw1.lower()} is fine, but the data says otherwise.",
                ),
                (
                    "Problem-Agitation",
                    "lower_third_bar",
                    f"THE DANGER OF {kw1}",
                    f"Watch what happens when {kw1.lower()} reaches its breaking point.",
                ),
                ("Direct Value", "floating_frosted_card", f"THE {kw2} BREAKTHROUGH", spoken),
            ],
            # Set 2: Urgent Disruption
            [
                (
                    "Curiosity Gap",
                    "top_neon_pill",
                    f"WHAT HAPPENED TO {kw1}",
                    f"This single shift in {kw1.lower()} changed the entire equation.",
                ),
                (
                    "Contrarian",
                    "center_punch_title",
                    f"THE BIG LIE ABOUT {kw1}",
                    f"Do not fall for the narrative around {kw1.lower()}.",
                ),
                (
                    "Problem-Agitation",
                    "lower_third_bar",
                    f"THE HIDDEN COST OF {kw1}",
                    f"You are likely paying the price for {kw1.lower()} right now.",
                ),
                ("Direct Value", "floating_frosted_card", f"MASTERING {kw2} IN 2026", spoken),
            ],
            # Set 3: Insider Strategy
            [
                (
                    "Curiosity Gap",
                    "top_neon_pill",
                    f"THE UNTOLD STORY OF {kw1}",
                    f"Here is what happened behind closed doors regarding {kw1.lower()}.",
                ),
                (
                    "Contrarian",
                    "center_punch_title",
                    f"FORGET EVERYTHING ABOUT {kw1}",
                    f"The conventional wisdom on {kw1.lower()} just broke down.",
                ),
                (
                    "Problem-Agitation",
                    "lower_third_bar",
                    f"BEFORE YOU TOUCH {kw1}",
                    f"Make sure you understand this key risk with {kw1.lower()} first.",
                ),
                ("Direct Value", "floating_frosted_card", f"THE {kw2} BLUEPRINT", spoken),
            ],
        ]

        chosen_set = template_pool[clip_index % len(template_pool)]
        # Dynamic base scores that vary per clip index so variant choice is diverse
        base_scores = [95.0, 93.5, 91.0, 94.0]
        # Shift scores so different archetypes win on different clips
        shift = clip_index % 4
        rotated_scores = base_scores[shift:] + base_scores[:shift]

        variants = []
        for i, (hook_type, style, headline, spoken_teaser) in enumerate(chosen_set):
            drawtext = self._build_ffmpeg_drawtext(headline, style)
            variants.append(
                HookVariant(
                    id=str(uuid.uuid4())[:8],
                    headline=headline,
                    spoken_hook=spoken_teaser,
                    hook_type=hook_type,
                    hook_score=rotated_scores[i],
                    visual_style=style,
                    ffmpeg_drawtext=drawtext,
                )
            )

        return variants

    def _build_ffmpeg_drawtext(self, headline: str, style: str) -> str:
        """Constructs deterministic FFmpeg drawtext parameters across multiple distinct visual hook presentations."""
        sanitized = headline.replace("'", "").replace(":", " - ").replace("%", "\\%").strip()

        if style in ("top_neon_pill", "top_banner_yellow"):
            # Top neon yellow pill at y=180
            return (
                f"drawtext=text='{sanitized}':fontcolor=yellow:fontsize=48:font='Arial':"
                f"box=1:boxcolor=black@0.8:boxborderw=16:x=(w-text_w)/2:y=180:enable='between(t,0,3.5)'"
            )
        elif style in ("center_punch_title", "center_glow_white"):
            # Centered punchy impact headline during initial 2.5s pattern-interrupt zoom
            return (
                f"drawtext=text='{sanitized}':fontcolor=white:fontsize=54:font='Arial':"
                f"box=1:boxcolor=black@0.88:boxborderw=20:x=(w-text_w)/2:y=(h-text_h)/2-100:enable='between(t,0,2.5)'"
            )
        elif style in ("lower_third_bar", "lower_third_punchy"):
            # Bottom third dark bar with red/amber accent at y=h-380
            return (
                f"drawtext=text='{sanitized}':fontcolor=white:fontsize=46:font='Arial':"
                f"box=1:boxcolor=red@0.85:boxborderw=14:x=(w-text_w)/2:y=h-380:enable='between(t,0,3.5)'"
            )
        elif style == "floating_frosted_card":
            # Frosted floating card at upper-center y=260
            return (
                f"drawtext=text='{sanitized}':fontcolor=0x38bdf8:fontsize=44:font='Arial':"
                f"box=1:boxcolor=0x0b1120@0.85:boxborderw=14:x=(w-text_w)/2:y=260:enable='between(t,0,3.5)'"
            )
        else:
            return (
                f"drawtext=text='{sanitized}':fontcolor=white:fontsize=46:font='Arial':"
                f"box=1:boxcolor=black@0.8:boxborderw=14:x=(w-text_w)/2:y=180:enable='between(t,0,3.5)'"
            )

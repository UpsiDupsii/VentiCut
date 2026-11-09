import json
import logging
import re

from groq import Groq

from app.core.config import settings
from app.models.clip import (
    ClipHighlight,
    PlatformPostCopy,
    SocialDistributionMetadata,
    VideoUnderstandingResult,
)
from app.services.token_tracker import token_tracker

logger = logging.getLogger(__name__)


class SocialMetadataAgent:
    """Agent that crafts platform-optimized titles, descriptions, hashtags, and pinned comments

    specifically engineered for YouTube Shorts, TikTok, and Instagram Reels algorithms.
    """

    def __init__(self, api_key: str | None = None, model: str | None = None):
        self.api_key = api_key or settings.GROQ_API_KEY
        self.model = model or settings.GROQ_LLM_MODEL
        self.client = Groq(api_key=self.api_key) if self.api_key else None

    def generate_metadata_for_clips(
        self,
        clips: list[ClipHighlight],
        understanding: VideoUnderstandingResult | None = None,
    ) -> list[ClipHighlight]:
        """Generates distribution packages for all clips across YouTube Shorts, TikTok, and Reels."""
        if not clips:
            return []

        for clip in clips:
            try:
                metadata = self.generate_clip_metadata(clip, understanding)
                clip.social_metadata = metadata
            except Exception as e:
                logger.warning(f"Social metadata generation failed for clip {clip.id}: {e}")
                clip.social_metadata = self._generate_fallback(clip, understanding)

        return clips

    def generate_clip_metadata(
        self,
        clip: ClipHighlight,
        understanding: VideoUnderstandingResult | None = None,
    ) -> SocialDistributionMetadata:
        """Invokes Groq LLM or falls back to rule-based platform copy generation."""
        if self.client:
            try:
                return self._generate_with_llm(clip, understanding)
            except Exception as e:
                logger.warning(
                    f"LLM social metadata failed for clip {clip.id}: {e}. Using fallback."
                )

        return self._generate_fallback(clip, understanding)

    def _generate_with_llm(
        self,
        clip: ClipHighlight,
        understanding: VideoUnderstandingResult | None,
    ) -> SocialDistributionMetadata:
        """Prompts Groq LLM to generate platform-specific post copy tailored for Shorts, TikTok, and Reels."""
        topics = ", ".join(understanding.topics) if understanding else "Viral Insights"
        tone = understanding.tone if understanding else "Engaging"

        prompt = f"""You are the VentiCut Social Metadata and SEO Agent, an expert in social video algorithms.

Craft platform-tailored distribution packages for this vertical short clip across YouTube Shorts, TikTok, and Instagram Reels.

Clip Details:
- Title: "{clip.headline}"
- Spoken Hook: "{clip.hook_text}"
- Summary: "{clip.summary or "Key insight"}"
- Primary Topics: {topics}
- Tone: {tone}

Requirements:
1. YouTube Shorts:
   - title: Under 60 chars, high-CTR, append #Shorts.
   - caption: 2 sentences explaining context + search keywords.
   - hashtags: 5 targeted tags.
   - pinned_comment: An open-ended question to ignite debate.
   - call_to_action: "Subscribe for more insights!"
2. TikTok:
   - title: Punchy 3-5 word hook.
   - caption: Conversational 1-2 lines with cliffhanger.
   - hashtags: 5 viral tags including #fyp, #foryou.
   - pinned_comment: Provocative question to boost comment rank.
   - call_to_action: "Follow for daily clips!"
3. Instagram Reels:
   - title: Aesthetic clean title.
   - caption: Storytelling caption formatted with clear paragraph breaks.
   - hashtags: 10-12 tags across broad, niche, and community categories.
   - pinned_comment: Encouragement to save the reel.
   - call_to_action: "Save this reel and share with someone who needs it!"

Respond ONLY with valid JSON in this exact structure:
{{
  "youtube_shorts": {{
    "title": "The AI Shockwave Explained #Shorts",
    "caption": "Here is why the AI market shifted overnight and what it means for creators. Watch until the end for the full breakdown.",
    "hashtags": ["#Shorts", "#AI", "#Tech", "#Finance", "#Viral"],
    "pinned_comment": "Do you agree with this take? Let me know your thoughts below!",
    "call_to_action": "Subscribe for daily deep-dives!"
  }},
  "tiktok": {{
    "title": "Why AI Just Shifted",
    "caption": "Nobody expected this to happen so quickly... wait for the conclusion.",
    "hashtags": ["#fyp", "#foryou", "#tech", "#ai", "#business"],
    "pinned_comment": "What would you have done here?",
    "call_to_action": "Follow for more daily clips!"
  }},
  "instagram_reels": {{
    "title": "The Hidden AI Shift",
    "caption": "Everything changes when capital allocation meets market reality.\n\nHere is what most analysts completely missed during this cycle.",
    "hashtags": ["#reels", "#explore", "#techtrends", "#businessinsights", "#futureoftech", "#productivity"],
    "pinned_comment": "Drop a save if this resonated with you.",
    "call_to_action": "Save this reel for later!"
  }}
}}"""

        models = [self.model]
        if "qwen/qwen3.8-27b" not in models:
            models.append("qwen/qwen3.8-27b")

        response = None
        for m in models:
            try:
                response = self.client.chat.completions.create(
                    model=m,
                    messages=[
                        {
                            "role": "system",
                            "content": (
                                "You are a specialized social media copywriter. "
                                "Always output valid JSON only."
                            ),
                        },
                        {"role": "user", "content": prompt},
                    ],
                    response_format={"type": "json_object"},
                    temperature=0.4,
                    max_tokens=900,
                )
                if response and response.choices and response.choices[0].message.content:
                    break
            except Exception as e:
                logger.warning(f"Groq model {m} failed for social metadata: {e}")

        if not response or not response.choices:
            raise ValueError("Groq failed to return social metadata.")

        if response.usage:
            token_tracker.record_groq_tokens(response.usage.total_tokens)

        content = response.choices[0].message.content or "{}"
        match = re.search(r"\{.*\}", content, re.DOTALL)
        raw_json = match.group(0) if match else content
        # Clean trailing commas
        cleaned_json = re.sub(r",\s*([\}\]])", r"\1", raw_json)
        data = json.loads(cleaned_json)

        return SocialDistributionMetadata(
            youtube_shorts=PlatformPostCopy(**data.get("youtube_shorts", {})),
            tiktok=PlatformPostCopy(**data.get("tiktok", {})),
            instagram_reels=PlatformPostCopy(**data.get("instagram_reels", {})),
        )

    def _generate_fallback(
        self,
        clip: ClipHighlight,
        understanding: VideoUnderstandingResult | None,
    ) -> SocialDistributionMetadata:
        """Deterministic rule-based distribution packaging if LLM is unavailable."""
        headline = clip.headline.strip() if clip.headline else "Viral Short"
        words = [w for w in re.findall(r"\b[A-Za-z]{3,}\b", headline) if len(w) > 3]
        topic = words[0].capitalize() if words else "Insight"

        yt_title = f"{headline[:50]} #Shorts"
        yt_caption = f"{clip.hook_text or headline}. Watch until the end for the key takeaway."
        yt_tags = ["#Shorts", f"#{topic}", "#Viral", "#Trending", "#Creator"]

        tt_title = headline[:40]
        tt_caption = f"{clip.hook_text or headline} What are your thoughts on this?"
        tt_tags = ["#fyp", "#foryou", f"#{topic.lower()}", "#viral", "#trending"]

        ig_title = headline
        ig_caption = f"{headline}\n\n{clip.hook_text or 'Listen closely to what happens next.'}\n\nSave this for later."
        ig_tags = [
            "#reels",
            "#explore",
            f"#{topic.lower()}",
            "#dailyinsights",
            "#trendingreels",
            "#viralpost",
        ]

        return SocialDistributionMetadata(
            youtube_shorts=PlatformPostCopy(
                title=yt_title,
                caption=yt_caption,
                hashtags=yt_tags,
                pinned_comment=f"What is your perspective on {topic.lower()}? Let us know in the comments!",
                call_to_action="Subscribe to VentiCut for more daily vertical shorts!",
            ),
            tiktok=PlatformPostCopy(
                title=tt_title,
                caption=tt_caption,
                hashtags=tt_tags,
                pinned_comment="Would you agree with this? Drop your thoughts below.",
                call_to_action="Follow for more daily viral clips!",
            ),
            instagram_reels=PlatformPostCopy(
                title=ig_title,
                caption=ig_caption,
                hashtags=ig_tags,
                pinned_comment="Save this reel so you have it handy when you need it.",
                call_to_action="Save and share this reel with a friend!",
            ),
        )

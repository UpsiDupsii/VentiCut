import logging
import re
import subprocess
from pathlib import Path

from app.core.config import settings
from app.models.clip import (
    CaptionStylePreset,
    ClipHighlight,
    TranscriptionResult,
    WordTimestamp,
)

logger = logging.getLogger(__name__)

# Color constants in ASS format: &HAABBGGRR& (Hex Alpha, Blue, Green, Red)
ASS_WHITE = "&H00FFFFFF&"
ASS_BLACK = "&H00000000&"
ASS_ELECTRIC_YELLOW = "&H001FE8FF&"  # #FFE81F in BGR
ASS_NEON_LIME = "&H0000FF66&"  # #66FF00 in BGR
ASS_NEON_CYAN = "&H00FFFF00&"  # #00FFFF in BGR
ASS_CORAL_AMBER = "&H001155FF&"  # #FF5511 in BGR
ASS_MUTED_SILVER = "&H00E0E0E0&"
ASS_MAGENTA_PINK = "&H00D020FF&"  # #FF20D0 in BGR
ASS_TRANSLUCENT_BLACK = "&H80121118&"
ASS_FROSTED_DARK = "&HA0151515&"

CAPTION_PRESETS: dict[str, dict] = {
    "hormozi_glow": {
        "id": "hormozi_glow",
        "name": "Alex Hormozi Glow",
        "description": "High-contrast white text with spoken active words popping in electric neon lime.",
        "font_name": "Arial",
        "font_size": 58,
        "primary_color": ASS_WHITE,
        "secondary_color": ASS_MUTED_SILVER,
        "outline_color": ASS_BLACK,
        "back_color": ASS_BLACK,
        "active_color": ASS_NEON_LIME,
        "outline_width": 3.6,
        "shadow_depth": 2.2,
        "alignment": 2,  # Bottom center
        "margin_v": 240,
        "border_style": 1,
        "words_per_batch": 3,
        "strategy": "active_word_highlight",
        "badge_style": "neon_green",
    },
    "mrbeast_yellow": {
        "id": "mrbeast_yellow",
        "name": "MrBeast Viral Yellow",
        "description": "Giant bold yellow uppercase text with thick black stroke and radiant white active flash.",
        "font_name": "Impact",
        "font_size": 62,
        "primary_color": ASS_ELECTRIC_YELLOW,
        "secondary_color": ASS_WHITE,
        "outline_color": ASS_BLACK,
        "back_color": ASS_BLACK,
        "active_color": ASS_WHITE,
        "outline_width": 4.0,
        "shadow_depth": 3.0,
        "alignment": 2,  # Bottom center
        "margin_v": 240,
        "border_style": 1,
        "words_per_batch": 3,
        "strategy": "active_word_highlight",
        "badge_style": "yellow",
    },
    "karaoke_fill": {
        "id": "karaoke_fill",
        "name": "Karaoke Wave Fill",
        "description": "Progressive smooth syllable color wipe filling into vibrant coral amber as spoken.",
        "font_name": "Arial",
        "font_size": 56,
        "primary_color": ASS_CORAL_AMBER,
        "secondary_color": ASS_MUTED_SILVER,
        "outline_color": ASS_BLACK,
        "back_color": ASS_BLACK,
        "active_color": ASS_CORAL_AMBER,
        "outline_width": 3.0,
        "shadow_depth": 2.0,
        "alignment": 2,
        "margin_v": 240,
        "border_style": 1,
        "words_per_batch": 4,
        "strategy": "karaoke_fill",
        "badge_style": "coral_wave",
    },
    "tiktok_badge": {
        "id": "tiktok_badge",
        "name": "TikTok Frosted Pill",
        "description": "Clean modern sans on a floating obsidian frosted badge with electric magenta highlights.",
        "font_name": "Arial",
        "font_size": 54,
        "primary_color": ASS_WHITE,
        "secondary_color": ASS_MUTED_SILVER,
        "outline_color": ASS_BLACK,
        "back_color": ASS_TRANSLUCENT_BLACK,
        "active_color": ASS_MAGENTA_PINK,
        "outline_width": 2.0,
        "shadow_depth": 0.0,
        "alignment": 2,
        "margin_v": 240,
        "border_style": 3,  # Opaque bounding box
        "words_per_batch": 2,
        "strategy": "active_word_highlight",
        "badge_style": "magenta_pill",
    },
    "minimal_clean": {
        "id": "minimal_clean",
        "name": "Minimalist Clean",
        "description": "Subtle elegant documentary subtitles with frosted lower-third background.",
        "font_name": "Arial",
        "font_size": 48,
        "primary_color": ASS_WHITE,
        "secondary_color": ASS_MUTED_SILVER,
        "outline_color": ASS_BLACK,
        "back_color": ASS_FROSTED_DARK,
        "active_color": ASS_WHITE,
        "outline_width": 1.5,
        "shadow_depth": 1.0,
        "alignment": 2,
        "margin_v": 200,
        "border_style": 3,  # Subtle bounding box
        "words_per_batch": 5,
        "strategy": "phrase_subtitles",
        "badge_style": "clean_frosted",
    },
}


class CaptionAgent:
    """Agent that generates synchronized, animated, multi-style video subtitles

    using Advanced SubStation Alpha (ASS) and deterministic FFmpeg rendering.
    """

    def __init__(self, output_dir: Path | None = None):
        self.output_dir = output_dir or settings.PROCESSED_DIR
        self.output_dir.mkdir(parents=True, exist_ok=True)

    @classmethod
    def list_styles(cls) -> list[CaptionStylePreset]:
        """Returns structured metadata for all available creative caption styles."""
        presets = []
        for p in CAPTION_PRESETS.values():
            presets.append(
                CaptionStylePreset(
                    id=p["id"],
                    name=p["name"],
                    description=p["description"],
                    font_name=p["font_name"],
                    primary_color=p["primary_color"],
                    highlight_color=p["active_color"],
                    badge_style=p["badge_style"],
                )
            )
        return presets

    def caption_clips(
        self,
        clips: list[ClipHighlight],
        transcription: TranscriptionResult | None,
        default_style: str = "hormozi_glow",
    ) -> list[ClipHighlight]:
        """Generates synchronized ASS subtitles and burns captions into all rendered clips."""
        if not clips:
            return clips

        for clip in clips:
            try:
                style_to_use = clip.caption_style or default_style
                if style_to_use not in CAPTION_PRESETS:
                    style_to_use = "hormozi_glow"

                clip.caption_style = style_to_use
                clip.available_caption_styles = list(CAPTION_PRESETS.keys())

                # Generate the ASS subtitle file containing actual spoken voice dialogues
                ass_path, word_count = self.generate_ass_file(clip, transcription, style_to_use)
                clip.subtitles_ass_path = str(ass_path)
                clip.caption_word_count = word_count

                # If clip already has a rendered video, burn captions into it
                if clip.rendered_video_path and Path(clip.rendered_video_path).exists():
                    captioned_path = self.burn_captions_into_video(
                        video_path=Path(clip.rendered_video_path),
                        ass_path=ass_path,
                        clip_id=clip.id,
                    )
                    clip.rendered_video_path = str(captioned_path)
                    clip.rendered_url = f"/api/v1/clips/downloads/{clip.id}"
                    caption_label = f"animated captions ({style_to_use})"
                    if caption_label not in clip.editing_effects:
                        clip.editing_effects.append(caption_label)

            except Exception as e:
                logger.error(f"Failed to generate captions for clip {clip.id}: {e}")

        return clips

    def generate_ass_file(
        self,
        clip: ClipHighlight,
        transcription: TranscriptionResult | None,
        style_id: str = "hormozi_glow",
    ) -> tuple[Path, int]:
        """Builds a frame-accurate ASS subtitle file synchronized to word timestamps."""
        preset = CAPTION_PRESETS.get(style_id, CAPTION_PRESETS["hormozi_glow"])
        ass_filename = f"{clip.id}_{style_id}.ass"
        ass_path = self.output_dir / ass_filename

        # Extract spoken voice dialogue words belonging to this clip window
        words = self._extract_clip_words(clip, transcription)

        # Generate ASS document content
        ass_content = self._build_ass_script(
            clip=clip,
            words=words,
            preset=preset,
        )

        with ass_path.open("w", encoding="utf-8") as f:
            f.write(ass_content)

        logger.info(
            f"Generated spoken voice ASS subtitles for clip {clip.id} ({len(words)} dialogue words): {ass_path}"
        )
        return ass_path, len(words)

    def burn_captions_into_video(
        self,
        video_path: Path,
        ass_path: Path,
        clip_id: str,
    ) -> Path:
        """Executes FFmpeg with libass filter to burn spoken animated subtitles onto the 9:16 vertical video."""
        temp_captioned_path = self.output_dir / f"{clip_id}_captioned_temp.mp4"

        # Properly format path for Windows FFmpeg:
        # Forward slashes + escaped colon for drive letters (e.g., C\:/path/to/subtitles.ass)
        resolved_ass = str(ass_path.resolve()).replace("\\", "/")
        escaped_ass_path = resolved_ass.replace(":", "\\:")

        cmd = [
            "ffmpeg",
            "-y",
            "-i",
            str(video_path),
            "-vf",
            f"ass=filename='{escaped_ass_path}'",
            "-c:v",
            "libx264",
            "-preset",
            "ultrafast",
            "-c:a",
            "copy",
            str(temp_captioned_path),
        ]

        logger.info(f"Burning spoken dialogue captions into {clip_id}: {' '.join(cmd)}")
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=180,
        )

        if result.returncode != 0:
            logger.warning(
                f"FFmpeg caption burn failed ({result.stderr}). Retrying with relative path."
            )
            rel_ass_path = str(ass_path).replace("\\", "/")
            alt_cmd = [
                "ffmpeg",
                "-y",
                "-i",
                str(video_path),
                "-vf",
                f"ass=filename='{rel_ass_path}'",
                "-c:v",
                "libx264",
                "-preset",
                "ultrafast",
                "-c:a",
                "copy",
                str(temp_captioned_path),
            ]
            alt_res = subprocess.run(alt_cmd, capture_output=True, text=True, timeout=120)
            if alt_res.returncode != 0:
                logger.error(f"Subtitle burning fallback failed: {alt_res.stderr}")
                return video_path

        # Atomically replace target file
        final_path = self.output_dir / f"{clip_id}.mp4"
        if temp_captioned_path.exists():
            if final_path.exists():
                try:
                    final_path.unlink()
                except Exception:
                    pass
            temp_captioned_path.rename(final_path)
            return final_path

        return video_path

    def _extract_clip_words(
        self,
        clip: ClipHighlight,
        transcription: TranscriptionResult | None,
    ) -> list[WordTimestamp]:
        """Extracts spoken dialogue word timestamps relative to clip start time (0.00s)."""
        if not transcription:
            return self._synthesize_fallback_words(clip)

        words_in_clip: list[WordTimestamp] = []
        clip_start = clip.start_time
        clip_end = clip.end_time

        has_word_timestamps = False
        for segment in transcription.segments:
            # Check if segment overlaps clip
            if segment.end < clip_start - 0.2 or segment.start > clip_end + 0.2:
                continue

            if segment.words:
                has_word_timestamps = True
                for w in segment.words:
                    if w.end >= clip_start and w.start <= clip_end:
                        rel_start = max(0.0, w.start - clip_start)
                        rel_end = min(clip.duration, w.end - clip_start)
                        if rel_end > rel_start:
                            words_in_clip.append(
                                WordTimestamp(
                                    word=w.word.strip().upper(),
                                    start=rel_start,
                                    end=rel_end,
                                )
                            )

        # If transcription segments had no sub-token words, interpolate from segment texts
        if not has_word_timestamps or not words_in_clip:
            words_in_clip = self._synthesize_from_segments(clip, transcription)

        return words_in_clip

    def _synthesize_from_segments(
        self,
        clip: ClipHighlight,
        transcription: TranscriptionResult,
    ) -> list[WordTimestamp]:
        """Interpolates spoken dialogue words evenly across segment durations when word tokens are missing."""
        words_in_clip: list[WordTimestamp] = []
        clip_start = clip.start_time
        clip_end = clip.end_time

        for segment in transcription.segments:
            if segment.end < clip_start or segment.start > clip_end:
                continue

            seg_text = segment.text.strip()
            raw_tokens = [t for t in re.split(r"\s+", seg_text) if t]
            if not raw_tokens:
                continue

            seg_rel_start = max(0.0, segment.start - clip_start)
            seg_rel_end = min(clip.duration, segment.end - clip_start)
            seg_dur = max(0.3, seg_rel_end - seg_rel_start)
            word_dur = seg_dur / len(raw_tokens)

            for i, token in enumerate(raw_tokens):
                w_start = seg_rel_start + (i * word_dur)
                w_end = min(clip.duration, w_start + word_dur)
                words_in_clip.append(
                    WordTimestamp(
                        word=token.strip().upper(),
                        start=w_start,
                        end=w_end,
                    )
                )

        if not words_in_clip:
            return self._synthesize_fallback_words(clip)

        return words_in_clip

    def _synthesize_fallback_words(self, clip: ClipHighlight) -> list[WordTimestamp]:
        """Fallback dialogue words if no transcription is available."""
        source_text = clip.hook_text or "LISTEN CLOSELY TO THIS MOMENT"
        tokens = [t.strip().upper() for t in re.split(r"\s+", source_text) if t]
        if not tokens:
            tokens = ["VENTICUT", "VIRAL", "CLIP"]

        word_dur = min(0.45, max(0.25, clip.duration / max(1, len(tokens))))
        words = []
        cur_t = 0.5
        for token in tokens:
            if cur_t >= clip.duration - 0.5:
                break
            words.append(
                WordTimestamp(
                    word=token,
                    start=cur_t,
                    end=min(clip.duration, cur_t + word_dur),
                )
            )
            cur_t += word_dur

        return words

    def _build_ass_script(
        self,
        clip: ClipHighlight,
        words: list[WordTimestamp],
        preset: dict,
    ) -> str:
        """Assembles complete ASS v4.00+ subtitle file structure."""
        font_name = preset["font_name"]
        font_size = preset["font_size"]
        primary_col = preset["primary_color"]
        sec_col = preset["secondary_color"]
        outline_col = preset["outline_color"]
        back_col = preset["back_color"]
        outline_w = preset["outline_width"]
        shadow_d = preset["shadow_depth"]
        alignment = preset["alignment"]
        margin_v = preset["margin_v"]
        border_style = preset["border_style"]

        header = f"""[Script Info]
Title: VentiCut Captions - {clip.id}
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,{font_name},{font_size},{primary_col},{sec_col},{outline_col},{back_col},-1,0,0,0,100,100,0,0,{border_style},{outline_w},{shadow_d},{alignment},60,60,{margin_v},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

        events = self._generate_dialogue_events(words, preset, clip.duration)
        return header + "\n".join(events) + "\n"

    def _generate_dialogue_events(
        self,
        words: list[WordTimestamp],
        preset: dict,
        max_duration: float,
    ) -> list[str]:
        """Generates synchronized ASS dialogue events according to the style strategy."""
        if not words:
            return []

        strategy = preset["strategy"]
        words_per_batch = preset["words_per_batch"]
        primary_col = preset["primary_color"]
        active_col = preset["active_color"]

        # Group words into batches
        batches: list[list[WordTimestamp]] = []
        current_batch: list[WordTimestamp] = []

        for word in words:
            current_batch.append(word)
            ends_sentence = word.word.endswith((".", "!", "?"))
            if len(current_batch) >= words_per_batch or ends_sentence:
                batches.append(current_batch)
                current_batch = []

        if current_batch:
            batches.append(current_batch)

        events: list[str] = []

        for batch in batches:
            if not batch:
                continue

            batch_start = max(0.0, batch[0].start)
            batch_end = min(max_duration, batch[-1].end)
            if batch_end <= batch_start:
                batch_end = batch_start + 0.5

            if strategy == "active_word_highlight":
                # Create a micro-event for each word where that specific word is highlighted
                for idx, active_word in enumerate(batch):
                    w_start = max(batch_start, active_word.start)
                    w_end = min(batch_end, active_word.end)
                    if w_end <= w_start:
                        w_end = w_start + 0.2

                    line_parts = []
                    for j, w in enumerate(batch):
                        clean_w = re.sub(r"[^\w\s\$\%\-\'\!\?]", "", w.word)
                        if j == idx:
                            line_parts.append(f"{{\\c{active_col}}}{clean_w}{{\\c{primary_col}}}")
                        else:
                            line_parts.append(clean_w)

                    rendered_text = " ".join(line_parts)
                    start_str = self._format_ass_time(w_start)
                    end_str = self._format_ass_time(w_end)
                    events.append(
                        f"Dialogue: 0,{start_str},{end_str},Default,,0,0,0,,{rendered_text}"
                    )

            elif strategy == "karaoke_fill":
                karaoke_parts = []
                last_time = batch_start
                for w in batch:
                    clean_w = re.sub(r"[^\w\s\$\%\-\'\!\?]", "", w.word)
                    cs = max(10, int(round((w.end - last_time) * 100)))
                    karaoke_parts.append(f"{{\\k{cs}}}{clean_w}")
                    last_time = w.end

                rendered_text = " ".join(karaoke_parts)
                start_str = self._format_ass_time(batch_start)
                end_str = self._format_ass_time(batch_end)
                events.append(f"Dialogue: 0,{start_str},{end_str},Default,,0,0,0,,{rendered_text}")

            else:
                # phrase_subtitles / minimal clean
                tokens = [re.sub(r"[^\w\s\$\%\-\'\!\?]", "", w.word) for w in batch]
                rendered_text = " ".join(tokens)
                start_str = self._format_ass_time(batch_start)
                end_str = self._format_ass_time(batch_end)
                events.append(f"Dialogue: 0,{start_str},{end_str},Default,,0,0,0,,{rendered_text}")

        return events

    def _format_ass_time(self, seconds: float) -> str:
        """Formats seconds into ASS timestamp: H:MM:SS.cs (centiseconds)."""
        seconds = max(0.0, seconds)
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        centis = int(round((seconds - int(seconds)) * 100))
        if centis >= 100:
            secs += 1
            centis = 0
        return f"{hours}:{minutes:02d}:{secs:02d}.{centis:02d}"

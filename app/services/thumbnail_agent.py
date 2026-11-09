import logging
import os
import subprocess
import uuid
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageStat

from app.core.config import settings
from app.models.clip import ClipHighlight

logger = logging.getLogger(__name__)


class ThumbnailAgent:
    """Agent that automatically selects the highest-engagement frame from vertical shorts

    and designs an eye-catching 9:16 cover thumbnail image with high-contrast text overlay.
    """

    def __init__(self, output_dir: Path | None = None):
        self.output_dir = output_dir or settings.PROCESSED_DIR
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.temp_dir = settings.TEMP_DIR
        self.temp_dir.mkdir(parents=True, exist_ok=True)

    def generate_thumbnails(self, clips: list[ClipHighlight]) -> list[ClipHighlight]:
        """Generates and binds optimized 9:16 cover thumbnails for all clips."""
        if not clips:
            return []

        for clip in clips:
            try:
                self.generate_thumbnail_for_clip(clip)
            except Exception as e:
                logger.warning(f"Thumbnail generation failed for clip {clip.id}: {e}")

        return clips

    def generate_thumbnail_for_clip(self, clip: ClipHighlight) -> ClipHighlight:
        """Extracts optimal candidate frame and renders high-contrast cover text."""
        # Locate rendered video path
        video_path = None
        if clip.rendered_video_path and Path(clip.rendered_video_path).exists():
            video_path = Path(clip.rendered_video_path)
        else:
            potential_file = self.output_dir / f"{clip.id}.mp4"
            if potential_file.exists():
                video_path = potential_file

        dur = max(3.0, clip.duration)
        candidates = [
            1.2,
            min(dur - 0.5, 2.8),
            round(dur * 0.45, 2),
            round(dur * 0.70, 2),
        ]

        best_img = None
        best_score = -1.0
        best_time = candidates[0]

        if video_path and video_path.exists():
            temp_paths: list[Path] = []
            for t in candidates:
                sample_path = self.temp_dir / f"sample_{clip.id}_{uuid.uuid4().hex[:6]}_{t}.jpg"
                temp_paths.append(sample_path)

                cmd = [
                    "ffmpeg",
                    "-y",
                    "-ss",
                    str(t),
                    "-i",
                    str(video_path),
                    "-vframes",
                    "1",
                    "-q:v",
                    "2",
                    str(sample_path),
                ]
                res = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
                if (
                    res.returncode == 0
                    and sample_path.exists()
                    and sample_path.stat().st_size > 1000
                ):
                    try:
                        with Image.open(sample_path) as im:
                            img_copy = im.convert("RGB")
                            score = self._score_frame(img_copy)
                            if score > best_score:
                                best_score = score
                                best_img = img_copy
                                best_time = t
                    except Exception:
                        pass

            # Cleanup candidate sample files
            for p in temp_paths:
                if p.exists():
                    try:
                        p.unlink()
                    except Exception:
                        pass

        if not best_img:
            # Fallback high-contrast dark canvas
            best_img = Image.new("RGB", (1080, 1920), color=(15, 23, 42))

        # Apply cover typography and gradient overlay
        final_thumb = self._apply_cover_typography(best_img, clip)

        # Save final thumbnail
        target_path = self.output_dir / f"{clip.id}_thumb.jpg"
        final_thumb.save(target_path, "JPEG", quality=92, optimize=True)

        clip.thumbnail_path = str(target_path)
        clip.thumbnail_url = f"/api/v1/clips/{clip.id}/thumbnail"
        clip.thumbnail_timestamp = round(best_time, 2)
        return clip

    def _score_frame(self, im: Image.Image) -> float:
        """Heuristic scoring evaluating contrast, brightness, and visual sharpness."""
        # Resize to fast evaluation thumbnail
        thumb = im.resize((320, 568))
        stat = ImageStat.Stat(thumb)
        mean_brightness = sum(stat.mean) / 3.0
        stddev_contrast = sum(stat.stddev) / 3.0

        # Penalize completely dark (<35) or blown-out (>230) frames
        brightness_penalty = 0.0
        if mean_brightness < 40:
            brightness_penalty = (40 - mean_brightness) * 1.5
        elif mean_brightness > 220:
            brightness_penalty = (mean_brightness - 220) * 1.5

        # Score is proportional to contrast and healthy illumination
        score = max(0.0, stddev_contrast * 2.0 - brightness_penalty)
        return score

    def _apply_cover_typography(self, base_image: Image.Image, clip: ClipHighlight) -> Image.Image:
        """Renders high-contrast headline banner and dark vignette for thumbnail readability."""
        # Ensure 1080x1920 dimensions
        if base_image.size != (1080, 1920):
            base_image = base_image.resize((1080, 1920), Image.Resampling.LANCZOS)

        canvas = base_image.copy()
        draw = ImageDraw.Draw(canvas, "RGBA")

        # Draw top and bottom dark gradient overlays for enhanced text contrast
        # Top gradient: (0,0) to (1080, 420)
        for y in range(400):
            alpha = int(180 * (1.0 - (y / 400.0)))
            draw.line([(0, y), (1080, y)], fill=(0, 0, 0, alpha))

        # Bottom gradient: (0, 1500) to (1080, 1920)
        for y in range(1500, 1920):
            alpha = int(190 * ((y - 1500) / 420.0))
            draw.line([(0, y), (1080, y)], fill=(0, 0, 0, alpha))

        # Select font
        font_path = "C:/Windows/Fonts/arialbd.ttf"
        font_title = None
        font_badge = None
        if os.path.exists(font_path):
            try:
                font_title = ImageFont.truetype(font_path, 60)
                font_badge = ImageFont.truetype(font_path, 32)
            except Exception:
                pass

        if not font_title:
            font_title = ImageFont.load_default()
            font_badge = ImageFont.load_default()

        # Extract punchy title
        raw_title = clip.headline.strip().upper() if clip.headline else "VIRAL MOMENT"
        # Wrap title to maximum 24 characters per line
        words = raw_title.split()
        lines = []
        cur_line = []
        cur_len = 0
        for w in words:
            if cur_len + len(w) + 1 <= 20:
                cur_line.append(w)
                cur_len += len(w) + 1
            else:
                if cur_line:
                    lines.append(" ".join(cur_line))
                cur_line = [w]
                cur_len = len(w)
        if cur_line:
            lines.append(" ".join(cur_line))

        lines = lines[:3]  # Max 3 lines

        # Draw Title Card in Top Third (y ~ 220)
        start_y = 200
        line_height = 80
        for i, line_text in enumerate(lines):
            # Compute text dimensions
            bbox = draw.textbbox((0, 0), line_text, font=font_title)
            text_w = bbox[2] - bbox[0]
            text_h = bbox[3] - bbox[1]
            x = (1080 - text_w) // 2
            y = start_y + (i * line_height)

            # Draw background pill box
            pad_x = 24
            pad_y = 12
            draw.rounded_rectangle(
                [(x - pad_x, y - pad_y), (x + text_w + pad_x, y + text_h + pad_y)],
                radius=14,
                fill=(0, 0, 0, 220),
                outline=(255, 235, 59, 230),  # Neon yellow border
                width=3,
            )

            # Draw yellow / white high contrast text
            text_color = (255, 235, 59, 255) if i == 0 else (255, 255, 255, 255)
            draw.text((x, y), line_text, font=font_title, fill=text_color)

        # Draw Duration and Virality Badge at Bottom (y ~ 1780)
        badge_text = f"VENTICUT VIRAL SHORT  |  {clip.duration:.0f}s"
        bbox_b = draw.textbbox((0, 0), badge_text, font=font_badge)
        bw = bbox_b[2] - bbox_b[0]
        bh = bbox_b[3] - bbox_b[1]
        bx = (1080 - bw) // 2
        by = 1780

        draw.rounded_rectangle(
            [(bx - 20, by - 10), (bx + bw + 20, by + bh + 10)],
            radius=12,
            fill=(15, 23, 42, 220),  # Dark navy obsidian
            outline=(56, 189, 248, 220),  # Cyan border
            width=2,
        )
        draw.text((bx, by), badge_text, font=font_badge, fill=(255, 255, 255, 255))

        return canvas

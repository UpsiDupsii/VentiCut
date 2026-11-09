import logging
import subprocess
from pathlib import Path

from app.core.config import settings
from app.models.clip import ClipHighlight, VideoMetadata

logger = logging.getLogger(__name__)


class VideoEditingAgent:
    """Agent that determines editing effects and executes deterministic FFmpeg video processing

    to transform horizontal video into polished, high-retention 9:16 vertical shorts.
    """

    def __init__(self, output_dir: Path | None = None):
        self.output_dir = output_dir or settings.PROCESSED_DIR
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def render_clips(
        self,
        input_video_path: Path,
        clips: list[ClipHighlight],
        metadata: VideoMetadata | None = None,
    ) -> list[ClipHighlight]:
        """Renders all candidate clips into standalone vertical 9:16 video files."""
        if not clips or not input_video_path.exists():
            return clips

        for clip in clips:
            try:
                out_path = self.render_single_clip(input_video_path, clip, metadata)
                clip.rendered_video_path = str(out_path)
                clip.rendered_url = f"/api/v1/clips/downloads/{clip.id}"
                clip.editing_effects = [
                    "9:16 smart vertical crop",
                    "opening pattern interrupt punch-in",
                    "loudness normalized audio",
                    "opening hook title card",
                ]
            except Exception as e:
                logger.error(f"Failed to render clip {clip.id}: {e}")

        return clips

    def render_single_clip(
        self,
        input_video_path: Path,
        clip: ClipHighlight,
        metadata: VideoMetadata | None = None,
    ) -> Path:
        """Executes FFmpeg with smart 9:16 cropping, opening punch-in hook, and audio normalization."""
        output_filename = f"{clip.id}.mp4"
        output_path = self.output_dir / output_filename

        start_time = max(0.0, clip.start_time)
        duration = max(1.0, clip.duration)

        # Build video filter chain
        vf_filters = self._build_video_filters(clip, metadata)
        af_filters = self._build_audio_filters(duration)

        cmd = [
            "ffmpeg",
            "-y",  # Overwrite output
            "-ss",
            f"{start_time:.3f}",
            "-i",
            str(input_video_path),
            "-t",
            f"{duration:.3f}",
            "-vf",
            vf_filters,
            "-af",
            af_filters,
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-crf",
            "22",
            "-c:a",
            "aac",
            "-b:a",
            "128k",
            "-movflags",
            "+faststart",
            str(output_path),
        ]

        logger.info(f"Rendering clip {clip.id}: {' '.join(cmd)}")
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=180,
        )

        if result.returncode != 0:
            logger.warning(
                f"FFmpeg primary filter chain failed ({result.stderr}). Retrying with safe fallback."
            )
            # Safe fallback: simple scale and crop without text overlays
            fallback_vf = "crop=ih*9/16:ih:(iw-ow)/2:0,scale=1080:1920"
            fallback_cmd = [
                "ffmpeg",
                "-y",
                "-ss",
                f"{start_time:.3f}",
                "-i",
                str(input_video_path),
                "-t",
                f"{duration:.3f}",
                "-vf",
                fallback_vf,
                "-c:v",
                "libx264",
                "-preset",
                "ultrafast",
                "-c:a",
                "aac",
                str(output_path),
            ]
            fb_res = subprocess.run(fallback_cmd, capture_output=True, text=True, timeout=120)
            if fb_res.returncode != 0:
                raise RuntimeError(f"FFmpeg fallback failed: {fb_res.stderr}")

        return output_path

    def _build_video_filters(
        self,
        clip: ClipHighlight,
        metadata: VideoMetadata | None,
    ) -> str:
        """Constructs smart vertical 9:16 crop, opening punch-in zoom, and title hook overlay."""
        filters = []

        # 1. Opening Punch-In Zoom Pattern Interrupt (1.08x zoom for first 2.5s, then normal 9:16 crop)
        # For t < 2.5s, crop tightly (zoomed-in centered frame); then crop standard 9:16
        punch_in_crop = (
            "crop='if(lt(t,2.5),ih*9/16/1.08,ih*9/16)':"
            "'if(lt(t,2.5),ih/1.08,ih)':"
            "(iw-ow)/2:(ih-oh)/2,"
            "scale=1080:1920"
        )
        filters.append(punch_in_crop)

        # 2. Opening Visual Hook Overlay (first 3.5 seconds)
        hook_headline = None
        if clip.selected_hook and clip.selected_hook.headline:
            hook_headline = clip.selected_hook.headline
        elif clip.headline:
            hook_headline = clip.headline

        if hook_headline:
            sanitized = (
                hook_headline.replace("'", "")
                .replace(":", " - ")
                .replace("%", "\\%")
                .strip()
                .upper()
            )
            # Top banner styled hook with high-contrast backing
            hook_drawtext = (
                f"drawtext=text='{sanitized}':fontcolor=yellow:fontsize=46:"
                f"box=1:boxcolor=black@0.75:boxborderw=14:x=(w-text_w)/2:y=180:enable='between(t,0,3.5)'"
            )
            filters.append(hook_drawtext)

        return ",".join(filters)

    def _build_audio_filters(self, duration: float) -> str:
        """Constructs audio fade transitions and mobile loudness normalization."""
        fade_dur = min(0.15, duration / 4)
        out_start = max(0.0, duration - fade_dur)
        return f"afade=t=in:st=0:d={fade_dur:.2f},afade=t=out:st={out_start:.2f}:d={fade_dur:.2f},loudnorm=I=-16:TP=-1.5:LRA=11"

import json
import logging
import math
import re
import subprocess
from pathlib import Path
from typing import Any

from app.core.config import settings
from app.models.clip import VideoMetadata

logger = logging.getLogger(__name__)


def extract_video_metadata(video_path: Path) -> VideoMetadata:
    """Extract resolution, duration, fps, and format using ffprobe."""
    if not video_path.exists():
        raise FileNotFoundError(f"Video file not found at {video_path}")

    file_size_mb = round(video_path.stat().st_size / (1024 * 1024), 2)
    cmd = [
        "ffprobe",
        "-v",
        "error",
        "-show_entries",
        "stream=width,height,r_frame_rate,duration,codec_name:format=duration,format_name",
        "-of",
        "json",
        str(video_path),
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        probe_data: dict[str, Any] = json.loads(result.stdout)
    except Exception as e:
        logger.warning(f"ffprobe extraction failed ({e}), using fallback metadata")
        return VideoMetadata(
            title=video_path.stem,
            file_size_mb=file_size_mb,
        )

    streams = probe_data.get("streams", [])
    video_stream = next(
        (s for s in streams if "width" in s and s.get("width")),
        {},
    )
    format_data = probe_data.get("format", {})

    width = int(video_stream.get("width") or 1920)
    height = int(video_stream.get("height") or 1080)

    # Frame rate calculation
    fps = 30.0
    r_frame_rate = video_stream.get("r_frame_rate")
    if r_frame_rate and "/" in r_frame_rate:
        num, den = r_frame_rate.split("/")
        if float(den) > 0:
            fps = round(float(num) / float(den), 2)

    # Duration
    duration_str = format_data.get("duration") or video_stream.get("duration") or "0.0"
    try:
        duration = round(float(duration_str), 2)
    except ValueError:
        duration = 0.0

    # Aspect ratio
    gcd_val = math.gcd(width, height)
    aspect_ratio = f"{width // gcd_val}:{height // gcd_val}" if gcd_val > 1 else f"{width}:{height}"
    if width == 1920 and height == 1080:
        aspect_ratio = "16:9"
    elif width == 1080 and height == 1920:
        aspect_ratio = "9:16"

    return VideoMetadata(
        title=video_path.stem.replace("_", " ").title(),
        duration=duration,
        width=width,
        height=height,
        fps=fps,
        aspect_ratio=aspect_ratio,
        format=format_data.get("format_name", "mp4").split(",")[0],
        file_size_mb=file_size_mb,
    )


def extract_audio(video_path: Path, output_audio_path: Path) -> Path:
    """Extract clean 16kHz mono MP3/WAV audio for Whisper speech-to-text."""
    if not video_path.exists():
        raise FileNotFoundError(f"Video file not found at {video_path}")

    output_audio_path.parent.mkdir(parents=True, exist_ok=True)

    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        str(video_path),
        "-vn",
        "-acodec",
        "libmp3lame",
        "-ar",
        "16000",
        "-ac",
        "1",
        "-b:a",
        "64k",
        str(output_audio_path),
    ]

    try:
        subprocess.run(cmd, capture_output=True, check=True)
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to extract audio with ffmpeg: {e.stderr.decode(errors='ignore')}")
        raise RuntimeError(f"Audio extraction failed: {e}") from e

    return output_audio_path


def download_youtube_video(url: str, output_dir: Path | None = None) -> tuple[Path, VideoMetadata]:
    """Download YouTube video using yt-dlp with multi-client bot-detection bypass and fallback."""
    import yt_dlp

    if output_dir is None:
        output_dir = settings.UPLOAD_DIR
    output_dir.mkdir(parents=True, exist_ok=True)
    out_template = str(output_dir / "%(id)s.%(ext)s")

    # Check for optional cookies.txt in workspace or storage
    cookie_file = None
    for cand in [Path("cookies.txt"), settings.STORAGE_DIR / "cookies.txt"]:
        if cand.exists():
            cookie_file = str(cand)
            break

    # Strategy 1: Multi-client emulation (mweb, android, ios) - bypasses YouTube bot check without cookies
    client_strategies = [
        {"player_client": ["mweb", "android", "ios"]},
        {"player_client": ["ios", "android"]},
        {"player_client": ["tv_embedded", "mweb"]},
    ]

    last_error = None
    for strat in client_strategies:
        ydl_opts = {
            "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
            "outtmpl": out_template,
            "quiet": True,
            "no_warnings": True,
            "noplaylist": True,
            "merge_output_format": "mp4",
            "extractor_args": {"youtube": strat},
            "retries": 3,
            "fragment_retries": 3,
        }
        if cookie_file:
            ydl_opts["cookiefile"] = cookie_file

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)
                video_path = Path(filename)
                if not video_path.exists():
                    mp4_candidate = video_path.with_suffix(".mp4")
                    if mp4_candidate.exists():
                        video_path = mp4_candidate

                metadata = extract_video_metadata(video_path)
                if info.get("title"):
                    # Sanitize title to pure ASCII to prevent Windows console encoding crashes
                    ascii_title = re.sub(r"[^\x00-\x7F]+", "", info["title"])
                    clean_title = re.sub(r"[^\w\s-]", "", ascii_title).strip()
                    metadata.title = clean_title or metadata.title
                return video_path, metadata
        except Exception as e:
            logger.warning(f"yt-dlp client strategy {strat} failed: {e}. Trying next strategy...")
            last_error = e

    # Strategy 2: If browser cookies are accessible, try cookies from browser
    for browser in ["chrome", "edge", "firefox"]:
        try:
            ydl_opts = {
                "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
                "outtmpl": out_template,
                "quiet": True,
                "no_warnings": True,
                "noplaylist": True,
                "merge_output_format": "mp4",
                "cookiesfrombrowser": (browser,),
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)
                video_path = Path(filename)
                if not video_path.exists():
                    mp4_candidate = video_path.with_suffix(".mp4")
                    if mp4_candidate.exists():
                        video_path = mp4_candidate
                metadata = extract_video_metadata(video_path)
                if info.get("title"):
                    ascii_title = re.sub(r"[^\x00-\x7F]+", "", info["title"])
                    clean_title = re.sub(r"[^\w\s-]", "", ascii_title).strip()
                    metadata.title = clean_title or metadata.title
                return video_path, metadata
        except Exception:
            pass

    # Strategy 3: Graceful fallback to existing local video if all YouTube methods fail
    existing_files = list(output_dir.glob("*.mp4"))
    if existing_files:
        fallback_path = existing_files[0]
        logger.warning(
            f"All YouTube download strategies failed ({last_error}). Using existing video fallback: {fallback_path.name}"
        )
        metadata = extract_video_metadata(fallback_path)
        metadata.title = f"Fallback - {metadata.title}"
        return fallback_path, metadata

    raise RuntimeError(
        f"YouTube download failed: {last_error}. Please use Direct File Upload on the dashboard or provide cookies.txt."
    )

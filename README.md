<p align="center">
  <img src="assets/logo.png" alt="VentiCut Logo" width="180" />
</p>

<h1 align="center">VentiCut</h1>

<p align="center">
  <strong>Autonomous AI Video Repurposing Pipeline</strong>
</p>

<p align="center">
  Transform long-form videos (podcasts, interviews, streams, YouTube videos) into engaging, viral short-form clips (TikTok, Instagram Reels, YouTube Shorts) powered by a multi-agent AI system and deterministic media tools.
</p>

---

## Architecture Overview

VentiCut separates decision-making from execution:
- **LLMs make editorial and analytical decisions** (detecting timestamps, identifying viral moments, generating visual hooks, assessing retention).
- **Deterministic tools execute media transformations** (yt-dlp downloads videos, FFmpeg extracts 16kHz audio, crops 9:16 vertical frames, applies punch-in effects, generates ASS animated subtitles, and renders final MP4 shorts).

```
Long-Form Video (YouTube URL or File Upload)
                     │
                     ▼
       ┌───────────────────────────┐
       │   Ingestion & FFprobe     │ ──> Video Metadata (codec, fps, bitrate)
       └───────────────────────────┘
                     │
                     ▼
       ┌───────────────────────────┐
       │   FFmpeg Audio Extractor  │ ──> 16kHz Mono Audio Stream
       └───────────────────────────┘
                     │
                     ▼
       ┌───────────────────────────┐
       │  Agent 1: Transcription   │ ──> Word-level Timestamps (Groq Whisper)
       └───────────────────────────┘
                     │
                     ▼
       ┌───────────────────────────┐
       │ Agent 2: Understanding    │ ──> Narrative Arc, Tone, Topics (Gemini)
       └───────────────────────────┘
                     │
                     ▼
       ┌───────────────────────────┐
       │ Agent 3: Clip Finder      │ ──> 15-60s Viral Moments & Scoring (Groq)
       └───────────────────────────┘
                     │
                     ▼
       ┌───────────────────────────┐
       │ Agent 4: Hook Generator   │ ──> 4 Hook Archetypes & Visual Styles
       └───────────────────────────┘
                     │
                     ▼
       ┌───────────────────────────┐
       │ Agent 5: Video Editing    │ ──> 9:16 Smart Crop, Punch-in Zoom, Audio Normalization
       └───────────────────────────┘
                     │
                     ▼
        ┌───────────────────────────┐
        │ Agent 6: Caption Agent    │ ──> 5 Synchronized ASS Caption Styles & Burn
        └───────────────────────────┘
                      │
                      ▼
        ┌───────────────────────────┐
        │ Agent 7: Quality Review   │ ──> Audio, Pacing, Contrast & Brand Safety Audit
        └───────────────────────────┘
                      │
                      ▼
        ┌───────────────────────────┐
        │ Agent 8: Social Metadata  │ ──> Multi-Platform SEO (Shorts, TikTok, Reels)
        └───────────────────────────┘
                      │
                      ▼
        ┌───────────────────────────┐
        │ Agent 9: Thumbnail Agent  │ ──> 9:16 Vertical Cover Frames & Typography
        └───────────────────────────┘
```

---

## Active AI Agents and Capabilities

### 1. Ingestion and Media Tools (`app/services/media_tools.py`)
- Downloads YouTube videos cleanly via `yt-dlp` with built-in multi-client bot-detection bypass (`mweb`, `android`, `ios`) and browser cookie fallback.
- Supports direct file uploads (MP4, MOV, MKV, WebM) with drag-and-drop.
- Extracts comprehensive stream properties with `ffprobe` (dimensions, fps, duration, codecs).
- Extracts clean 16kHz mono MP3 tracks with `ffmpeg` for optimal speech-to-text accuracy.

### 2. Transcription Agent (`app/services/transcription_agent.py`)
- Transcribes audio into timestamped segments and individual word boundaries.
- Powered by Groq Cloud (`whisper-large-v3-turbo` and `whisper-large-v3`).
- Includes algorithmic fallback simulation for offline execution.

### 3. Video Understanding Agent (`app/services/understanding_agent.py`)
- Analyzes transcript context, overarching narrative arc, pacing, and tone.
- Extracts primary themes, speaker insights, and high-impact quotable takeaways.
- Powered by Google Gemini (`gemini-2.5-flash`) via Google AI Studio.

### 4. Viral Clip Finder Agent (`app/services/clip_finder_agent.py`)
- Analyzes transcript cadence, emotional peaks, and viral triggers.
- Identifies optimal self-contained segments between 15 and 60 seconds.
- Computes dynamic Virality Index, Hook Score, and Retention Potential metrics.
- Crafts tailored, segment-specific headlines from spoken dialogue without repetitive cliches.
- Powered by Groq LLM (`openai/gpt-oss-120b` and `qwen/qwen3.8-27b`).

### 5. Hook Generator Agent (`app/services/hook_generator_agent.py`)
- Evaluates the opening 3-5 seconds of each candidate clip to maximize viewer retention.
- Crafts 4 distinct viral hook variations per clip across proven copywriting archetypes and visual presentations:
  - **Curiosity Gap** with `top_neon_pill`: Poses an irresistible mystery or unspoken pattern.
  - **Contrarian** with `center_punch_title`: Challenges mainstream belief right during the opening zoom punch-in.
  - **Problem-Agitation** with `lower_third_bar`: Pinpoints a frustrating mistake and promises immediate relief.
  - **Direct Value** with `floating_frosted_card`: Delivers an actionable secret, hack, or framework.
- Generates dynamic, context-specific hook headlines tailored to the speaker's exact insight (eliminating repetitive cliches).
- Automatically generates deterministic FFmpeg overlay parameters for on-screen titles.

### 6. Video Editing Agent (`app/services/video_editing_agent.py`)
- Deterministically crops horizontal 16:9 video to vertical 9:16 format (1080x1920) optimized for TikTok, Instagram Reels, and YouTube Shorts.
- Applies an opening **pattern interrupt punch-in zoom effect** (1.08x zoom for the first 2.5 seconds) to visually grab viewer attention and prevent swiping.
- Burns high-contrast visual title cards and hook banners into the opening 3.5 seconds.
- Applies mobile loudness normalization (`loudnorm=I=-16:TP=-1.5:LRA=11`) and smooth audio fade transitions to eliminate audio clicks on cut boundaries.
- Renders standalone vertical MP4 files saved to `storage/processed/{clip_id}.mp4` accessible via streaming API.

### 7. Caption Agent (`app/services/caption_agent.py`)
- Generates frame-accurate Advanced SubStation Alpha (ASS v4.00+) subtitle documents mapped to Whisper word-level timestamps.
- Burns animated subtitles directly into 9:16 vertical clips using FFmpeg's `libass` subtitle engine.
- Supports 5 distinct creative caption styles tailored to diverse content formats:
  - **Alex Hormozi Glow (`hormozi_glow`)**: High-contrast white typography where the spoken active word pops in electric neon lime (`#00FF66`). Fast 2-3 word cadence.
  - **MrBeast Viral Yellow (`mrbeast_yellow`)**: Giant bold yellow impact text (`#FFE81F`) with thick 4.5px black outline and radiant white active flash.
  - **Karaoke Wave Fill (`karaoke_fill`)**: Syllable-by-syllable smooth progressive color wipe from silver to vibrant coral amber (`#FF5511`).
  - **TikTok Frosted Pill (`tiktok_badge`)**: Clean modern sans enclosed in a floating obsidian translucent badge with electric magenta highlights.
  - **Minimalist Clean (`minimal_clean`)**: Elegant frosted lower-third subtitles with subtle dark backing, ideal for documentary and luxury podcast clips.
- Provides interactive on-the-fly clip re-rendering (`POST /api/v1/clips/jobs/{job_id}/clips/{clip_id}/rerender`) to allow switching caption and hook styles with instant browser previews.

### 8. Quality Review and Safety Agent (`app/services/quality_review_agent.py`)
- Performs comprehensive automated quality assurance audits before clips are published:
  - **Platform Duration Compliance**: Ensures clips fit optimal watch-time windows (15s to 60s).
  - **Audio Loudness & Dynamics**: Verifies EBU R128 loudness normalization and crossfade integrity.
  - **Subtitle Cadence & Speech Pacing**: Calculates words-per-second to ensure dialogue readability.
  - **Brand Safety & Content Moderation**: Scans transcripts via Groq LLM for hate speech, harassment, or policy violations.
- Computes an overall **Publish Readiness Score** (0-100) with pass/warning/fail status flags and actionable engagement recommendations.

### 9. Social Metadata and SEO Agent (`app/services/social_metadata_agent.py`)
- Crafts distribution packages optimized for algorithmic discovery across three platforms:
  - **YouTube Shorts**: High-CTR titles (under 60 characters), search-optimized descriptions, and pinned discussion questions.
  - **TikTok**: Conversational hook captions, trending hashtag sets (`#fyp`, `#foryou`, niche tags), and engagement-boosting pinned comments.
  - **Instagram Reels**: Storytelling captions formatted with paragraph breaks, 10-12 categorized hashtags, and save-incentivizing CTAs.
- Features one-click clipboard copying for post copy, hashtag sets, and pinned comments directly in the interface.

### 10. Thumbnail and Cover Frame Selector Agent (`app/services/thumbnail_agent.py`)
- Automatically selects the visual climax of the vertical video clip by sampling and scoring candidate frames for contrast, illumination, and sharpness.
- Renders high-contrast 1080x1920 vertical cover thumbnail images with custom title pills and subtle top/bottom vignettes.
- Saves cover frames to `storage/processed/{clip_id}_thumb.jpg` and exposes streaming download endpoints (`GET /api/v1/clips/downloads/{clip_id}/thumbnail`).

---

## Frontend Architecture

The user interface is built with React 19 and Vite, following a strict modular architecture where every major view is isolated into its own `.jsx` component file for maintainability:

```
frontend/src/
├── components/
│   ├── Navbar.jsx            # Brand header, navigation links, and Admin Center trigger
│   ├── VideoIngestion.jsx    # Dual-input card for YouTube URLs and file uploads with caption selector
│   ├── ExecutionMonitor.jsx  # Multi-stage pipeline progress stepper (Steps 1 to 7)
│   ├── ViralClipsTab.jsx     # Detected clips, 5 caption styles, 4 hook options, video player, and re-rendering
│   ├── UnderstandingTab.jsx  # Narrative arc, pacing, tone, and extracted topics
│   ├── TranscriptTab.jsx     # Searchable dialogue stream with timestamps
│   ├── MetadataTab.jsx       # FFprobe technical stream diagnostics
│   ├── LogsTab.jsx           # Terminal log viewer with real-time events
│   └── AdminModal.jsx        # Telemetry dashboard for API tokens and storage
├── services/
│   └── api.js                # Centralized REST API client
├── App.jsx                   # Central state container and tabbed workspace
└── index.css                 # Enterprise design system styled after assets/logo.png
```

Production assets compile directly to `app/static/dist/`, which is mounted and served natively by the FastAPI application at `GET /` and `/app-assets`.

---

## Admin & Telemetry Dashboard

VentiCut includes an administrative telemetry console to monitor usage across free-tier APIs and disk storage.

- **Admin Login**:
  - Default Username: `admin` (or `admin@email.com`)
  - Default Password: `1234`
- **Tracked Free-Tier Metrics**:
  - **Groq LLM Tokens**: Live consumption against the 500,000 daily free token quota.
  - **Groq Whisper Minutes**: Live audio minutes against the 2,000 daily free minute quota.
  - **Google Gemini Requests**: Live request counter against the 1,500 daily free request limit.
  - **Storage Allocation**: Live megabyte tracking across `uploads/`, `temp/`, and `processed/`.
  - **Webhook Callbacks**: Dispatched callback counts and delivery success rates.

---

## Installation & Setup

### 1. Prerequisites
- Python 3.10+ (Tested on Python 3.14)
- Node.js 18+ and npm (for frontend building)
- FFmpeg installed and accessible in your system `PATH` (must include `libass` support)

### 2. Clone and Setup Environment

```bash
# Clone repository
git clone git@github.com:UpsiDupsii/VentiCut.git
cd VentiCut

# Activate virtual environment
# Windows (PowerShell):
.\.venv\Scripts\Activate.ps1
# macOS/Linux:
source .venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt
```

### 3. Configure API Keys

Copy the sample environment file:
```bash
cp .env.example .env
```

Edit `.env` and provide your free API keys:
```env
# Google Gemini API Key (Free tier from Google AI Studio: https://aistudio.google.com)
GEMINI_API_KEY=AIzaSy...

# Groq API Key (Free tier from Groq Console: https://console.groq.com)
GROQ_API_KEY=gsk_...
GROQ_LLM_MODEL=openai/gpt-oss-120b

# Admin Authentication
ADMIN_USERNAME=admin
ADMIN_EMAIL=admin@email.com
ADMIN_PASSWORD=1234
SECRET_KEY=venticut-jwt-secret-key-replace-in-production
```

### 4. Build Frontend

```bash
cd frontend
npm install
npm run build
cd ..
```

---

## Running the Application

Start the FastAPI application with Uvicorn:

```bash
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

- **Web Dashboard**: Open [http://127.0.0.1:8000](http://127.0.0.1:8000)
- **Interactive Swagger Docs**: Open [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **OpenAPI Schema**: [http://127.0.0.1:8000/api/v1/openapi.json](http://127.0.0.1:8000/api/v1/openapi.json)

---

## API Usage Examples

### 1. Submit a YouTube Video for Repurposing with Selected Caption Style

```bash
curl -X POST "http://127.0.0.1:8000/api/v1/clips/jobs" \
  -H "Content-Type: application/json" \
  -d '{
    "video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    "target_aspect_ratio": "9:16",
    "caption_style": "hormozi_glow",
    "webhook_url": "https://your-domain.com/webhook"
  }'
```

### 2. List Available Caption Styles

```bash
curl -X GET "http://127.0.0.1:8000/api/v1/clips/caption-styles"
```

### 3. Re-render an Existing Clip with a Different Caption Style or Hook

```bash
curl -X POST "http://127.0.0.1:8000/api/v1/clips/jobs/{job_id}/clips/{clip_id}/rerender" \
  -H "Content-Type: application/json" \
  -d '{
    "caption_style": "mrbeast_yellow",
    "hook_style": "center_punch_title"
  }'
```

### 4. Stream or Download Rendered Clip MP4

```bash
curl -O -J "http://127.0.0.1:8000/api/v1/clips/downloads/{clip_id}"
```

---

## Running Tests

Execute the full automated test suite:

```bash
pytest -v
```

Run code formatting and linting:

```bash
ruff check .
ruff format --check .
```

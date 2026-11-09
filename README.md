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
- **Deterministic tools execute media transformations** (yt-dlp downloads videos, FFmpeg extracts 16kHz audio and crops 9:16 vertical frames, Whisper transcribes).

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
       │ Agent 4: Hook Generator   │ ──> 4 Hook Archetypes & FFmpeg Overlays
       └───────────────────────────┘
                     │
                     ▼
          [Upcoming Agent Pipeline]
   ┌───────────────────────────────────┐
   │ Agent 5: Video Editing (Cropping) │
   │ Agent 6: Caption Subtitles        │
   │ Agent 7: Quality Review Agent     │
   └───────────────────────────────────┘
```

---

## Active AI Agents and Capabilities

### 1. Ingestion and Media Tools (`app/services/media_tools.py`)
- Downloads YouTube videos cleanly via `yt-dlp`.
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
- Powered by Groq LLM (`openai/gpt-oss-120b`).

### 5. Hook Generator Agent (`app/services/hook_generator_agent.py`)
- Evaluates the opening 3-5 seconds of each candidate clip to maximize viewer retention.
- Crafts 4 distinct viral hook variations per clip across proven copywriting archetypes:
  - **Curiosity Gap**: Poses an irresistible mystery or cliffhanger.
  - **Contrarian**: Challenges mainstream belief or conventional wisdom.
  - **Problem-Agitation**: Pinpoints a frustrating mistake and promises immediate relief.
  - **Direct Value**: Delivers an actionable secret, hack, or formula.
- Automatically generates deterministic FFmpeg `drawtext` overlay parameters (e.g. `drawtext=text='...':fontcolor=yellow:fontsize=48:x=(w-text_w)/2:y=180:enable='between(t,0,3.5)'`).

---

## Frontend Architecture

The user interface is built with React 19 and Vite, following a strict modular architecture where every major view is isolated into its own `.jsx` component file for maintainability:

```
frontend/src/
├── components/
│   ├── Navbar.jsx            # Brand header, navigation links, and Admin Center trigger
│   ├── VideoIngestion.jsx    # Dual-input card for YouTube URLs and file uploads
│   ├── ExecutionMonitor.jsx  # Multi-stage pipeline progress stepper (Steps 1 to 5)
│   ├── ViralClipsTab.jsx     # Detected viral clips and 4-option Hook Generator grid
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
- FFmpeg installed and accessible in your system `PATH`

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

### 4. Build the Frontend (Optional for Python Devs)

The compiled distribution is committed under `app/static/dist/`. To rebuild after making React component edits:
```bash
cd frontend
npm install
npm run build
cd ..
```

### 5. Launch the Application

```bash
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Once running:
- **Web Interface**: http://127.0.0.1:8000
- **Interactive API Docs (Swagger)**: http://127.0.0.1:8000/docs
- **Health Check**: http://127.0.0.1:8000/api/v1/health

---

## How to Use VentiCut

### 1. Repurpose a YouTube Video
1. Open http://127.0.0.1:8000 in your browser.
2. In the **Ingest Video** section, select **YouTube URL**.
3. Paste a YouTube link (e.g. `https://www.youtube.com/watch?v=...` or `https://youtu.be/...`).
4. (Optional) Provide a Webhook URL to receive automated JSON event dispatches.
5. Click **Process Video**.

### 2. Upload a Local Video File
1. Click the **Upload Video File** tab.
2. Drag and drop any raw MP4, MOV, MKV, or WebM video file (up to 500 MB).
3. Click **Process Video**.

### 3. Monitor Real-Time Multi-Agent Execution
Observe the execution monitor as the pipeline progresses through:
- **Step 1: Ingestion & Audio**: Downloads video and strips 16kHz audio.
- **Step 2: Transcription Agent**: Generates word-level timestamps via Groq Whisper.
- **Step 3: Understanding Agent**: Generates narrative arc and topic comprehension via Gemini.
- **Step 4: Viral Clip Finder**: Identifies 15-60s candidate segments with virality scores via Groq.
- **Step 5: Hook Generator Agent**: Crafts 4 viral hook variations and FFmpeg overlay filters.

### 4. Inspect Results
- **Viral Clips Tab**: Browse detected highlights, inspect virality/retention scores, and view 4 tailored hook options (`Curiosity Gap`, `Contrarian`, `Problem-Agitation`, `Direct Value`).
- **Understanding Tab**: Review the Gemini executive briefing, narrative tone, pacing, and extracted themes.
- **Transcript Tab**: Search dialogues in real time with word timestamps.
- **Metadata Tab**: Review technical video stream specs (bitrate, fps, codec, resolution).
- **Logs Tab**: View raw execution events and terminal messages.

### 5. Admin & Quota Management
1. Click **Admin Panel** in the top navigation bar.
2. Sign in with username `admin` and password `1234`.
3. Review your remaining daily free-tier quotas for Groq tokens, Whisper minutes, and Gemini requests.

---

## REST API Reference

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/` | Serves the modular React web application |
| `GET` | `/api/v1/health` | System health and service availability check |
| `POST` | `/api/v1/clips/jobs` | Submit a YouTube video URL for background processing |
| `POST` | `/api/v1/clips/upload` | Upload a video file for background processing |
| `GET` | `/api/v1/clips/jobs/{id}` | Poll execution status, progress, and generated clips |
| `POST` | `/api/v1/admin/login` | Authenticate administrator and receive JWT token |
| `GET` | `/api/v1/admin/stats` | Retrieve live token usage and storage telemetry |

---

## Testing & Quality Assurance

VentiCut enforces strict code formatting and testing standards.

```bash
# Run Ruff lint check
ruff check .

# Run Ruff formatting check
ruff format --check .

# Auto-format all Python files
ruff format .

# Run Pytest suite
pytest
```

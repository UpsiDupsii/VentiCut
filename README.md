# VentiCut 🎬⚡

**VentiCut** is an AI-powered pipeline designed to convert long-form videos (podcasts, interviews, streams, YouTube videos) into engaging, viral short-form clips (TikTok, Instagram Reels, YouTube Shorts).

---

## 🚀 Key Planned Features

1. **Audio Extraction & Transcription**: High-accuracy speech-to-text with word-level timestamps using Whisper.
2. **AI Highlight & Virality Detection**: Analyzes transcript sentiment, hook strength, energy peaks, and topic shifts to extract optimal 15-60s moments.
3. **Smart Cropping (16:9 ➔ 9:16)**: Active speaker detection and face-tracking to keep speakers framed vertically.
4. **Dynamic Subtitles**: Auto-generated animated captions with word-level pop highlights (OpusClip / CapCut style).
5. **FastAPI Backend**: Asynchronous job queue, media uploads, and REST API for pipeline management.

---

## 🛠️ Project Structure

```
VentiCut/
├── app/
│   ├── api/
│   │   └── v1/
│   │       ├── endpoints/
│   │       │   ├── health.py        # Service health check
│   │       │   └── clips.py         # Clip job submissions & status
│   │       └── router.py            # Central v1 route registry
│   ├── core/
│   │   └── config.py                # Environment & application settings
│   ├── models/
│   │   └── clip.py                  # Pydantic schemas and models
│   ├── services/                    # Pipeline stages (transcription, cropping, subtitles)
│   └── main.py                      # FastAPI application entrypoint
├── storage/                         # Local storage for uploads, temp, & outputs
│   ├── uploads/
│   ├── temp/
│   └── processed/
├── tests/                           # Pytest test suite
├── .env.example                     # Sample environment variables
├── .gitignore                       # Git ignore rules for media & venv
├── requirements.txt                 # Project dependencies
└── README.md
```

---

## ⚡ Getting Started

### 1. Prerequisites
- Python 3.10+ (Tested on Python 3.14)
- FFmpeg (for video rendering & audio processing)

### 2. Setup Virtual Environment

```bash
# Clone the repository
git clone git@github.com:UpsiDupsii/VentiCut.git
cd VentiCut

# Activate the virtual environment
# On Windows (PowerShell):
.\.venv\Scripts\Activate.ps1
# On macOS/Linux:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Environment Variables

Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

### 4. Run the API Server

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Once started:
- **Interactive Swagger Docs**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **ReDoc**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)
- **Health Check**: [http://127.0.0.1:8000/api/v1/health](http://127.0.0.1:8000/api/v1/health)

### 5. Run Tests

```bash
pytest
```

from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app
from app.models.clip import TranscriptionResult, VideoMetadata
from app.services.transcription_agent import TranscriptionAgent
from app.services.understanding_agent import VideoUnderstandingAgent

client = TestClient(app)


def test_root_endpoint_serves_ui():
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers.get("content-type", "")
    assert "VentiCut" in response.text


def test_api_root_endpoint():
    response = client.get("/api")
    assert response.status_code == 200
    data = response.json()
    assert "VentiCut" in data["message"]


def test_health_endpoint():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["app"] == "VentiCut"


def test_create_and_get_job():
    create_resp = client.post(
        "/api/v1/clips/jobs",
        json={"video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"},
    )
    assert create_resp.status_code == 202
    job = create_resp.json()
    job_id = job["job_id"]
    assert job["status"] in ["pending", "downloading"]

    get_resp = client.get(f"/api/v1/clips/jobs/{job_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["job_id"] == job_id


def test_upload_job():
    file_content = b"fake video bytes for testing"
    files = {"file": ("test_sample.mp4", file_content, "video/mp4")}
    resp = client.post("/api/v1/clips/upload", files=files)
    assert resp.status_code == 202
    data = resp.json()
    assert data["video_filename"] == "test_sample.mp4"


def test_transcription_agent_fallback(tmp_path: Path):
    dummy_audio = tmp_path / "dummy.mp3"
    dummy_audio.write_bytes(b"dummy audio content")

    agent = TranscriptionAgent(api_key=None)
    result = agent.transcribe(dummy_audio)
    assert isinstance(result, TranscriptionResult)
    assert len(result.segments) > 0
    assert result.duration > 0


def test_video_understanding_agent_fallback():
    agent = VideoUnderstandingAgent(api_key=None)
    transcript = TranscriptionResult(
        language="en",
        duration=30.0,
        full_text="This is a test transcript for VentiCut pipeline.",
        segments=[],
    )
    metadata = VideoMetadata(title="Test Video", duration=30.0)
    understanding = agent.analyze(transcript, metadata)
    assert understanding.summary != ""
    assert len(understanding.topics) > 0
    assert len(understanding.potential_hooks) > 0

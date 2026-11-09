from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models.clip import TranscriptionResult, TranscriptionSegment, VideoMetadata
from app.services.clip_finder_agent import ViralClipFinderAgent
from app.services.token_tracker import token_tracker
from app.services.transcription_agent import TranscriptionAgent
from app.services.understanding_agent import VideoUnderstandingAgent
from app.services.webhook import dispatch_webhook

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
        json={
            "video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "webhook_url": "https://example.com/webhook",
        },
    )
    assert create_resp.status_code == 202
    job = create_resp.json()
    job_id = job["job_id"]
    assert job["status"] in ["pending", "downloading"]
    assert job["webhook_url"] == "https://example.com/webhook"

    get_resp = client.get(f"/api/v1/clips/jobs/{job_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["job_id"] == job_id


def test_upload_job():
    file_content = b"fake video bytes for testing"
    files = {"file": ("test_sample.mp4", file_content, "video/mp4")}
    resp = client.post(
        "/api/v1/clips/upload",
        files=files,
        data={"webhook_url": "https://example.com/webhook"},
    )
    assert resp.status_code == 202
    data = resp.json()
    assert data["video_filename"] == "test_sample.mp4"
    assert data["webhook_url"] == "https://example.com/webhook"


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


def test_viral_clip_finder_agent():
    agent = ViralClipFinderAgent(api_key=None)
    segments = [
        TranscriptionSegment(
            id=1,
            start=0.0,
            end=10.0,
            text="Why do 99 percent of creators fail when starting out?",
        ),
        TranscriptionSegment(
            id=2,
            start=10.0,
            end=22.0,
            text="The secret is they focus entirely on views instead of retention.",
        ),
        TranscriptionSegment(
            id=3,
            start=22.0,
            end=35.0,
            text="If you master the opening three seconds, everything changes permanently.",
        ),
    ]
    transcript = TranscriptionResult(
        language="en",
        duration=35.0,
        full_text="Why do 99 percent of creators fail when starting out? The secret is they focus entirely on views instead of retention. If you master the opening three seconds, everything changes permanently.",
        segments=segments,
    )

    clips = agent.find_viral_clips(
        transcript=transcript,
        min_duration=15,
        max_duration=40,
    )

    assert len(clips) > 0
    first_clip = clips[0]
    assert first_clip.start_time >= 0.0
    assert first_clip.end_time > first_clip.start_time
    assert first_clip.virality_score > 50.0
    assert first_clip.headline != ""
    assert first_clip.hook_text != ""


@pytest.mark.anyio
async def test_webhook_dispatcher():
    # Without URL, returns False safely
    res_none = await dispatch_webhook(None, "test_event", "job1", "pending", 10, "msg")
    assert res_none is False

    # Mocked client delivering webhook
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value.status_code = 200
        delivered = await dispatch_webhook(
            "https://fake-endpoint.com/webhook",
            "job_completed",
            "job_123",
            "completed",
            100,
            "Success",
            {"test": True},
        )
        assert delivered is True


def test_admin_auth_success():
    # Test with email
    resp_email = client.post(
        "/api/v1/admin/login",
        json={"username_or_email": "admin@email.com", "password": "1234"},
    )
    assert resp_email.status_code == 200
    data_email = resp_email.json()
    assert "access_token" in data_email
    token = data_email["access_token"]

    # Test with username
    resp_user = client.post(
        "/api/v1/admin/login",
        json={"username_or_email": "admin", "password": "1234"},
    )
    assert resp_user.status_code == 200

    # Test authenticated endpoint
    stats_resp = client.get(
        "/api/v1/admin/stats",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert stats_resp.status_code == 200
    stats = stats_resp.json()
    assert "api_usage" in stats
    assert "groq" in stats["api_usage"]
    assert "gemini" in stats["api_usage"]


def test_admin_auth_invalid():
    # Wrong password
    resp = client.post(
        "/api/v1/admin/login",
        json={"username_or_email": "admin@email.com", "password": "wrongpassword"},
    )
    assert resp.status_code == 401

    # Unauthorized access to stats
    unauth_resp = client.get("/api/v1/admin/stats")
    assert unauth_resp.status_code == 401


def test_token_tracker_calculations():
    token_tracker.record_groq_whisper(duration_seconds=120.0)
    token_tracker.record_groq_llm(prompt_tokens=100, completion_tokens=50)
    token_tracker.record_gemini_call(estimated_tokens=250)
    token_tracker.record_webhook(success=True)

    summary = token_tracker.get_summary()
    assert summary["groq"]["whisper_calls"] >= 1
    assert summary["groq"]["total_tokens_used"] >= 150
    assert summary["gemini"]["requests_used"] >= 1
    assert summary["webhooks"]["total_dispatched"] >= 1

from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.main import app
from app.models.clip import (
    ClipHighlight,
    HookVariant,
    TranscriptionResult,
    TranscriptionSegment,
    VideoMetadata,
)
from app.services.clip_finder_agent import ViralClipFinderAgent
from app.services.hook_generator_agent import HookGeneratorAgent
from app.services.token_tracker import token_tracker
from app.services.transcription_agent import TranscriptionAgent
from app.services.understanding_agent import VideoUnderstandingAgent
from app.services.video_editing_agent import VideoEditingAgent
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
    with patch("app.api.v1.endpoints.clips.run_pipeline_for_job"):
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
    with patch("app.api.v1.endpoints.clips.run_pipeline_for_job"):
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


def test_hook_generator_agent_fallback():
    agent = HookGeneratorAgent(api_key=None)
    clip = ClipHighlight(
        id="test-clip-1",
        start_time=0.0,
        end_time=30.0,
        duration=30.0,
        headline="ALGORITHM SECRETS REVEALED",
        hook_text="Why do 99 percent of creators fail when starting out?",
        virality_score=92.0,
        hook_score=85.0,
        retention_score=88.0,
        reasoning="Strong opening curiosity gap",
    )

    processed_clips = agent.generate_hooks_for_clips([clip])
    assert len(processed_clips) == 1
    p_clip = processed_clips[0]

    # Check 4 distinct hook variants are generated
    assert len(p_clip.hooks) == 4
    types = {h.hook_type for h in p_clip.hooks}
    assert "Curiosity Gap" in types
    assert "Contrarian" in types
    assert "Problem-Agitation" in types
    assert "Direct Value" in types

    # Check selected hook
    assert p_clip.selected_hook is not None
    assert p_clip.selected_hook.hook_score >= 85.0
    assert "drawtext=" in p_clip.selected_hook.ffmpeg_drawtext


def test_hook_generator_drawtext_formatting():
    agent = HookGeneratorAgent(api_key=None)
    filter_banner = agent._build_ffmpeg_drawtext("STOP DOING THIS", "top_banner_yellow")
    assert "drawtext=text='STOP DOING THIS'" in filter_banner
    assert "fontsize=" in filter_banner
    assert "enable='between(t,0,3.5)'" in filter_banner

    filter_center = agent._build_ffmpeg_drawtext("SECRET FORMULA", "center_glow_white")
    assert "drawtext=text='SECRET FORMULA'" in filter_center
    assert "boxcolor=black@0.85" in filter_center


def test_video_editing_agent_filters():
    agent = VideoEditingAgent()
    hook = HookVariant(
        id="h1",
        headline="STOP WASTING TIME",
        spoken_hook="Stop wasting time on low retention edits",
        hook_type="Contrarian",
        hook_score=94.0,
        visual_style="top_banner_yellow",
    )
    clip = ClipHighlight(
        id="clip_test_render",
        start_time=10.0,
        end_time=35.0,
        duration=25.0,
        headline="TEST HEADLINE",
        virality_score=90.0,
        selected_hook=hook,
    )
    vf = agent._build_video_filters(clip, metadata=None)
    assert "scale=1080:1920" in vf
    assert "if(lt(t,2.5)" in vf
    assert "drawtext=text='STOP WASTING TIME'" in vf


def test_video_editing_agent_audio_filters():
    agent = VideoEditingAgent()
    af = agent._build_audio_filters(duration=30.0)
    assert "afade=t=in:st=0:d=" in af
    assert "afade=t=out:st=29." in af
    assert "loudnorm=I=-16" in af


def test_download_clip_endpoint(tmp_path: Path):
    settings.PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    test_clip_id = "test_download_clip_id"
    test_file = settings.PROCESSED_DIR / f"{test_clip_id}.mp4"
    test_file.write_bytes(b"fake mp4 video bytes for testing")

    try:
        # Success response
        resp = client.get(f"/api/v1/clips/downloads/{test_clip_id}")
        assert resp.status_code == 200
        assert "video/mp4" in resp.headers.get("content-type", "")

        # 404 response for nonexistent file
        missing_resp = client.get("/api/v1/clips/downloads/non_existent_clip_xyz")
        assert missing_resp.status_code == 404
    finally:
        if test_file.exists():
            test_file.unlink()


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

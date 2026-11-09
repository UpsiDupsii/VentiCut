from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

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
    WordTimestamp,
)
from app.services.caption_agent import CaptionAgent
from app.services.clip_finder_agent import ViralClipFinderAgent
from app.services.coordinator import ACTIVE_JOBS, create_new_job
from app.services.hook_generator_agent import HookGeneratorAgent
from app.services.quality_review_agent import QualityReviewAgent
from app.services.social_metadata_agent import SocialMetadataAgent
from app.services.thumbnail_agent import ThumbnailAgent
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
    with patch("app.api.v1.endpoints.clips.run_pipeline_for_job", new_callable=AsyncMock):
        request_payload = {
            "video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "target_aspect_ratio": "9:16",
            "max_duration_seconds": 60,
            "min_duration_seconds": 15,
            "caption_style": "hormozi_glow",
        }
        create_resp = client.post("/api/v1/clips/jobs", json=request_payload)
        assert create_resp.status_code == 202
        data = create_resp.json()
        assert "job_id" in data
        assert data["status"] == "pending"
        assert data["video_url"] == request_payload["video_url"]

        job_id = data["job_id"]
        get_resp = client.get(f"/api/v1/clips/jobs/{job_id}")
        assert get_resp.status_code == 200
        get_data = get_resp.json()
        assert get_data["job_id"] == job_id
        assert get_data["status"] == "pending"


def test_upload_job(tmp_path: Path):
    with patch("app.api.v1.endpoints.clips.run_pipeline_for_job", new_callable=AsyncMock):
        test_video = tmp_path / "test_sample.mp4"
        test_video.write_bytes(b"dummy video content for unit testing")

        with test_video.open("rb") as f:
            upload_resp = client.post(
                "/api/v1/clips/upload",
                files={"file": ("test_sample.mp4", f, "video/mp4")},
                data={
                    "target_aspect_ratio": "9:16",
                    "min_duration_seconds": 15,
                    "max_duration_seconds": 60,
                    "caption_style": "mrbeast_yellow",
                },
            )
        assert upload_resp.status_code == 202
        data = upload_resp.json()
        assert "job_id" in data
        assert data["video_filename"] == "test_sample.mp4"


def test_transcription_agent_fallback(tmp_path: Path):
    agent = TranscriptionAgent(api_key=None)
    fake_audio = tmp_path / "fake_audio.mp3"
    fake_audio.write_bytes(b"dummy audio content")

    result = agent.transcribe(fake_audio)
    assert result.duration > 0
    assert result.full_text != ""
    assert len(result.segments) > 0


def test_video_understanding_agent_fallback():
    agent = VideoUnderstandingAgent(api_key=None)
    agent.client = None
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
    agent.client = None
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

    # Test top neon pill
    filter_pill = agent._build_ffmpeg_drawtext("WHY NOBODY TALKS", "top_neon_pill")
    assert "drawtext=text='WHY NOBODY TALKS'" in filter_pill
    assert "fontsize=48" in filter_pill
    assert "enable='between(t,0,3.5)'" in filter_pill

    # Test center punch title
    filter_center = agent._build_ffmpeg_drawtext("STOP DOING THIS", "center_punch_title")
    assert "drawtext=text='STOP DOING THIS'" in filter_center
    assert "fontsize=54" in filter_center
    assert "enable='between(t,0,2.5)'" in filter_center

    # Test lower third bar
    filter_bar = agent._build_ffmpeg_drawtext("BIGGEST MISTAKE", "lower_third_bar")
    assert "drawtext=text='BIGGEST MISTAKE'" in filter_bar
    assert "y=h-380" in filter_bar

    # Test floating frosted card
    filter_card = agent._build_ffmpeg_drawtext("SECRET FORMULA", "floating_frosted_card")
    assert "drawtext=text='SECRET FORMULA'" in filter_card
    assert "boxcolor=0x0b1120@0.85" in filter_card


def test_video_editing_agent_filters():
    agent = VideoEditingAgent()
    hook = HookVariant(
        id="h1",
        headline="STOP WASTING TIME",
        spoken_hook="Stop wasting time on low retention edits",
        hook_type="Contrarian",
        hook_score=94.0,
        visual_style="center_punch_title",
        ffmpeg_drawtext="drawtext=text='STOP WASTING TIME':fontsize=54",
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
        resp = client.get(f"/api/v1/clips/downloads/{test_clip_id}")
        assert resp.status_code == 200
        assert "video/mp4" in resp.headers.get("content-type", "")

        missing_resp = client.get("/api/v1/clips/downloads/non_existent_clip_xyz")
        assert missing_resp.status_code == 404
    finally:
        if test_file.exists():
            test_file.unlink()


def test_caption_agent_list_styles():
    styles = CaptionAgent.list_styles()
    assert len(styles) == 5
    style_ids = {s.id for s in styles}
    assert "hormozi_glow" in style_ids
    assert "mrbeast_yellow" in style_ids
    assert "karaoke_fill" in style_ids
    assert "tiktok_badge" in style_ids
    assert "minimal_clean" in style_ids


def test_caption_agent_ass_generation_all_styles(tmp_path: Path):
    agent = CaptionAgent(output_dir=tmp_path)
    words = [
        WordTimestamp(word="THIS", start=10.0, end=10.5),
        WordTimestamp(word="IS", start=10.5, end=11.0),
        WordTimestamp(word="AN", start=11.0, end=11.4),
        WordTimestamp(word="INSANE", start=11.4, end=12.0),
        WordTimestamp(word="VIRAL", start=12.0, end=12.6),
        WordTimestamp(word="SHORT", start=12.6, end=13.2),
    ]
    segment = TranscriptionSegment(
        id=1,
        start=10.0,
        end=13.5,
        text="This is an insane viral short",
        words=words,
    )
    transcript = TranscriptionResult(
        language="en",
        duration=30.0,
        full_text="This is an insane viral short",
        segments=[segment],
    )
    clip = ClipHighlight(
        id="clip_ass_test",
        start_time=10.0,
        end_time=14.0,
        duration=4.0,
        headline="INSANE VIRAL SHORT",
        virality_score=95.0,
    )

    all_styles = ["hormozi_glow", "mrbeast_yellow", "karaoke_fill", "tiktok_badge", "minimal_clean"]
    for s in all_styles:
        ass_path, count = agent.generate_ass_file(clip, transcript, style_id=s)
        assert ass_path.exists()
        assert count == 6
        content = ass_path.read_text(encoding="utf-8")
        assert "[Script Info]" in content
        assert "PlayResX: 1080" in content
        assert "PlayResY: 1920" in content
        assert "[V4+ Styles]" in content
        assert "[Events]" in content
        assert "Dialogue:" in content
        if s == "karaoke_fill":
            assert r"{\k" in content


def test_caption_agent_burn_mock(tmp_path: Path):
    agent = CaptionAgent(output_dir=tmp_path)
    fake_video = tmp_path / "fake_input.mp4"
    fake_video.write_bytes(b"dummy mp4")
    fake_ass = tmp_path / "fake.ass"
    fake_ass.write_text("[Script Info]\n", encoding="utf-8")

    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0)
        # Create the temp output file that FFmpeg would create
        temp_out = tmp_path / "clip1_captioned_temp.mp4"
        temp_out.write_bytes(b"dummy captioned mp4")

        res_path = agent.burn_captions_into_video(fake_video, fake_ass, "clip1")
        assert res_path.name == "clip1.mp4"
        assert res_path.exists()


def test_caption_styles_api_endpoint():
    resp = client.get("/api/v1/clips/caption-styles")
    assert resp.status_code == 200
    styles = resp.json()
    assert len(styles) == 5
    ids = [s["id"] for s in styles]
    assert "hormozi_glow" in ids
    assert "mrbeast_yellow" in ids


def test_rerender_clip_api_endpoint(tmp_path: Path):
    # Setup test job and clip
    test_video = settings.UPLOAD_DIR / "rerender_test_source.mp4"
    test_video.write_bytes(b"dummy source video content")

    hook = HookVariant(
        id="h_variant_1",
        headline="HOOK VARIANT 1",
        spoken_hook="Spoken teaser one",
        hook_type="Curiosity Gap",
        hook_score=95.0,
        visual_style="top_neon_pill",
    )
    clip = ClipHighlight(
        id="clip_rerender_1",
        start_time=0.0,
        end_time=5.0,
        duration=5.0,
        headline="INITIAL HEADLINE",
        virality_score=90.0,
        hooks=[hook],
        selected_hook=hook,
        caption_style="hormozi_glow",
    )
    job = create_new_job("rerender_test_source.mp4", video_filename="rerender_test_source.mp4")
    job.highlights = [clip]
    ACTIVE_JOBS[job.job_id] = job

    # Mock video editing and caption burning
    with (
        patch.object(VideoEditingAgent, "render_single_clip") as mock_edit,
        patch.object(CaptionAgent, "burn_captions_into_video") as mock_burn,
    ):
        rendered_cut = tmp_path / "clip_rerender_1.mp4"
        rendered_cut.write_bytes(b"base cut")
        mock_edit.return_value = rendered_cut
        mock_burn.return_value = rendered_cut

        rerender_payload = {
            "caption_style": "mrbeast_yellow",
            "hook_variant_id": "h_variant_1",
            "hook_style": "center_punch_title",
        }
        resp = client.post(
            f"/api/v1/clips/jobs/{job.job_id}/clips/{clip.id}/rerender",
            json=rerender_payload,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["caption_style"] == "mrbeast_yellow"
        assert data["selected_hook"]["visual_style"] == "center_punch_title"
        assert "/api/v1/clips/downloads/clip_rerender_1" in data["rendered_url"]

    if test_video.exists():
        test_video.unlink()


@pytest.mark.anyio
async def test_webhook_dispatcher():
    res_none = await dispatch_webhook(None, "test_event", "job1", "pending", 10, "msg")
    assert res_none is False

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
    resp_email = client.post(
        "/api/v1/admin/login",
        json={"username_or_email": "admin@email.com", "password": "1234"},
    )
    assert resp_email.status_code == 200
    data_email = resp_email.json()
    assert "access_token" in data_email
    token = data_email["access_token"]

    resp_user = client.post(
        "/api/v1/admin/login",
        json={"username_or_email": "admin", "password": "1234"},
    )
    assert resp_user.status_code == 200

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
    resp = client.post(
        "/api/v1/admin/login",
        json={"username_or_email": "admin@email.com", "password": "wrongpassword"},
    )
    assert resp.status_code == 401

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


def test_thumbnail_agent_generation(tmp_path: Path):
    agent = ThumbnailAgent(output_dir=tmp_path)
    clip = ClipHighlight(
        id="clip_thumb_unit_test",
        start_time=5.0,
        end_time=25.0,
        duration=20.0,
        headline="AI REVOLUTION BLUEPRINT",
        virality_score=94.0,
    )
    updated = agent.generate_thumbnail_for_clip(clip)
    assert updated.thumbnail_path is not None
    assert Path(updated.thumbnail_path).exists()
    assert "/api/v1/clips/clip_thumb_unit_test/thumbnail" in updated.thumbnail_url


def test_quality_review_agent_audit():
    agent = QualityReviewAgent(api_key=None)
    clip = ClipHighlight(
        id="clip_qa_unit_test",
        start_time=10.0,
        end_time=35.0,
        duration=25.0,
        headline="WHY SILICON VALUATION DROPPED",
        hook_text="Investors pulled billions out of tech companies today.",
        virality_score=91.0,
        hook_score=92.0,
        caption_word_count=55,
        editing_effects=["9:16 smart vertical crop", "loudness normalized audio"],
    )
    review = agent.audit_clip(clip)
    assert review.overall_score >= 80.0
    assert review.status in ("passed", "warning")
    assert len(review.checks) >= 5
    assert any(c.name == "Platform Duration Compliance" for c in review.checks)
    assert any(c.name == "Audio Loudness & Dynamics" for c in review.checks)
    assert any(c.name == "Brand Safety & Content Moderation" for c in review.checks)


def test_social_metadata_agent_generation():
    agent = SocialMetadataAgent(api_key=None)
    clip = ClipHighlight(
        id="clip_social_unit_test",
        start_time=12.0,
        end_time=38.0,
        duration=26.0,
        headline="THE $4T TECH MARKET ROUT",
        hook_text="Almost nobody realized what actually happened to semiconductor valuations.",
        virality_score=93.0,
    )
    meta = agent.generate_clip_metadata(clip)
    assert "#Shorts" in meta.youtube_shorts.title
    assert len(meta.youtube_shorts.hashtags) >= 3
    assert "#fyp" in meta.tiktok.hashtags
    assert len(meta.instagram_reels.hashtags) >= 3
    assert meta.youtube_shorts.pinned_comment != ""


def test_download_clip_thumbnail_endpoint(tmp_path: Path):
    settings.PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    test_clip_id = "test_thumb_endpoint_clip"
    test_thumb = settings.PROCESSED_DIR / f"{test_clip_id}_thumb.jpg"
    test_thumb.write_bytes(
        b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00`\x00`\x00\x00\xff\xdb\x00C\x00"
    )

    try:
        resp = client.get(f"/api/v1/clips/downloads/{test_clip_id}/thumbnail")
        assert resp.status_code == 200
        assert resp.headers["content-type"] == "image/jpeg"

        resp_alias = client.get(f"/api/v1/clips/{test_clip_id}/thumbnail")
        assert resp_alias.status_code == 200
    finally:
        if test_thumb.exists():
            test_thumb.unlink()

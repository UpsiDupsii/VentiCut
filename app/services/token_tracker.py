import datetime
import logging
from pathlib import Path
from typing import Any

from app.core.config import settings

logger = logging.getLogger(__name__)


class TokenTracker:
    """Singleton tracker for recording API usage, token consumption, and free-tier quotas."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init_tracker()
        return cls._instance

    def _init_tracker(self):
        # Daily reset timestamp tracker
        self.last_reset_date = datetime.date.today().isoformat()

        # Groq Quota & Usage
        self.groq_daily_token_limit = 500_000
        self.groq_daily_request_limit = 14_400
        self.groq_rpm_limit = 30
        self.groq_whisper_calls = 0
        self.groq_whisper_audio_minutes = 0.0
        self.groq_llm_calls = 0
        self.groq_llm_prompt_tokens = 0
        self.groq_llm_completion_tokens = 0

        # Gemini Quota & Usage
        self.gemini_daily_request_limit = 1_500
        self.gemini_rpm_limit = 15
        self.gemini_calls = 0
        self.gemini_estimated_tokens = 0

        # Webhook metrics
        self.webhooks_dispatched = 0
        self.webhooks_successful = 0

    def _check_daily_reset(self):
        today = datetime.date.today().isoformat()
        if today != self.last_reset_date:
            self.last_reset_date = today
            self.groq_whisper_calls = 0
            self.groq_whisper_audio_minutes = 0.0
            self.groq_llm_calls = 0
            self.groq_llm_prompt_tokens = 0
            self.groq_llm_completion_tokens = 0
            self.gemini_calls = 0
            self.gemini_estimated_tokens = 0

    def record_groq_whisper(self, duration_seconds: float = 0.0):
        self._check_daily_reset()
        self.groq_whisper_calls += 1
        self.groq_whisper_audio_minutes += round(duration_seconds / 60.0, 2)

    def record_groq_llm(self, prompt_tokens: int = 0, completion_tokens: int = 0):
        self._check_daily_reset()
        self.groq_llm_calls += 1
        self.groq_llm_prompt_tokens += prompt_tokens
        self.groq_llm_completion_tokens += completion_tokens

    def record_groq_tokens(self, total_tokens: int = 0):
        self._check_daily_reset()
        self.groq_llm_calls += 1
        self.groq_llm_prompt_tokens += total_tokens

    def record_gemini_call(self, estimated_tokens: int = 0):
        self._check_daily_reset()
        self.gemini_calls += 1
        self.gemini_estimated_tokens += estimated_tokens

    def record_webhook(self, success: bool):
        self.webhooks_dispatched += 1
        if success:
            self.webhooks_successful += 1

    def get_summary(self) -> dict[str, Any]:
        self._check_daily_reset()

        # Groq calculations
        groq_total_tokens = self.groq_llm_prompt_tokens + self.groq_llm_completion_tokens
        groq_tokens_remaining = max(0, self.groq_daily_token_limit - groq_total_tokens)
        groq_total_requests = self.groq_whisper_calls + self.groq_llm_calls
        groq_requests_remaining = max(0, self.groq_daily_request_limit - groq_total_requests)

        # Gemini calculations
        gemini_requests_remaining = max(0, self.gemini_daily_request_limit - self.gemini_calls)

        # Storage directory sizes
        def get_dir_size_mb(path: Path) -> float:
            if not path.exists():
                return 0.0
            total_bytes = sum(f.stat().st_size for f in path.glob("**/*") if f.is_file())
            return round(total_bytes / (1024 * 1024), 2)

        uploads_mb = get_dir_size_mb(settings.UPLOAD_DIR)
        temp_mb = get_dir_size_mb(settings.TEMP_DIR)
        processed_mb = get_dir_size_mb(settings.PROCESSED_DIR)

        return {
            "date": self.last_reset_date,
            "groq": {
                "whisper_calls": self.groq_whisper_calls,
                "whisper_audio_minutes": self.groq_whisper_audio_minutes,
                "audio_minutes_processed": self.groq_whisper_audio_minutes,
                "llm_calls": self.groq_llm_calls,
                "llm_prompt_tokens": self.groq_llm_prompt_tokens,
                "llm_completion_tokens": self.groq_llm_completion_tokens,
                "total_tokens_used": groq_total_tokens,
                "daily_token_limit": self.groq_daily_token_limit,
                "tokens_remaining": groq_tokens_remaining,
                "token_usage_percentage": round(
                    (groq_total_tokens / self.groq_daily_token_limit) * 100, 2
                ),
                "tokens_pct_used": round(
                    (groq_total_tokens / self.groq_daily_token_limit) * 100, 2
                ),
                "total_requests": groq_total_requests,
                "daily_request_limit": self.groq_daily_request_limit,
                "requests_remaining": groq_requests_remaining,
            },
            "gemini": {
                "requests_used": self.gemini_calls,
                "daily_request_limit": self.gemini_daily_request_limit,
                "requests_limit": self.gemini_daily_request_limit,
                "requests_remaining": gemini_requests_remaining,
                "request_usage_percentage": round(
                    (self.gemini_calls / self.gemini_daily_request_limit) * 100, 2
                ),
                "requests_pct_used": round(
                    (self.gemini_calls / self.gemini_daily_request_limit) * 100, 2
                ),
                "estimated_tokens": self.gemini_estimated_tokens,
            },
            "webhooks": {
                "total_dispatched": self.webhooks_dispatched,
                "successful": self.webhooks_successful,
                "failed": self.webhooks_dispatched - self.webhooks_successful,
                "success_rate_percentage": round(
                    (self.webhooks_successful / max(1, self.webhooks_dispatched)) * 100, 1
                ),
            },
            "storage": {
                "uploads_mb": uploads_mb,
                "temp_mb": temp_mb,
                "processed_mb": processed_mb,
                "total_mb": round(uploads_mb + temp_mb + processed_mb, 2),
            },
            "storage_mb": {
                "uploads": uploads_mb,
                "temp": temp_mb,
                "processed": processed_mb,
                "total": round(uploads_mb + temp_mb + processed_mb, 2),
            },
        }


token_tracker = TokenTracker()

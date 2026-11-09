import logging
from pathlib import Path

from groq import Groq

from app.core.config import settings
from app.models.clip import TranscriptionResult, TranscriptionSegment, WordTimestamp

logger = logging.getLogger(__name__)


class TranscriptionAgent:
    """Agent responsible for transcribing audio and generating precise word-level timestamps."""

    def __init__(self, api_key: str | None = None, model: str | None = None):
        self.api_key = api_key or settings.GROQ_API_KEY
        self.model = model or settings.GROQ_WHISPER_MODEL
        self.client = Groq(api_key=self.api_key) if self.api_key else None

    def transcribe(self, audio_path: Path) -> TranscriptionResult:
        """Transcribe an audio file using Groq Whisper API with word timestamps."""
        if not audio_path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        if not self.client:
            logger.warning("No GROQ_API_KEY provided. Using simulated transcription.")
            return self._simulated_transcription(audio_path)

        try:
            with open(audio_path, "rb") as audio_file:
                response = self.client.audio.transcriptions.create(
                    file=(audio_path.name, audio_file.read()),
                    model=self.model,
                    response_format="verbose_json",
                    timestamp_granularities=["segment", "word"],
                    temperature=0.0,
                )

            # Parse verbose_json response
            raw_data = response.to_dict() if hasattr(response, "to_dict") else response
            full_text = getattr(response, "text", "") or raw_data.get("text", "")
            duration = float(getattr(response, "duration", 0.0) or raw_data.get("duration", 0.0))
            language = getattr(response, "language", "en") or raw_data.get("language", "en")

            raw_segments = getattr(response, "segments", None) or raw_data.get("segments", [])
            raw_words = getattr(response, "words", None) or raw_data.get("words", [])

            segments: list[TranscriptionSegment] = []

            for idx, seg in enumerate(raw_segments):
                seg_dict = seg if isinstance(seg, dict) else seg.__dict__
                seg_start = float(seg_dict.get("start", 0.0))
                seg_end = float(seg_dict.get("end", 0.0))
                seg_text = seg_dict.get("text", "").strip()

                # Match words in this segment window
                segment_words: list[WordTimestamp] = []
                for w in raw_words:
                    w_dict = w if isinstance(w, dict) else w.__dict__
                    w_start = float(w_dict.get("start", 0.0))
                    w_end = float(w_dict.get("end", 0.0))
                    if seg_start <= w_start <= seg_end or (not raw_segments):
                        segment_words.append(
                            WordTimestamp(
                                word=w_dict.get("word", "").strip(),
                                start=w_start,
                                end=w_end,
                            )
                        )

                segments.append(
                    TranscriptionSegment(
                        id=idx,
                        start=seg_start,
                        end=seg_end,
                        text=seg_text,
                        words=segment_words,
                    )
                )

            return TranscriptionResult(
                language=language,
                duration=duration,
                full_text=full_text,
                segments=segments,
            )

        except Exception as e:
            logger.error(f"Groq Whisper transcription failed: {e}. Falling back to simulation.")
            return self._simulated_transcription(audio_path, str(e))

    def _simulated_transcription(
        self, audio_path: Path, error_note: str | None = None
    ) -> TranscriptionResult:
        """Fallback transcription when API key is missing or offline."""
        mock_segments = [
            TranscriptionSegment(
                id=0,
                start=0.0,
                end=5.5,
                text="Welcome to VentiCut, the automated AI video repurposing pipeline.",
                words=[
                    WordTimestamp(word="Welcome", start=0.0, end=0.8),
                    WordTimestamp(word="to", start=0.8, end=1.0),
                    WordTimestamp(word="VentiCut", start=1.0, end=1.8),
                    WordTimestamp(word="the", start=1.8, end=2.0),
                    WordTimestamp(word="automated", start=2.0, end=2.8),
                    WordTimestamp(word="AI", start=2.8, end=3.1),
                    WordTimestamp(word="video", start=3.1, end=3.6),
                    WordTimestamp(word="repurposing", start=3.6, end=4.6),
                    WordTimestamp(word="pipeline", start=4.6, end=5.5),
                ],
            ),
            TranscriptionSegment(
                id=1,
                start=5.5,
                end=11.2,
                text="In this video we demonstrate how long videos transform into viral shorts.",
                words=[
                    WordTimestamp(word="In", start=5.5, end=5.8),
                    WordTimestamp(word="this", start=5.8, end=6.1),
                    WordTimestamp(word="video", start=6.1, end=6.6),
                    WordTimestamp(word="we", start=6.6, end=6.9),
                    WordTimestamp(word="demonstrate", start=6.9, end=7.8),
                    WordTimestamp(word="how", start=7.8, end=8.1),
                    WordTimestamp(word="long", start=8.1, end=8.6),
                    WordTimestamp(word="videos", start=8.6, end=9.2),
                    WordTimestamp(word="transform", start=9.2, end=9.9),
                    WordTimestamp(word="into", start=9.9, end=10.3),
                    WordTimestamp(word="viral", start=10.3, end=10.8),
                    WordTimestamp(word="shorts", start=10.8, end=11.2),
                ],
            ),
        ]
        full_text = " ".join(s.text for s in mock_segments)
        if error_note:
            full_text = f"[{error_note}] {full_text}"

        return TranscriptionResult(
            language="en",
            duration=12.0,
            full_text=full_text,
            segments=mock_segments,
        )

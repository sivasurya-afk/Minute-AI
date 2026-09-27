"""
Audio transcription service using Groq Whisper Large V3.
"""

from typing import Tuple, Optional
import os
import tempfile
import logging
from services.groq_service import GroqService, DEFAULT_TRANSCRIPTION_MODEL

logger = logging.getLogger(__name__)


class TranscriptionService:
    """Handles audio transcription using Groq Whisper Large V3."""

    def __init__(self, groq_service: Optional[GroqService] = None):
        self.groq_service = groq_service or GroqService.get_instance()

    def transcribe_audio_bytes(
        self,
        file_bytes: bytes,
        file_name: str,
        model: Optional[str] = None,
    ) -> Tuple[bool, str]:
        """
        Transcribes audio data bytes using Groq Whisper Large V3.
        Returns: (success: bool, transcript_text_or_error_message: str)
        """
        if not self.groq_service.is_configured():
            return False, "Groq API key is not configured. Please supply a valid GROQ_API_KEY in your settings or .env."

        model_name = model or os.getenv("GROQ_TRANSCRIPTION_MODEL", DEFAULT_TRANSCRIPTION_MODEL)
        ext = os.path.splitext(file_name)[1] or ".mp3"

        tmp_path = None
        try:
            with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp_file:
                tmp_file.write(file_bytes)
                tmp_path = tmp_file.name

            with open(tmp_path, "rb") as audio_file:
                transcription = self.groq_service.client.audio.transcriptions.create(
                    file=audio_file,
                    model=model_name,
                    response_format="verbose_json",
                )

            # Extract full text
            text = getattr(transcription, "text", "")
            if not text and isinstance(transcription, dict):
                text = transcription.get("text", "")

            if not text:
                return False, "Transcription resulted in empty text. Please check the audio quality."

            return True, text.strip()

        except Exception as e:
            logger.error(f"Whisper transcription failed: {e}")
            return False, f"Transcription failed: {str(e)}"

        finally:
            if tmp_path and os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except OSError:
                    pass

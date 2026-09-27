"""
Input validation utilities for Minute AI.
Handles file format verification, size limits, and entity validation.
"""

from typing import Tuple, List, Optional
import os
import re

# File upload constants
MAX_AUDIO_SIZE_BYTES = 25 * 1024 * 1024  # 25 MB Groq Whisper API limit
ALLOWED_AUDIO_EXTENSIONS = {".mp3", ".wav", ".m4a", ".ogg", ".webm", ".flac", ".aac"}
ALLOWED_TEXT_EXTENSIONS = {".txt", ".vtt", ".srt"}

MIN_TRANSCRIPT_LENGTH = 20  # Minimum characters to constitute a valid meeting transcript


def validate_audio_file(filename: str, file_size: int) -> Tuple[bool, Optional[str]]:
    """Validate audio file extension and size."""
    ext = os.path.splitext(filename.lower())[1]
    if ext not in ALLOWED_AUDIO_EXTENSIONS:
        allowed = ", ".join(sorted(ALLOWED_AUDIO_EXTENSIONS))
        return False, f"Unsupported audio format '{ext}'. Allowed formats: {allowed}"

    if file_size > MAX_AUDIO_SIZE_BYTES:
        mb = file_size / (1024 * 1024)
        return False, f"File size ({mb:.1f} MB) exceeds maximum allowed size of 25 MB for Whisper transcription."

    if file_size == 0:
        return False, "Audio file is empty (0 bytes)."

    return True, None


def validate_text_file(filename: str, file_size: int) -> Tuple[bool, Optional[str]]:
    """Validate text/subtitle file extension and size."""
    ext = os.path.splitext(filename.lower())[1]
    if ext not in ALLOWED_TEXT_EXTENSIONS:
        allowed = ", ".join(sorted(ALLOWED_TEXT_EXTENSIONS))
        return False, f"Unsupported text file format '{ext}'. Allowed formats: {allowed}"

    # Allow up to 10 MB for text files
    if file_size > 10 * 1024 * 1024:
        return False, "Text file is unusually large (> 10 MB). Please check your file."

    if file_size == 0:
        return False, "Uploaded file is empty (0 bytes)."

    return True, None


def validate_transcript_content(content: str) -> Tuple[bool, Optional[str]]:
    """Validate transcript content length and validity."""
    if not content or not content.strip():
        return False, "Transcript text is empty. Please provide meeting discussion content."

    stripped = content.strip()
    if len(stripped) < MIN_TRANSCRIPT_LENGTH:
        return False, f"Transcript is too short ({len(stripped)} chars). Please provide a fuller transcript."

    return True, None


def validate_jira_project_key(key: str) -> Tuple[bool, Optional[str]]:
    """Validate Jira project key conforms to standard naming (e.g., 'CORE', 'FRONT-1')."""
    if not key or not key.strip():
        return False, "Project key cannot be empty."

    cleaned_key = key.strip().upper()
    if not re.match(r"^[A-Z][A-Z0-9_\-]{1,19}$", cleaned_key):
        return False, "Project key must start with a letter and contain only uppercase letters, numbers, and hyphens (2-20 characters)."

    return True, None

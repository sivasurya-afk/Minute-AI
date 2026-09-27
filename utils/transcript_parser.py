"""
Transcript parsing utilities.
Supports raw text, .txt files, WebVTT (.vtt), and SubRip (.srt) formats.
Strips cue timestamps, removes formatting markup, and preserves speaker attributions.
"""

import re
from typing import Dict, Any, List


class TranscriptParser:
    """Parser and normalizer for various transcript text and subtitle formats."""

    # Regex patterns
    VTT_HEADER_PATTERN = re.compile(r"^WEBVTT.*?(?:\r?\n){2,}", re.DOTALL | re.IGNORECASE)
    VTT_TIMESTAMP_PATTERN = re.compile(
        r"^(?:\d{1,2}:)?\d{2}:\d{2}\.\d{3}\s*-->\s*(?:\d{1,2}:)?\d{2}:\d{2}\.\d{3}.*$",
        re.MULTILINE,
    )
    SRT_TIMESTAMP_PATTERN = re.compile(
        r"^\d{2}:\d{2}:\d{2},\d{3}\s*-->\s*\d{2}:\d{2}:\d{2},\d{3}.*$",
        re.MULTILINE,
    )
    SRT_INDEX_PATTERN = re.compile(r"^\d+\s*$", re.MULTILINE)
    HTML_TAG_PATTERN = re.compile(r"<[^>]+>")
    SPEAKER_VOICE_TAG_PATTERN = re.compile(r"<v(?:\.[\w\-]+)?\s+([^>]+)>(.*?)(?:</v>|$)", re.IGNORECASE)

    @classmethod
    def parse_vtt(cls, content: str) -> str:
        """Parse WebVTT content, stripping header, timestamps, and formatting while keeping speaker info."""
        if not content:
            return ""

        # Remove WEBVTT header and comments
        text = cls.VTT_HEADER_PATTERN.sub("", content)

        # Replace voice tags <v SpeakerName>Dialogue with SpeakerName: Dialogue
        text = cls.SPEAKER_VOICE_TAG_PATTERN.sub(r"\1: \2", text)

        # Strip remaining HTML/formatting tags
        text = cls.HTML_TAG_PATTERN.sub("", text)

        lines = text.splitlines()
        cleaned_lines = []
        for line in lines:
            line_str = line.strip()
            if not line_str:
                continue
            # Skip VTT notes / cue settings / timestamps
            if line_str.startswith("NOTE"):
                continue
            if cls.VTT_TIMESTAMP_PATTERN.match(line_str):
                continue
            if re.match(r"^STYLE\b", line_str, re.IGNORECASE):
                continue
            cleaned_lines.append(line_str)

        return cls._consolidate_speaker_turns(cleaned_lines)

    @classmethod
    def parse_srt(cls, content: str) -> str:
        """Parse SubRip (.srt) subtitle content, removing indices and timestamps."""
        if not content:
            return ""

        lines = content.splitlines()
        cleaned_lines = []
        for line in lines:
            line_str = line.strip()
            if not line_str:
                continue
            # Skip numeric sequence counters
            if cls.SRT_INDEX_PATTERN.match(line_str):
                continue
            # Skip timestamp arrows
            if cls.SRT_TIMESTAMP_PATTERN.match(line_str):
                continue
            # Remove any stray HTML tags
            cleaned_line = cls.HTML_TAG_PATTERN.sub("", line_str).strip()
            if cleaned_line:
                cleaned_lines.append(cleaned_line)

        return cls._consolidate_speaker_turns(cleaned_lines)

    @classmethod
    def parse_text(cls, content: str) -> str:
        """Parse and normalize plain text transcripts."""
        if not content:
            return ""
        lines = [line.strip() for line in content.splitlines()]
        # Filter empty lines while preserving structural spacing
        cleaned = [line for line in lines if line]
        return cls._consolidate_speaker_turns(cleaned)

    @classmethod
    def parse(cls, content: str, source_type: str = "paste") -> str:
        """Dispatch parsing based on input source format."""
        source_lower = source_type.lower()
        if source_lower == "vtt":
            return cls.parse_vtt(content)
        elif source_lower == "srt":
            return cls.parse_srt(content)
        else:
            return cls.parse_text(content)

    @classmethod
    def _consolidate_speaker_turns(cls, lines: List[str]) -> str:
        """
        Groups consecutive lines spoken by the same person into a single paragraph.
        Recognizes common formats like 'Alice: text', '[Bob] text', '(Charlie) text'.
        """
        if not lines:
            return ""

        speaker_pattern = re.compile(r"^([A-Z][a-zA-Z0-9_\-\s]{1,30}):\s*(.*)$")
        bracket_speaker_pattern = re.compile(r"^\[([A-Z][a-zA-Z0-9_\-\s]{1,30})\]\s*(.*)$")

        turns: List[str] = []
        current_speaker: str = ""
        current_utterance: List[str] = []

        for line in lines:
            speaker_match = speaker_pattern.match(line)
            bracket_match = bracket_speaker_pattern.match(line)

            if speaker_match:
                speaker = speaker_match.group(1).strip()
                utterance = speaker_match.group(2).strip()
            elif bracket_match:
                speaker = bracket_match.group(1).strip()
                utterance = bracket_match.group(2).strip()
            else:
                speaker = None
                utterance = line

            if speaker:
                if speaker == current_speaker:
                    if utterance:
                        current_utterance.append(utterance)
                else:
                    if current_speaker and current_utterance:
                        turns.append(f"{current_speaker}: {' '.join(current_utterance)}")
                    current_speaker = speaker
                    current_utterance = [utterance] if utterance else []
            else:
                if current_speaker:
                    current_utterance.append(utterance)
                else:
                    turns.append(utterance)

        if current_speaker and current_utterance:
            turns.append(f"{current_speaker}: {' '.join(current_utterance)}")

        return "\n\n".join(turns) if turns else "\n\n".join(lines)

    @classmethod
    def get_metadata(cls, text: str) -> Dict[str, Any]:
        """Compute basic statistical metadata for transcript analysis."""
        if not text:
            return {"word_count": 0, "line_count": 0, "speaker_count": 0, "estimated_minutes": 0}

        words = text.split()
        word_count = len(words)
        lines = [l for l in text.splitlines() if l.strip()]

        # Identify speakers
        speaker_regex = re.compile(r"^([A-Z][a-zA-Z0-9_\-\s]{1,30}):", re.MULTILINE)
        speakers = set(speaker_regex.findall(text))

        # Average spoken English rate is ~140 words per minute
        estimated_minutes = max(1, round(word_count / 140)) if word_count > 0 else 0

        return {
            "word_count": word_count,
            "line_count": len(lines),
            "speaker_count": len(speakers),
            "speakers": sorted(list(speakers)),
            "estimated_minutes": estimated_minutes,
        }

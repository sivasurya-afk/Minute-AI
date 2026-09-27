"""
Tests for TranscriptParser across plain text, WebVTT, and SubRip SRT formats.
"""

from utils.transcript_parser import TranscriptParser


def test_parse_plain_text():
    raw = (
        "Alice: Hello everyone.\n\n"
        "Bob: I will implement the auth token refresh endpoint.\n"
        "Bob: And I will write unit tests for it."
    )
    parsed = TranscriptParser.parse(raw, source_type="paste")
    assert "Alice: Hello everyone." in parsed
    assert "Bob: I will implement the auth token refresh endpoint. And I will write unit tests for it." in parsed


def test_parse_vtt(sample_raw_vtt):
    parsed = TranscriptParser.parse_vtt(sample_raw_vtt)
    # Check that WEBVTT headers and timestamps are stripped
    assert "WEBVTT" not in parsed
    assert "00:00:01" not in parsed
    assert "-->" not in parsed
    # Check that voice tags are converted to Speaker: Text
    assert "Alice: Let's kick off the sync." in parsed
    assert "Bob: I will optimize the Redis caching layer by Thursday." in parsed


def test_parse_srt(sample_raw_srt):
    parsed = TranscriptParser.parse_srt(sample_raw_srt)
    # Check that sequence numbers and timestamp arrows are stripped
    assert "00:00:01" not in parsed
    assert "-->" not in parsed
    # Speaker dialogue preserved
    assert "Alice: Let's kick off the sync." in parsed
    assert "Bob: I will optimize the Redis caching layer by Thursday." in parsed


def test_parse_empty_input():
    assert TranscriptParser.parse("") == ""
    assert TranscriptParser.parse("   \n\n  ") == ""
    meta = TranscriptParser.get_metadata("")
    assert meta["word_count"] == 0
    assert meta["speaker_count"] == 0


def test_get_metadata():
    text = (
        "Alice: We need to ship the release on time.\n\n"
        "Bob: I will monitor the error rates after deployment.\n\n"
        "Charlie: I will coordinate with customer support."
    )
    meta = TranscriptParser.get_metadata(text)
    assert meta["word_count"] > 10
    assert meta["speaker_count"] == 3
    assert "Alice" in meta["speakers"]
    assert "Bob" in meta["speakers"]
    assert "Charlie" in meta["speakers"]
    assert meta["estimated_minutes"] >= 1

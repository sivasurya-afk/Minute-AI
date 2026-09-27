"""
Tests for Duplicate Detection across action items and transcripts.
"""

from utils.helpers import (
    calculate_jaccard_similarity,
    deduplicate_extracted_items,
    compute_content_hash,
)
from database.repositories import TranscriptRepository


def test_jaccard_similarity():
    s1 = "Implement Redis caching layer for authentication"
    s2 = "Implement Redis caching layer for auth tokens"
    s3 = "Completely unrelated task about marketing budget"

    sim_high = calculate_jaccard_similarity(s1, s2)
    sim_low = calculate_jaccard_similarity(s1, s3)

    assert sim_high > 0.50
    assert sim_low == 0.0


def test_deduplicate_extracted_items():
    items = [
        {
            "action_title": "Implement Redis caching layer",
            "source_excerpt": "Bob: I will implement the Redis caching layer by Thursday.",
            "confidence_score": 0.80,
            "assignee": "Bob",
        },
        {
            "action_title": "Implement Redis caching layer for auth",
            "source_excerpt": "Bob: I will implement the Redis caching layer by Thursday.",
            "confidence_score": 0.95,
            "assignee": "Bob",
        },
        {
            "action_title": "Fix navbar avatar bug",
            "source_excerpt": "Charlie: I will fix the avatar image rendering bug.",
            "confidence_score": 0.90,
            "assignee": "Charlie",
        },
    ]

    deduped = deduplicate_extracted_items(items, threshold=0.70)
    # The two Redis caching items should merge into 1, retaining confidence_score 0.95
    assert len(deduped) == 2
    redis_item = next(i for i in deduped if "Redis" in i["action_title"])
    assert redis_item["confidence_score"] == 0.95


def test_content_hash_consistency():
    t1 = "Alice: Let's start the meeting."
    t2 = "  Alice:   Let's start the meeting.  \n"
    assert compute_content_hash(t1) == compute_content_hash(t2)


def test_transcript_repository_duplicate_detection():
    repo = TranscriptRepository()
    user_id = "00000000-0000-0000-0000-000000000001"

    # From mock seed: "Incident Postmortem: API Latency Spike"
    existing = repo.find_duplicate(
        user_id=user_id,
        meeting_name="Incident Postmortem: API Latency Spike",
        meeting_date=repo.mock_db.transcripts[1]["meeting_date"],
    )
    assert existing is not None
    assert existing["meeting_name"] == "Incident Postmortem: API Latency Spike"

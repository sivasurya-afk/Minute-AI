"""
Tests for ActionExtractor and Pydantic schema validation.
"""

from unittest.mock import MagicMock
from models.action_item import ActionItemExtraction, ActionItemBatch
from services.action_extractor import ActionExtractor


def test_action_item_pydantic_validation():
    data = {
        "action_title": "Implement Redis Cache",
        "description": "Add Redis caching to auth endpoints to lower DB load",
        "assignee": "Bob",
        "jira_project_key": "CORE",
        "priority": "High",
        "due_date": "Thursday",
        "action_type": "feature",
        "source_excerpt": "Bob: I will complete the Redis caching layer implementation by Thursday.",
        "confidence_score": 0.95,
        "clarification_required": False,
        "clarification_reason": None,
    }
    item = ActionItemExtraction.model_validate(data)
    assert item.action_title == "Implement Redis Cache"
    assert item.assignee == "Bob"
    assert item.priority == "High"
    assert item.confidence_score == 0.95


def test_action_item_null_handling():
    """Verify that empty, 'none', or 'null' strings are sanitized to None without hallucination."""
    data = {
        "action_title": "Investigate latency",
        "description": "Examine database latency graphs",
        "assignee": "None",
        "jira_project_key": "n/a",
        "priority": None,
        "due_date": "unknown",
        "action_type": "investigation",
        "source_excerpt": "Someone should look into latency.",
        "confidence_score": 0.70,
        "clarification_required": True,
        "clarification_reason": "No owner assigned",
    }
    item = ActionItemExtraction.model_validate(data)
    assert item.assignee is None
    assert item.jira_project_key is None
    assert item.due_date is None
    assert item.priority is None
    assert item.clarification_required is True


def test_extractor_with_mock_groq(sample_projects):
    mock_groq = MagicMock()
    mock_groq.is_configured.return_value = True
    mock_groq.chat_completion_json.return_value = {
        "items": [
            {
                "action_title": "Implement Redis cache",
                "description": "Cache session tokens in Redis",
                "assignee": "Bob",
                "jira_project_key": "CORE",
                "priority": "High",
                "due_date": "Thursday",
                "action_type": "feature",
                "source_excerpt": "Bob: I will complete Redis caching by Thursday.",
                "confidence_score": 0.95,
                "clarification_required": False,
                "clarification_reason": None,
            }
        ]
    }

    extractor = ActionExtractor(groq_service=mock_groq)
    success, items, err = extractor.extract_action_items(
        transcript_text="Bob: I will complete Redis caching by Thursday.",
        active_projects=sample_projects,
        meeting_name="Sprint Sync",
    )

    assert success is True
    assert len(items) == 1
    assert items[0]["action_title"] == "Implement Redis cache"
    assert items[0]["jira_project_key"] == "CORE"
    assert items[0]["project_id"] == "proj-uuid-2"
    assert items[0]["assignee"] == "Bob"


def test_extractor_retry_on_invalid_json(sample_projects):
    """Test that extractor feeds schema failure back to LLM and recovers on retry."""
    mock_groq = MagicMock()
    mock_groq.is_configured.return_value = True

    # 1st call fails schema validation (missing required 'source_excerpt' and 'action_title')
    invalid_response = {"items": [{"description": "Missing title"}]}

    # 2nd call (retry) returns valid schema
    valid_response = {
        "items": [
            {
                "action_title": "Fix memory leaks",
                "description": "Audit and fix leaks in staging cluster",
                "assignee": "Dana",
                "jira_project_key": "INFRA",
                "priority": "High",
                "due_date": "Friday",
                "action_type": "task",
                "source_excerpt": "Dana: I will audit memory limits by Friday.",
                "confidence_score": 0.90,
                "clarification_required": False,
                "clarification_reason": None,
            }
        ]
    }

    mock_groq.chat_completion_json.side_effect = [invalid_response, valid_response]

    extractor = ActionExtractor(groq_service=mock_groq)
    success, items, err = extractor.extract_action_items(
        transcript_text="Dana: I will audit memory limits by Friday.",
        active_projects=sample_projects,
    )

    assert success is True
    assert len(items) == 1
    assert items[0]["action_title"] == "Fix memory leaks"
    assert items[0]["jira_project_key"] == "INFRA"
    # Verify that mock was called twice (initial + retry)
    assert mock_groq.chat_completion_json.call_count == 2

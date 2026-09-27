"""
Tests for Database Repositories and User Data Isolation.
"""

import pytest
from database.repositories import ProjectRepository, TranscriptRepository, ActionItemRepository


def test_project_repository_crud():
    repo = ProjectRepository()
    user_id = "test-user-iso-1"

    # Create
    created = repo.create_project(
        user_id=user_id,
        project_data={
            "project_name": "Billing Service",
            "project_key": "BILL",
            "description": "Stripe invoices and payment webhooks",
            "team_name": "Finance",
            "keywords": ["stripe", "billing", "invoice"],
            "is_active": True,
        },
    )
    assert created["project_key"] == "BILL"

    # Duplicate key rejection
    with pytest.raises(ValueError, match="already exists"):
        repo.create_project(
            user_id=user_id,
            project_data={
                "project_name": "Duplicate Billing",
                "project_key": "BILL",
            },
        )

    # Fetch
    proj = repo.get_project_by_key(user_id, "BILL")
    assert proj is not None
    assert proj["project_name"] == "Billing Service"

    # Update
    repo.update_project(user_id, created["id"], {"team_name": "Core Payments"})
    updated = repo.get_project_by_id(user_id, created["id"])
    assert updated["team_name"] == "Core Payments"

    # Toggle active
    repo.toggle_active(user_id, created["id"], False)
    assert repo.get_project_by_id(user_id, created["id"])["is_active"] is False

    # Delete
    deleted = repo.delete_project(user_id, created["id"])
    assert deleted is True
    assert repo.get_project_by_id(user_id, created["id"]) is None


def test_user_data_isolation():
    """Verify that user A cannot see or access user B's projects or transcripts."""
    proj_repo = ProjectRepository()
    user_a = "user-a-1111"
    user_b = "user-b-2222"

    p_a = proj_repo.create_project(
        user_id=user_a,
        project_data={"project_name": "Project A Secret", "project_key": "SECA"},
    )
    p_b = proj_repo.create_project(
        user_id=user_b,
        project_data={"project_name": "Project B Secret", "project_key": "SECB"},
    )

    projects_for_a = proj_repo.get_projects(user_a)
    keys_for_a = [p["project_key"] for p in projects_for_a]
    assert "SECA" in keys_for_a
    assert "SECB" not in keys_for_a

    # Clean up
    proj_repo.delete_project(user_a, p_a["id"])
    proj_repo.delete_project(user_b, p_b["id"])


def test_transcript_and_action_item_cascade():
    t_repo = TranscriptRepository()
    a_repo = ActionItemRepository()
    user_id = "cascade-test-user"

    # Create transcript
    t = t_repo.create_transcript(
        user_id=user_id,
        transcript_data={
            "meeting_name": "Cascade Test Meeting",
            "meeting_date": "2026-09-27",
            "transcript_text": "Alice: I will fix this.",
            "source_type": "paste",
        },
    )

    # Bulk create action items
    items = [
        {
            "action_title": "Fix item 1",
            "description": "Fix 1",
            "assignee": "Alice",
            "priority": "High",
            "source_excerpt": "Alice: I will fix this.",
            "confidence_score": 0.90,
        },
        {
            "action_title": "Fix item 2",
            "description": "Fix 2",
            "assignee": "Alice",
            "priority": "Medium",
            "source_excerpt": "Alice: I will fix this.",
            "confidence_score": 0.85,
        },
    ]
    created_items = a_repo.bulk_create_action_items(user_id, t["id"], items)
    assert len(created_items) == 2

    # Status update
    a_repo.update_action_item_status(user_id, created_items[0]["id"], "Approved")
    approved_items = a_repo.get_action_items(user_id, filters={"status": "Approved"})
    assert any(i["id"] == created_items[0]["id"] for i in approved_items)

    # Check metrics
    metrics = a_repo.get_dashboard_metrics(user_id)
    assert metrics["total_action_items"] >= 2
    assert metrics["approved_items"] >= 1

    # Delete transcript and verify cascade
    t_repo.delete_transcript(user_id, t["id"])
    remaining_items = a_repo.get_action_items(user_id, filters={"transcript_id": t["id"]})
    assert len(remaining_items) == 0

"""
Tests for ProjectMapper and Jira classification context formatting.
"""

from services.project_mapper import ProjectMapper


def test_project_mapper_prompt_context(sample_projects):
    mapper = ProjectMapper(sample_projects)
    context = mapper.generate_classification_prompt_context()

    assert "AVAILABLE JIRA PROJECTS" in context
    assert "[FRONT]" in context
    assert "[CORE]" in context
    assert "[INFRA]" in context
    assert "FastAPI backend services" in context


def test_project_mapper_valid_link(sample_projects):
    mapper = ProjectMapper(sample_projects, confidence_threshold=0.70)
    item = {
        "action_title": "Fix navbar",
        "jira_project_key": "FRONT",
        "confidence_score": 0.88,
    }

    linked = mapper.validate_and_link_project(item)
    assert linked["project_id"] == "proj-uuid-1"
    assert linked["jira_project_key"] == "FRONT"
    assert linked["project_name"] == "Frontend Web App"
    assert linked.get("clarification_required") is False or linked.get("clarification_required") is None


def test_project_mapper_unknown_key_falls_back(sample_projects):
    mapper = ProjectMapper(sample_projects)
    item = {
        "action_title": "Build rocket engine",
        "jira_project_key": "SPACEX",  # Unknown key
        "confidence_score": 0.90,
    }

    linked = mapper.validate_and_link_project(item)
    assert linked["project_id"] is None
    assert linked["jira_project_key"] is None
    assert linked["clarification_required"] is True
    assert "SPACEX" in linked["clarification_reason"]


def test_project_mapper_low_confidence_flag(sample_projects):
    mapper = ProjectMapper(sample_projects, confidence_threshold=0.75)
    item = {
        "action_title": "Maybe update some config",
        "jira_project_key": "CORE",
        "confidence_score": 0.60,  # Below 0.75 threshold
    }

    linked = mapper.validate_and_link_project(item)
    assert linked["project_id"] == "proj-uuid-2"
    assert linked["clarification_required"] is True
    assert "Low classification confidence" in linked["clarification_reason"]

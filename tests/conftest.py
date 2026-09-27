"""
Pytest configuration and shared fixtures for Minute AI test suite.
"""

import sys
import os
import pytest

# Ensure minute-AI directory is in Python path for test discovery
minute_ai_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if minute_ai_dir not in sys.path:
    sys.path.insert(0, minute_ai_dir)


@pytest.fixture
def sample_projects():
    """Sample active Jira projects for testing classification."""
    return [
        {
            "id": "proj-uuid-1",
            "user_id": "test-user-uuid",
            "project_name": "Frontend Web App",
            "project_key": "FRONT",
            "description": "User interface, Next.js, React components, CSS styling, and dashboard pages.",
            "team_name": "Frontend Team",
            "keywords": ["frontend", "ui", "react", "nextjs", "css", "avatar", "sidebar", "button"],
            "is_active": True,
        },
        {
            "id": "proj-uuid-2",
            "user_id": "test-user-uuid",
            "project_name": "Core Backend API",
            "project_key": "CORE",
            "description": "FastAPI backend services, database migrations, caching, and auth endpoints.",
            "team_name": "Backend Team",
            "keywords": ["backend", "api", "redis", "database", "sql", "auth", "token", "cache"],
            "is_active": True,
        },
        {
            "id": "proj-uuid-3",
            "user_id": "test-user-uuid",
            "project_name": "Cloud Infrastructure",
            "project_key": "INFRA",
            "description": "Kubernetes, Docker containers, Terraform, CI/CD pipelines, and monitoring.",
            "team_name": "DevOps",
            "keywords": ["devops", "k8s", "kubernetes", "docker", "terraform", "monitoring", "alert"],
            "is_active": True,
        },
    ]


@pytest.fixture
def sample_raw_vtt():
    return """WEBVTT

00:00:01.000 --> 00:00:04.000
<v Alice>Let's kick off the sync.</v>

00:00:05.000 --> 00:00:09.000
<v Bob>I will optimize the Redis caching layer by Thursday.</v>
"""


@pytest.fixture
def sample_raw_srt():
    return """1
00:00:01,000 --> 00:00:04,000
Alice: Let's kick off the sync.

2
00:00:05,000 --> 00:00:09,000
Bob: I will optimize the Redis caching layer by Thursday.
"""

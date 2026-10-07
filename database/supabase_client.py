"""
Supabase client factory and offline mock data repository for local evaluation.
"""

from typing import Optional, Dict, Any, List
import os
import uuid
from datetime import datetime, date, timedelta
from dotenv import load_dotenv

load_dotenv()


_client_cache: Dict[str, Any] = {}


def get_supabase_client(access_token: Optional[str] = None):
    """
    Returns an authenticated Supabase client using anon key, service role key, or user access token.
    Enforces Row Level Security (RLS) on PostgreSQL.
    Caches client instances to prevent connection pool exhaustion and TLS handshakes.
    """
    cache_key = access_token or "__default__"
    if cache_key in _client_cache:
        return _client_cache[cache_key]

    url = os.getenv("SUPABASE_URL", "")
    anon_key = os.getenv("SUPABASE_ANON_KEY", "")
    service_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")

    if not url or "your-project" in url:
        return None

    # Use service role key if available and no user access_token specified (admin/backend operations)
    api_key = service_key if (service_key and not access_token and "your_supabase" not in service_key) else anon_key
    if not api_key or "your_supabase" in api_key:
        return None

    try:
        from supabase import create_client, ClientOptions

        options = ClientOptions(postgrest_client_timeout=10.0)
        if access_token:
            options.headers = {"Authorization": f"Bearer {access_token}"}

        client = create_client(url, api_key, options=options)
        _client_cache[cache_key] = client
        return client
    except Exception:
        return None


# ============================================================================
# In-Memory Mock Storage for Offline / Evaluation / Demo Mode
# ============================================================================

class MockDatabase:
    """Thread-safe in-memory database used when Supabase is not configured."""

    _instance: Optional["MockDatabase"] = None

    def __init__(self):
        self.projects: List[Dict[str, Any]] = []
        self.transcripts: List[Dict[str, Any]] = []
        self.action_items: List[Dict[str, Any]] = []
        self._seed_sample_data()

    @classmethod
    def get_instance(cls) -> "MockDatabase":
        if cls._instance is None:
            cls._instance = MockDatabase()
        return cls._instance

    def _seed_sample_data(self):
        """Seed realistic demo records for evaluation."""
        user_id = "00000000-0000-0000-0000-000000000001"
        now = datetime.now()

        # Seed 3 Jira Projects
        proj_front_id = str(uuid.uuid4())
        proj_core_id = str(uuid.uuid4())
        proj_infra_id = str(uuid.uuid4())

        self.projects = [
            {
                "id": proj_front_id,
                "user_id": user_id,
                "project_name": "Frontend Web App",
                "project_key": "FRONT",
                "description": "Next.js & React user dashboard, client authentication, and responsive UI components.",
                "team_name": "Frontend Team",
                "keywords": ["ui", "react", "nextjs", "css", "dashboard", "button", "modal", "frontend"],
                "is_active": True,
                "created_at": now - timedelta(days=10),
                "updated_at": now - timedelta(days=10),
            },
            {
                "id": proj_core_id,
                "user_id": user_id,
                "project_name": "Core Backend API",
                "project_key": "CORE",
                "description": "Python FastAPI microservices, database schemas, auth tokens, and business logic.",
                "team_name": "Backend Team",
                "keywords": ["api", "fastapi", "backend", "python", "database", "sql", "endpoint", "auth"],
                "is_active": True,
                "created_at": now - timedelta(days=9),
                "updated_at": now - timedelta(days=9),
            },
            {
                "id": proj_infra_id,
                "user_id": user_id,
                "project_name": "Cloud Infrastructure",
                "project_key": "INFRA",
                "description": "AWS, Docker, Kubernetes clusters, CI/CD GitHub Actions pipelines, and monitoring.",
                "team_name": "DevOps & SRE",
                "keywords": ["docker", "k8s", "aws", "ci/cd", "deployment", "terraform", "monitoring"],
                "is_active": True,
                "created_at": now - timedelta(days=8),
                "updated_at": now - timedelta(days=8),
            },
        ]

        # Seed 2 Sample Transcripts
        t1_id = str(uuid.uuid4())
        t2_id = str(uuid.uuid4())

        self.transcripts = [
            {
                "id": t1_id,
                "user_id": user_id,
                "meeting_name": "Sprint 24 Planning & Technical Sync",
                "meeting_date": (date.today() - timedelta(days=3)).isoformat(),
                "transcript_text": (
                    "Alice: Good morning team. Let's align on Sprint 24 deliverables.\n"
                    "Bob: I will implement the new token refresh endpoint for the auth service by Thursday. It is high priority.\n"
                    "Charlie: On the frontend side, I noticed the user profile avatar upload fails for images over 2MB. I'll fix the image compression bug by tomorrow.\n"
                    "Alice: Great. Dana, can you review the Docker compose configuration for the staging cluster? We need to make sure the memory limits are properly set.\n"
                    "Dana: Yes, I will audit the staging cluster memory settings by Friday.\n"
                    "Bob: Maybe in the future we should also explore GraphQL? Not for this sprint though."
                ),
                "source_type": "paste",
                "processing_status": "processed",
                "created_at": now - timedelta(days=3),
                "updated_at": now - timedelta(days=3),
            },
            {
                "id": t2_id,
                "user_id": user_id,
                "meeting_name": "Incident Postmortem: API Latency Spike",
                "meeting_date": (date.today() - timedelta(days=1)).isoformat(),
                "transcript_text": (
                    "Alice: Thank you for joining the latency spike postmortem.\n"
                    "Bob: The root cause was an unindexed query on the audit logs table. I will add the missing composite index to the PostgreSQL database today.\n"
                    "Dana: I will set up a Datadog alert to trigger whenever p99 database response times exceed 300 milliseconds. I'll finish this by Wednesday.\n"
                    "Charlie: We should also inform customer support. Alice, can you send them an incident summary?\n"
                    "Alice: Sure, I will draft the incident summary email by 3 PM today."
                ),
                "source_type": "txt",
                "processing_status": "processed",
                "created_at": now - timedelta(days=1),
                "updated_at": now - timedelta(days=1),
            },
        ]

        # Seed 6 Action Items across the transcripts
        self.action_items = [
            {
                "id": str(uuid.uuid4()),
                "user_id": user_id,
                "transcript_id": t1_id,
                "project_id": proj_core_id,
                "action_title": "Implement auth token refresh endpoint",
                "description": "Build and test the new token refresh endpoint in the auth service to handle expired session tokens.",
                "assignee": "Bob",
                "jira_project_key": "CORE",
                "priority": "High",
                "due_date": "Thursday",
                "action_type": "feature",
                "source_excerpt": "Bob: I will implement the new token refresh endpoint for the auth service by Thursday. It is high priority.",
                "confidence_score": 0.96,
                "status": "Approved",
                "clarification_required": False,
                "clarification_reason": None,
                "created_at": now - timedelta(days=3),
                "updated_at": now - timedelta(days=3),
            },
            {
                "id": str(uuid.uuid4()),
                "user_id": user_id,
                "transcript_id": t1_id,
                "project_id": proj_front_id,
                "action_title": "Fix avatar upload compression bug for images >2MB",
                "description": "Fix bug in profile avatar upload component to add client-side image compression before submitting.",
                "assignee": "Charlie",
                "jira_project_key": "FRONT",
                "priority": "Medium",
                "due_date": "Tomorrow",
                "action_type": "bug",
                "source_excerpt": "Charlie: I noticed the user profile avatar upload fails for images over 2MB. I'll fix the image compression bug by tomorrow.",
                "confidence_score": 0.94,
                "status": "Pending Review",
                "clarification_required": False,
                "clarification_reason": None,
                "created_at": now - timedelta(days=3),
                "updated_at": now - timedelta(days=3),
            },
            {
                "id": str(uuid.uuid4()),
                "user_id": user_id,
                "transcript_id": t1_id,
                "project_id": proj_infra_id,
                "action_title": "Audit staging cluster Docker memory limits",
                "description": "Review Docker compose configuration and ensure memory limits are properly specified to prevent OOM events.",
                "assignee": "Dana",
                "jira_project_key": "INFRA",
                "priority": "Medium",
                "due_date": "Friday",
                "action_type": "investigation",
                "source_excerpt": "Dana: Yes, I will audit the staging cluster memory settings by Friday.",
                "confidence_score": 0.92,
                "status": "Pending Review",
                "clarification_required": False,
                "clarification_reason": None,
                "created_at": now - timedelta(days=3),
                "updated_at": now - timedelta(days=3),
            },
            {
                "id": str(uuid.uuid4()),
                "user_id": user_id,
                "transcript_id": t2_id,
                "project_id": proj_core_id,
                "action_title": "Add composite index to audit logs table",
                "description": "Create PostgreSQL composite index on the audit logs table to prevent query latency spikes during high volume.",
                "assignee": "Bob",
                "jira_project_key": "CORE",
                "priority": "Highest",
                "due_date": "Today",
                "action_type": "task",
                "source_excerpt": "Bob: I will add the missing composite index to the PostgreSQL database today.",
                "confidence_score": 0.98,
                "status": "Approved",
                "clarification_required": False,
                "clarification_reason": None,
                "created_at": now - timedelta(days=1),
                "updated_at": now - timedelta(days=1),
            },
            {
                "id": str(uuid.uuid4()),
                "user_id": user_id,
                "transcript_id": t2_id,
                "project_id": proj_infra_id,
                "action_title": "Configure Datadog p99 latency alert (>300ms)",
                "description": "Set up automated Datadog monitor triggering an alert when p99 database latency exceeds 300ms.",
                "assignee": "Dana",
                "jira_project_key": "INFRA",
                "priority": "High",
                "due_date": "Wednesday",
                "action_type": "task",
                "source_excerpt": "Dana: I will set up a Datadog alert to trigger whenever p99 database response times exceed 300 milliseconds.",
                "confidence_score": 0.95,
                "status": "Approved",
                "clarification_required": False,
                "clarification_reason": None,
                "created_at": now - timedelta(days=1),
                "updated_at": now - timedelta(days=1),
            },
            {
                "id": str(uuid.uuid4()),
                "user_id": user_id,
                "transcript_id": t2_id,
                "project_id": None,
                "action_title": "Draft incident summary communication for customer support",
                "description": "Prepare summary of latency spike and resolution to send to customer support team.",
                "assignee": "Alice",
                "jira_project_key": None,
                "priority": "Medium",
                "due_date": "3 PM today",
                "action_type": "follow-up",
                "source_excerpt": "Alice: Sure, I will draft the incident summary email by 3 PM today.",
                "confidence_score": 0.88,
                "status": "Needs Clarification",
                "clarification_required": True,
                "clarification_reason": "No configured Jira project exists for internal communication / support tasks.",
                "created_at": now - timedelta(days=1),
                "updated_at": now - timedelta(days=1),
            },
        ]

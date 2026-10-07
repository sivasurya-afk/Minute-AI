"""
Repository for Jira Projects.
Operates on Supabase PostgreSQL with automatic fallback to MockDatabase.
"""

from typing import List, Dict, Any, Optional
import uuid
import logging
from datetime import datetime
from database.supabase_client import get_supabase_client, MockDatabase

logger = logging.getLogger(__name__)


class ProjectRepository:
    """Data access layer for Jira Projects."""

    def __init__(self, access_token: Optional[str] = None):
        self.client = get_supabase_client(access_token)
        self.mock_db = MockDatabase.get_instance()

    def get_projects(self, user_id: str, active_only: bool = False) -> List[Dict[str, Any]]:
        """Fetch all Jira projects owned by user."""
        if self.client:
            try:
                query = self.client.table("jira_projects").select("*").eq("user_id", user_id)
                if active_only:
                    query = query.eq("is_active", True)
                res = query.order("project_name").execute()
                if res.data or user_id != "00000000-0000-0000-0000-000000000001":
                    return res.data or []
            except Exception as e:
                logger.warning(f"Supabase get_projects failed, falling back to mock database: {e}")

        # Mock fallback
        projects = [
            p for p in self.mock_db.projects
            if (p.get("user_id") == user_id or p.get("user_id") == "00000000-0000-0000-0000-000000000001")
        ]
        if active_only:
            projects = [p for p in projects if p.get("is_active", True)]
        return sorted(projects, key=lambda x: x.get("project_name", "").lower())

    def get_project_by_id(self, user_id: str, project_id: str) -> Optional[Dict[str, Any]]:
        """Fetch single project by ID."""
        if self.client:
            try:
                res = self.client.table("jira_projects").select("*").eq("id", project_id).eq("user_id", user_id).execute()
                if res.data:
                    return res.data[0]
            except Exception as e:
                logger.warning(f"Supabase get_project_by_id failed: {e}")

        for p in self.mock_db.projects:
            if p["id"] == project_id:
                return p
        return None

    def get_project_by_key(self, user_id: str, project_key: str) -> Optional[Dict[str, Any]]:
        """Fetch project by uppercase project key."""
        key = project_key.strip().upper()
        if self.client:
            try:
                res = self.client.table("jira_projects").select("*").eq("project_key", key).eq("user_id", user_id).execute()
                if res.data:
                    return res.data[0]
            except Exception as e:
                logger.warning(f"Supabase get_project_by_key failed: {e}")

        for p in self.mock_db.projects:
            if p.get("project_key", "").upper() == key:
                return p
        return None

    def create_project(self, user_id: str, project_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new Jira project record."""
        key = project_data["project_key"].strip().upper()
        # Verify uniqueness
        existing = self.get_project_by_key(user_id, key)
        if existing:
            raise ValueError(f"Project key '{key}' already exists in your workspace.")

        record = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "project_name": project_data["project_name"].strip(),
            "project_key": key,
            "description": project_data.get("description", "").strip(),
            "team_name": project_data.get("team_name", "").strip(),
            "keywords": project_data.get("keywords", []),
            "is_active": project_data.get("is_active", True),
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
        }

        if self.client:
            try:
                res = self.client.table("jira_projects").insert(record).execute()
                return res.data[0] if res.data else record
            except Exception as e:
                logger.warning(f"Supabase create_project failed, falling back to mock database: {e}")

        self.mock_db.projects.append(record)
        return record

    def update_project(self, user_id: str, project_id: str, update_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update existing Jira project record."""
        update_data["updated_at"] = datetime.now().isoformat()
        if "project_key" in update_data:
            update_data["project_key"] = update_data["project_key"].strip().upper()

        if self.client:
            try:
                res = (
                    self.client.table("jira_projects")
                    .update(update_data)
                    .eq("id", project_id)
                    .eq("user_id", user_id)
                    .execute()
                )
                if res.data:
                    return res.data[0]
            except Exception as e:
                logger.warning(f"Supabase update_project failed: {e}")

        for p in self.mock_db.projects:
            if p["id"] == project_id:
                p.update(update_data)
                return p
        raise ValueError(f"Project with ID '{project_id}' not found.")

    def delete_project(self, user_id: str, project_id: str) -> bool:
        """Delete project by ID."""
        if self.client:
            try:
                self.client.table("jira_projects").delete().eq("id", project_id).eq("user_id", user_id).execute()
                return True
            except Exception as e:
                logger.warning(f"Supabase delete_project failed: {e}")

        initial_len = len(self.mock_db.projects)
        self.mock_db.projects = [p for p in self.mock_db.projects if p["id"] != project_id]
        return len(self.mock_db.projects) < initial_len

    def toggle_active(self, user_id: str, project_id: str, is_active: bool) -> Dict[str, Any]:
        """Toggle active status for classification."""
        return self.update_project(user_id, project_id, {"is_active": is_active})

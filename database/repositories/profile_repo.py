"""
Repository for User Profiles.
"""

from typing import Dict, Any, Optional
from database.supabase_client import get_supabase_client, MockDatabase


class ProfileRepository:
    """Data access layer for User Profiles."""

    def __init__(self, access_token: Optional[str] = None):
        self.client = get_supabase_client(access_token)

    def get_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Fetch profile for user."""
        if self.client:
            res = self.client.table("profiles").select("*").eq("id", user_id).execute()
            return res.data[0] if res.data else None

        return {
            "id": user_id,
            "full_name": "Demo User",
            "email": "demo@minute.ai",
            "created_at": "2026-01-01T00:00:00Z",
        }

    def update_profile(self, user_id: str, full_name: str) -> Optional[Dict[str, Any]]:
        """Update user display name."""
        if self.client:
            res = self.client.table("profiles").update({"full_name": full_name}).eq("id", user_id).execute()
            return res.data[0] if res.data else None
        return {"id": user_id, "full_name": full_name}

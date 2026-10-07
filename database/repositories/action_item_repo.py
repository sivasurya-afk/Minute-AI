"""
Repository for Action Items.
Handles CRUD, filtering, searching, bulk insertion, and dynamic dashboard metrics.
"""

from typing import List, Dict, Any, Optional
import uuid
import logging
from datetime import datetime
from database.supabase_client import get_supabase_client, MockDatabase
from database.repositories.project_repo import ProjectRepository

logger = logging.getLogger(__name__)


class ActionItemRepository:
    """Data access layer for Action Items."""

    def __init__(self, access_token: Optional[str] = None):
        self.client = get_supabase_client(access_token)
        self.mock_db = MockDatabase.get_instance()
        self.project_repo = ProjectRepository(access_token)

    def get_action_items(
        self,
        user_id: str,
        filters: Optional[Dict[str, Any]] = None,
        search: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Fetch action items with enriched meeting and project metadata."""
        items: List[Dict[str, Any]] = []

        if self.client:
            try:
                query = self.client.table("action_items").select(
                    "*, jira_projects(project_name, project_key), transcripts(meeting_name, meeting_date)"
                ).eq("user_id", user_id)

                if filters:
                    if filters.get("project_id"):
                        query = query.eq("project_id", filters["project_id"])
                    if filters.get("assignee"):
                        query = query.ilike("assignee", f"%{filters['assignee']}%")
                    if filters.get("priority"):
                        query = query.eq("priority", filters["priority"])
                    if filters.get("status"):
                        query = query.eq("status", filters["status"])
                    if filters.get("action_type"):
                        query = query.eq("action_type", filters["action_type"])
                    if filters.get("transcript_id"):
                        query = query.eq("transcript_id", filters["transcript_id"])

                res = query.order("created_at", desc=True).execute()
                raw_data = res.data or []

                if raw_data or user_id != "00000000-0000-0000-0000-000000000001":
                    for row in raw_data:
                        jp = row.get("jira_projects") or {}
                        tr = row.get("transcripts") or {}
                        row["project_name"] = jp.get("project_name")
                        row["jira_project_key"] = row.get("jira_project_key") or jp.get("project_key")
                        row["meeting_name"] = tr.get("meeting_name")
                        row["meeting_date"] = tr.get("meeting_date")
                        items.append(row)

                    if search and search.strip():
                        query_str = search.strip().lower()
                        items = [
                            item for item in items
                            if (
                                query_str in (item.get("action_title") or "").lower()
                                or query_str in (item.get("description") or "").lower()
                                or query_str in (item.get("assignee") or "").lower()
                                or query_str in (item.get("source_excerpt") or "").lower()
                                or query_str in (item.get("jira_project_key") or "").lower()
                            )
                        ]
                    return items
            except Exception as e:
                logger.warning(f"Supabase get_action_items failed, falling back to mock database: {e}")

        # Mock fallback
        raw_items = [
            i for i in self.mock_db.action_items
            if (i.get("user_id") == user_id or i.get("user_id") == "00000000-0000-0000-0000-000000000001")
        ]
        # Map relations
        projects_map = {p["id"]: p for p in self.mock_db.projects}
        transcripts_map = {t["id"]: t for t in self.mock_db.transcripts}

        for item in raw_items:
            item_copy = dict(item)
            proj = projects_map.get(item_copy.get("project_id"))
            tran = transcripts_map.get(item_copy.get("transcript_id"))
            if proj:
                item_copy["project_name"] = proj.get("project_name")
                if not item_copy.get("jira_project_key"):
                    item_copy["jira_project_key"] = proj.get("project_key")
            if tran:
                item_copy["meeting_name"] = tran.get("meeting_name")
                item_copy["meeting_date"] = str(tran.get("meeting_date", ""))

            # Apply filters
            if filters:
                if filters.get("project_id") and item_copy.get("project_id") != filters["project_id"]:
                    continue
                if filters.get("assignee") and (filters["assignee"].lower() not in (item_copy.get("assignee") or "").lower()):
                    continue
                if filters.get("priority") and item_copy.get("priority") != filters["priority"]:
                    continue
                if filters.get("status") and item_copy.get("status") != filters["status"]:
                    continue
                if filters.get("action_type") and item_copy.get("action_type") != filters["action_type"]:
                    continue
                if filters.get("transcript_id") and item_copy.get("transcript_id") != filters["transcript_id"]:
                    continue

            items.append(item_copy)

        # Apply text search across title, description, and source excerpt
        if search and search.strip():
            query_str = search.strip().lower()
            items = [
                item for item in items
                if (
                    query_str in (item.get("action_title") or "").lower()
                    or query_str in (item.get("description") or "").lower()
                    or query_str in (item.get("assignee") or "").lower()
                    or query_str in (item.get("source_excerpt") or "").lower()
                    or query_str in (item.get("jira_project_key") or "").lower()
                )
            ]

        return items

    def bulk_create_action_items(
        self,
        user_id: str,
        transcript_id: str,
        items: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Insert a batch of newly extracted action items."""
        now_str = datetime.now().isoformat()
        records_to_insert = []

        for item in items:
            rec = {
                "id": str(uuid.uuid4()),
                "user_id": user_id,
                "transcript_id": transcript_id,
                "project_id": item.get("project_id"),
                "action_title": item.get("action_title", "Untitled Action Item"),
                "description": item.get("description", ""),
                "assignee": item.get("assignee"),
                "priority": item.get("priority"),
                "due_date": item.get("due_date"),
                "action_type": item.get("action_type", "task"),
                "source_excerpt": item.get("source_excerpt", ""),
                "confidence_score": float(item.get("confidence_score", 0.85)),
                "status": "Needs Clarification" if item.get("clarification_required") else "Pending Review",
                "clarification_required": bool(item.get("clarification_required", False)),
                "clarification_reason": item.get("clarification_reason"),
                "created_at": now_str,
                "updated_at": now_str,
            }
            records_to_insert.append(rec)

        if not records_to_insert:
            return []

        if self.client:
            try:
                res = self.client.table("action_items").insert(records_to_insert).execute()
                return res.data or records_to_insert
            except Exception as e:
                logger.warning(f"Supabase bulk_create_action_items failed, falling back to mock database: {e}")

        self.mock_db.action_items.extend(records_to_insert)
        return records_to_insert

    def update_action_item_status(self, user_id: str, item_id: str, new_status: str) -> Dict[str, Any]:
        """Update review status of action item (Pending Review, Approved, Needs Clarification, Rejected)."""
        valid_statuses = {"Pending Review", "Approved", "Needs Clarification", "Rejected"}
        if new_status not in valid_statuses:
            raise ValueError(f"Invalid status: '{new_status}'")

        update_data = {
            "status": new_status,
            "updated_at": datetime.now().isoformat(),
        }
        if new_status == "Approved":
            update_data["clarification_required"] = False

        if self.client:
            try:
                res = (
                    self.client.table("action_items")
                    .update(update_data)
                    .eq("id", item_id)
                    .eq("user_id", user_id)
                    .execute()
                )
                if res.data:
                    return res.data[0]
            except Exception as e:
                logger.warning(f"Supabase update_action_item_status failed: {e}")

        for i in self.mock_db.action_items:
            if i["id"] == item_id:
                i.update(update_data)
                return i
        raise ValueError(f"Action item with ID '{item_id}' not found.")

    def update_action_item_fields(self, user_id: str, item_id: str, fields: Dict[str, Any]) -> Dict[str, Any]:
        """Update editable fields of an action item."""
        fields["updated_at"] = datetime.now().isoformat()

        if self.client:
            try:
                res = (
                    self.client.table("action_items")
                    .update(fields)
                    .eq("id", item_id)
                    .eq("user_id", user_id)
                    .execute()
                )
                if res.data:
                    return res.data[0]
            except Exception as e:
                logger.warning(f"Supabase update_action_item_fields failed: {e}")

        for i in self.mock_db.action_items:
            if i["id"] == item_id:
                i.update(fields)
                return i
        raise ValueError(f"Action item with ID '{item_id}' not found.")

    def delete_action_items_by_transcript(self, user_id: str, transcript_id: str) -> int:
        """Delete all action items associated with a transcript (e.g. during reprocessing)."""
        if self.client:
            try:
                res = (
                    self.client.table("action_items")
                    .delete()
                    .eq("transcript_id", transcript_id)
                    .eq("user_id", user_id)
                    .execute()
                )
                return len(res.data) if res.data else 0
            except Exception as e:
                logger.warning(f"Supabase delete_action_items_by_transcript failed: {e}")

        initial_len = len(self.mock_db.action_items)
        self.mock_db.action_items = [
            i for i in self.mock_db.action_items if i.get("transcript_id") != transcript_id
        ]
        return initial_len - len(self.mock_db.action_items)

    def get_dashboard_metrics(self, user_id: str) -> Dict[str, int]:
        """
        Dynamically calculate main dashboard summary cards:
        1. Total transcripts processed
        2. Total action items extracted
        3. Action items awaiting review
        4. Action items requiring clarification
        5. Number of Jira projects
        6. Number of approved action items
        """
        all_items = self.get_action_items(user_id)
        projects = self.project_repo.get_projects(user_id)

        # Transcripts count
        total_transcripts = 0
        if self.client:
            try:
                res_t = self.client.table("transcripts").select("id", count="exact").eq("user_id", user_id).execute()
                total_transcripts = res_t.count or len(res_t.data or [])
            except Exception as e:
                logger.warning(f"Supabase get_dashboard_metrics transcript count failed: {e}")

        if not total_transcripts:
            total_transcripts = len([
                t for t in self.mock_db.transcripts
                if (t.get("user_id") == user_id or t.get("user_id") == "00000000-0000-0000-0000-000000000001")
            ])

        total_action_items = len(all_items)
        awaiting_review = len([i for i in all_items if i.get("status") == "Pending Review"])
        requiring_clarification = len([i for i in all_items if i.get("status") == "Needs Clarification" or i.get("clarification_required")])
        approved_items = len([i for i in all_items if i.get("status") == "Approved"])
        jira_projects_count = len(projects)

        return {
            "total_transcripts": total_transcripts,
            "total_action_items": total_action_items,
            "awaiting_review": awaiting_review,
            "requiring_clarification": requiring_clarification,
            "jira_projects_count": jira_projects_count,
            "approved_items": approved_items,
        }

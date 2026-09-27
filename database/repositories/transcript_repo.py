"""
Repository for Transcripts.
Operates on Supabase PostgreSQL with automatic fallback to MockDatabase.
"""

from typing import List, Dict, Any, Optional
import uuid
from datetime import datetime, date
from database.supabase_client import get_supabase_client, MockDatabase


class TranscriptRepository:
    """Data access layer for Transcripts."""

    def __init__(self, access_token: Optional[str] = None):
        self.client = get_supabase_client(access_token)
        self.mock_db = MockDatabase.get_instance()

    def get_transcripts(self, user_id: str) -> List[Dict[str, Any]]:
        """Fetch all transcripts owned by user with action item counts."""
        if self.client:
            res = (
                self.client.table("transcripts")
                .select("*, action_items(id, status)")
                .eq("user_id", user_id)
                .order("created_at", desc=True)
                .execute()
            )
            data = res.data or []
            # Calculate action item counts
            for row in data:
                items = row.get("action_items") or []
                row["action_item_count"] = len(items)
                row["approved_count"] = len([i for i in items if i.get("status") == "Approved"])
            return data

        # Mock fallback
        transcripts = [
            t for t in self.mock_db.transcripts
            if (t.get("user_id") == user_id or t.get("user_id") == "00000000-0000-0000-0000-000000000001")
        ]
        result = []
        for t in transcripts:
            t_copy = dict(t)
            matching_items = [
                i for i in self.mock_db.action_items if i.get("transcript_id") == t["id"]
            ]
            t_copy["action_item_count"] = len(matching_items)
            t_copy["approved_count"] = len([i for i in matching_items if i.get("status") == "Approved"])
            result.append(t_copy)

        return sorted(result, key=lambda x: str(x.get("created_at", "")), reverse=True)

    def get_transcript_by_id(self, user_id: str, transcript_id: str) -> Optional[Dict[str, Any]]:
        """Fetch a single transcript by ID."""
        if self.client:
            res = self.client.table("transcripts").select("*").eq("id", transcript_id).eq("user_id", user_id).execute()
            return res.data[0] if res.data else None

        for t in self.mock_db.transcripts:
            if t["id"] == transcript_id:
                return t
        return None

    def find_duplicate(self, user_id: str, meeting_name: str, meeting_date: str) -> Optional[Dict[str, Any]]:
        """Check if a transcript with identical meeting name and date already exists."""
        clean_name = meeting_name.strip().lower()
        if self.client:
            res = (
                self.client.table("transcripts")
                .select("id, meeting_name, meeting_date")
                .eq("user_id", user_id)
                .ilike("meeting_name", clean_name)
                .eq("meeting_date", meeting_date)
                .execute()
            )
            return res.data[0] if res.data else None

        for t in self.mock_db.transcripts:
            if (
                (t.get("user_id") == user_id or t.get("user_id") == "00000000-0000-0000-0000-000000000001")
                and t.get("meeting_name", "").strip().lower() == clean_name
                and str(t.get("meeting_date", "")) == str(meeting_date)
            ):
                return t
        return None

    def create_transcript(self, user_id: str, transcript_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create new transcript record."""
        record = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "meeting_name": transcript_data["meeting_name"].strip(),
            "meeting_date": str(transcript_data.get("meeting_date", date.today().isoformat())),
            "transcript_text": transcript_data["transcript_text"].strip(),
            "source_type": transcript_data.get("source_type", "paste"),
            "processing_status": transcript_data.get("processing_status", "processed"),
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
        }

        if self.client:
            res = self.client.table("transcripts").insert(record).execute()
            return res.data[0] if res.data else record

        self.mock_db.transcripts.append(record)
        return record

    def update_status(self, user_id: str, transcript_id: str, status: str) -> Dict[str, Any]:
        """Update processing status of transcript."""
        update_data = {"processing_status": status, "updated_at": datetime.now().isoformat()}
        if self.client:
            res = (
                self.client.table("transcripts")
                .update(update_data)
                .eq("id", transcript_id)
                .eq("user_id", user_id)
                .execute()
            )
            return res.data[0] if res.data else update_data

        for t in self.mock_db.transcripts:
            if t["id"] == transcript_id:
                t.update(update_data)
                return t
        raise ValueError(f"Transcript with ID '{transcript_id}' not found.")

    def delete_transcript(self, user_id: str, transcript_id: str) -> bool:
        """Delete transcript and cascade delete associated action items."""
        if self.client:
            self.client.table("transcripts").delete().eq("id", transcript_id).eq("user_id", user_id).execute()
            return True

        initial_len = len(self.mock_db.transcripts)
        self.mock_db.transcripts = [t for t in self.mock_db.transcripts if t["id"] != transcript_id]
        # Also clean up action items
        self.mock_db.action_items = [i for i in self.mock_db.action_items if i.get("transcript_id") != transcript_id]
        return len(self.mock_db.transcripts) < initial_len

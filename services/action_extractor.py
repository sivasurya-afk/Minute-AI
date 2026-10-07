"""
AI Action Item Extraction service using Groq LLM and Pydantic validation.
Implements the 13 strict extraction rules, chunking for long transcripts,
semantic project mapping, and controlled retry on validation error.
"""

from typing import List, Dict, Any, Tuple, Optional
import os
import json
import logging
from pydantic import ValidationError
from models.action_item import ActionItemBatch, ActionItemExtraction
from services.groq_service import GroqService, DEFAULT_LLM_MODEL
from services.project_mapper import ProjectMapper
from utils.helpers import deduplicate_extracted_items

logger = logging.getLogger(__name__)

EXTRACTION_SYSTEM_PROMPT = """You are an expert AI Executive Assistant specialized in engineering and product team meetings.
Your sole job is to analyze meeting transcripts, identify explicit actionable commitments and follow-up tasks, map each task to an appropriate Jira project, and output structured JSON.

### STRICT EXTRACTION RULES:
1. Distinguish between explicit commitments vs informal suggestions:
   - ONLY extract actionable items where someone explicitly commits, is assigned, or where a clear follow-up task was agreed upon.
   - DO NOT extract hypothetical ideas, casual opinions, polite chit-chat, or general discussion topics.
   - Do NOT turn every sentence into a task.
2. DO NOT invent assignees. If a task was discussed but not explicitly assigned to a named person, return null for `assignee`.
3. DO NOT invent deadlines or due dates. Only extract if explicitly stated (e.g. 'by Friday', 'October 15th', 'end of sprint'). Otherwise return null.
4. DO NOT invent priorities. Only set priority ('Lowest', 'Low', 'Medium', 'High', 'Highest') if explicitly stated (e.g., 'this is critical/P0', 'high priority') or clearly urgent. Otherwise return null.
5. DO NOT invent Jira project keys. You MUST ONLY pick an exact key from the provided AVAILABLE JIRA PROJECTS list. If you cannot confidently classify the project, return null for `jira_project_key` and set `clarification_required` to true.
6. Provide an exact, verbatim `source_excerpt` from the transcript for every single action item.
7. If a task is missing necessary details (e.g. owner unclear, requirements ambiguous), set `clarification_required` to true and explain why in `clarification_reason`.
8. Avoid duplicate action items.
9. Format output strictly as JSON matching this schema:
{
  "items": [
    {
      "action_title": "Short task title",
      "description": "Detailed task description",
      "assignee": "Person Name or null",
      "jira_project_key": "VALID_KEY or null",
      "priority": "Highest|High|Medium|Low|Lowest or null",
      "due_date": "Date/Timeframe or null",
      "action_type": "bug|feature|investigation|follow-up|task",
      "source_excerpt": "Exact quote from transcript",
      "confidence_score": 0.95,
      "clarification_required": false,
      "clarification_reason": null
    }
  ]
}
"""


class ActionExtractor:
    """Orchestrates AI extraction of action items from meeting transcripts."""

    def __init__(
        self,
        groq_service: Optional[GroqService] = None,
        model: Optional[str] = None,
        confidence_threshold: float = 0.70,
    ):
        self.groq_service = groq_service or GroqService.get_instance()
        self.model = model or os.getenv("GROQ_LLM_MODEL", DEFAULT_LLM_MODEL)
        self.confidence_threshold = confidence_threshold

    def extract_action_items(
        self,
        transcript_text: str,
        active_projects: List[Dict[str, Any]],
        meeting_name: str = "Meeting",
    ) -> Tuple[bool, List[Dict[str, Any]], Optional[str]]:
        """
        Extracts action items from transcript, validates with Pydantic,
        maps to Jira projects, and deduplicates.

        Returns: (success: bool, items: List[Dict], error_message: Optional[str])
        """
        if not transcript_text or not transcript_text.strip():
            return False, [], "Transcript is empty."

        project_mapper = ProjectMapper(active_projects, self.confidence_threshold)
        project_context = project_mapper.generate_classification_prompt_context()

        # Check if chunking is needed (> 5,000 words ~ 7,000 tokens)
        words = transcript_text.split()
        if len(words) > 5000:
            chunks = self._chunk_transcript(transcript_text, max_words_per_chunk=4000)
            logger.info(f"Splitting transcript into {len(chunks)} chunks for processing.")
        else:
            chunks = [transcript_text]

        all_extracted_items: List[Dict[str, Any]] = []

        for chunk_idx, chunk in enumerate(chunks):
            chunk_header = f"[Transcript Segment {chunk_idx + 1} of {len(chunks)} for '{meeting_name}']"
            user_prompt = (
                f"{chunk_header}\n\n"
                f"{project_context}\n\n"
                f"MEETING TRANSCRIPT:\n\"\"\"\n{chunk}\n\"\"\"\n\n"
                "Extract all actionable tasks following all 13 extraction rules. "
                "Respond with valid JSON containing the 'items' array."
            )

            success, items, err = self._extract_chunk_with_retry(user_prompt)
            if not success:
                # If a chunk fails, log and continue or return error if only 1 chunk
                if len(chunks) == 1:
                    return False, [], err
                logger.warning(f"Chunk {chunk_idx + 1} failed: {err}")
            else:
                all_extracted_items.extend(items)

        # Validate projects and link project_ids
        processed_items = []
        for item in all_extracted_items:
            linked_item = project_mapper.validate_and_link_project(item)
            processed_items.append(linked_item)

        # Deduplicate across chunks and intra-transcript
        deduped_items = deduplicate_extracted_items(processed_items)

        return True, deduped_items, None

    def _extract_chunk_with_retry(self, user_prompt: str) -> Tuple[bool, List[Dict[str, Any]], Optional[str]]:
        """
        Calls Groq API to extract action items with automated 1-turn retry on validation failure.
        """
        messages = [
            {"role": "system", "content": EXTRACTION_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ]

        # Initial call
        try:
            raw_response = self.groq_service.chat_completion_json(messages, model=self.model)
        except Exception as e:
            return False, [], f"Groq API call error: {str(e)}"

        # Validate with Pydantic
        validation_error = None
        try:
            batch = ActionItemBatch.model_validate(raw_response)
            return True, [item.model_dump() for item in batch.items], None
        except (ValidationError, TypeError, ValueError) as ve:
            validation_error = str(ve)
            logger.warning(f"Initial validation failed: {ve}. Attempting controlled self-correction retry...")

        # Controlled retry: provide the error back to the model
        retry_messages = list(messages)
        retry_messages.append({"role": "assistant", "content": json.dumps(raw_response)})
        retry_messages.append({
            "role": "user",
            "content": (
                f"The previous output was invalid and failed Pydantic schema validation:\n{validation_error}\n\n"
                "Please fix the format and re-generate ONLY the corrected valid JSON containing the 'items' array."
            )
        })

        try:
            retry_response = self.groq_service.chat_completion_json(retry_messages, model=self.model)
            batch = ActionItemBatch.model_validate(retry_response)
            return True, [item.model_dump() for item in batch.items], None
        except Exception as retry_err:
            logger.error(f"Retry validation failed: {retry_err}")
            return False, [], f"Schema validation error after retry: {str(retry_err)}"

    def _chunk_transcript(self, text: str, max_words_per_chunk: int = 4000) -> List[str]:
        """
        Split a long transcript on speaker boundaries or double newlines into overlapping chunks.
        """
        paragraphs = text.split("\n\n")
        chunks: List[str] = []
        current_chunk: List[str] = []
        current_words = 0

        for para in paragraphs:
            para_words = len(para.split())
            if current_words + para_words > max_words_per_chunk and current_chunk:
                chunks.append("\n\n".join(current_chunk))
                # 1 paragraph overlap for context continuity
                current_chunk = [current_chunk[-1], para] if len(current_chunk) > 1 else [para]
                current_words = sum(len(p.split()) for p in current_chunk)
            else:
                current_chunk.append(para)
                current_words += para_words

        if current_chunk:
            chunks.append("\n\n".join(current_chunk))

        return chunks if chunks else [text]


def generate_offline_extracted_items(text: str, active_projects: list) -> list:
    """Generate deterministic parsed items when running in demo/offline mode without Groq key."""
    import re
    items = []
    lines = text.split("\n")

    proj_map = {p["project_key"]: p for p in active_projects}
    keys = list(proj_map.keys())

    for line in lines:
        line_clean = line.strip()
        commitment_match = re.search(r"(?:([A-Z][a-zA-Z0-9_\s]+):)?.*?\b(I will|I'll|will|shall|can you)\s+([^\.]+)", line_clean, re.IGNORECASE)
        if commitment_match:
            speaker = (commitment_match.group(1) or "").strip() or None
            task_desc = commitment_match.group(3).strip()

            assigned_key = None
            assigned_id = None
            task_lower = task_desc.lower()

            for p in active_projects:
                for kw in p.get("keywords", []):
                    if kw.lower() in task_lower:
                        assigned_key = p["project_key"]
                        assigned_id = p["id"]
                        break
                if assigned_key:
                    break

            if not assigned_key and keys:
                assigned_key = keys[0]
                assigned_id = proj_map[keys[0]]["id"]

            items.append({
                "action_title": task_desc.capitalize()[:80],
                "description": f"Extracted task from discussion: {task_desc}.",
                "assignee": speaker,
                "project_id": assigned_id,
                "jira_project_key": assigned_key,
                "priority": "High" if "urgent" in task_lower or "critical" in task_lower else "Medium",
                "due_date": "This Sprint",
                "action_type": "bug" if "bug" in task_lower or "fix" in task_lower else "task",
                "source_excerpt": line_clean,
                "confidence_score": 0.90 if assigned_key else 0.65,
                "clarification_required": not bool(assigned_key),
                "clarification_reason": None if assigned_key else "Could not confidently map to active projects.",
            })

    if not items:
        items.append({
            "action_title": "Review meeting minutes and action items",
            "description": "Follow up on discussion points highlighted during the meeting.",
            "assignee": None,
            "project_id": active_projects[0]["id"] if active_projects else None,
            "jira_project_key": active_projects[0]["project_key"] if active_projects else None,
            "priority": "Medium",
            "due_date": None,
            "action_type": "follow-up",
            "source_excerpt": text[:120],
            "confidence_score": 0.80,
            "clarification_required": True,
            "clarification_reason": "No explicit owner assigned in discussion.",
        })

    return items


_generate_offline_extracted_items = generate_offline_extracted_items


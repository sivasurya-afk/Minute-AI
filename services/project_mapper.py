"""
Jira Project mapping and semantic classification service.
Provides context prompt formatting and validates LLM project classification results.
"""

from typing import List, Dict, Any, Optional
import os
import logging
from models.jira_project import JiraProjectRecord

logger = logging.getLogger(__name__)
DEFAULT_CONFIDENCE_THRESHOLD = 0.70


class ProjectMapper:
    """Handles mapping of extracted action items to configured Jira projects."""

    def __init__(self, projects: List[Dict[str, Any]], confidence_threshold: Optional[float] = None):
        """
        Initialize with active Jira projects list.
        Each project should contain id, project_name, project_key, description, team_name, keywords.
        """
        self.projects = projects
        self.confidence_threshold = (
            confidence_threshold
            if confidence_threshold is not None
            else float(os.getenv("CONFIDENCE_THRESHOLD", DEFAULT_CONFIDENCE_THRESHOLD))
        )
        self.key_to_project_map = {
            p["project_key"].upper(): p for p in projects if p.get("project_key")
        }

    def generate_classification_prompt_context(self) -> str:
        """
        Format active Jira projects into a structured prompt section for the LLM.
        """
        if not self.projects:
            return (
                "NO ACTIVE JIRA PROJECTS ARE CONFIGURED.\n"
                "You must set `jira_project_key` to null and mark `clarification_required` as true "
                "with clarification_reason: 'No configured Jira project exists for this task.'"
            )

        context_lines = [
            "AVAILABLE JIRA PROJECTS (You MUST choose ONLY from these project keys or return null):"
        ]

        for p in self.projects:
            key = p.get("project_key", "").upper()
            name = p.get("project_name", "")
            desc = p.get("description", "No description provided.")
            team = p.get("team_name", "General")
            keywords = p.get("keywords", [])
            kw_str = ", ".join(keywords) if isinstance(keywords, list) else str(keywords)

            context_lines.append(f"- Key: [{key}] | Name: {name} (Team: {team})")
            context_lines.append(f"  Description: {desc}")
            if kw_str:
                context_lines.append(f"  Keywords/Tags: {kw_str}")

        context_lines.append(
            "\nCLASSIFICATION RULES:\n"
            "1. Match the task to the most semantically relevant project based on its scope, keywords, and description.\n"
            "2. If none of the above projects are a confident fit (confidence < 0.70), return null for `jira_project_key` "
            "and set `clarification_required` to true.\n"
            "3. NEVER invent or fabricate a Jira project key."
        )

        return "\n".join(context_lines)

    def validate_and_link_project(self, action_item: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validates the extracted project key against active projects and attaches project_id.
        Enforces confidence thresholds and flags for clarification if needed.
        """
        extracted_key = action_item.get("jira_project_key")
        confidence = float(action_item.get("confidence_score", 0.85))

        if not extracted_key:
            action_item["project_id"] = None
            action_item["jira_project_key"] = None
            if not action_item.get("clarification_required"):
                action_item["clarification_required"] = True
                action_item["clarification_reason"] = "Could not confidently map to any configured Jira project."
            return action_item

        normalized_key = extracted_key.strip().upper()

        if normalized_key in self.key_to_project_map:
            matched_project = self.key_to_project_map[normalized_key]
            action_item["project_id"] = matched_project.get("id")
            action_item["jira_project_key"] = normalized_key
            action_item["project_name"] = matched_project.get("project_name")

            # Check confidence cutoff
            if confidence < self.confidence_threshold:
                action_item["clarification_required"] = True
                if not action_item.get("clarification_reason"):
                    action_item["clarification_reason"] = (
                        f"Low classification confidence ({confidence:.2f} < {self.confidence_threshold:.2f}) "
                        f"for project '{normalized_key}'."
                    )
        else:
            # LLM hallucinated or returned an invalid project key
            action_item["project_id"] = None
            action_item["jira_project_key"] = None
            action_item["clarification_required"] = True
            action_item["clarification_reason"] = (
                f"Proposed project key '{extracted_key}' does not match any active Jira projects."
            )

        return action_item

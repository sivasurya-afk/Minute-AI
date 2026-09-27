"""
Pydantic data models for Action Items.
Includes models for AI structured extraction, validation, and database records.
"""

from typing import Optional, List, Literal
from datetime import datetime
from pydantic import BaseModel, Field, field_validator


ActionTypeLiteral = Literal["bug", "feature", "investigation", "follow-up", "task"]
PriorityLiteral = Literal["Lowest", "Low", "Medium", "High", "Highest"]
StatusLiteral = Literal["Pending Review", "Approved", "Needs Clarification", "Rejected"]


class ActionItemExtraction(BaseModel):
    """Structured action item extracted by LLM from meeting transcripts."""
    action_title: str = Field(
        ...,
        description="Concise, imperative task title (e.g., 'Migrate auth service to JWT tokens')"
    )
    description: str = Field(
        ...,
        description="Detailed description including background, context, and clear expected outcome"
    )
    assignee: Optional[str] = Field(
        None,
        description="Name of the person explicitly assigned or committing to the task. If unknown or unassigned, return null."
    )
    jira_project_key: Optional[str] = Field(
        None,
        description="Matching Jira project key from available list (e.g. 'FRONT', 'BACK'). If cannot confidently map, return null."
    )
    priority: Optional[PriorityLiteral] = Field(
        None,
        description="Task priority if explicitly mentioned or clearly urgent ('Lowest', 'Low', 'Medium', 'High', 'Highest'). Else null."
    )
    due_date: Optional[str] = Field(
        None,
        description="Due date or deadline if explicitly mentioned (e.g., '2026-10-05', 'End of Sprint 3'). If not mentioned, return null."
    )
    action_type: ActionTypeLiteral = Field(
        default="task",
        description="Classification of the action item: bug, feature, investigation, follow-up, or task"
    )
    source_excerpt: str = Field(
        ...,
        description="Exact verbatim quote or sentence from the transcript that directly triggered this action item"
    )
    confidence_score: float = Field(
        default=0.85,
        ge=0.0,
        le=1.0,
        description="Confidence score between 0.0 and 1.0 regarding the accuracy of extraction and project mapping"
    )
    clarification_required: bool = Field(
        default=False,
        description="True if the task is ambiguous, missing critical details, or project mapping is uncertain"
    )
    clarification_reason: Optional[str] = Field(
        None,
        description="Explanation of what needs clarification if clarification_required is True"
    )

    @field_validator("assignee", "due_date", "jira_project_key", mode="before")
    @classmethod
    def clean_empty_strings(cls, v):
        if isinstance(v, str):
            v_stripped = v.strip()
            if not v_stripped or v_stripped.lower() in ("null", "none", "n/a", "unknown", "unassigned"):
                return None
            return v_stripped
        return v

    @field_validator("action_title", "description", "source_excerpt", mode="before")
    @classmethod
    def strip_text(cls, v):
        if isinstance(v, str):
            return v.strip()
        return v


class ActionItemBatch(BaseModel):
    """Batch container for structured output from Groq LLM."""
    items: List[ActionItemExtraction] = Field(
        default_factory=list,
        description="List of extracted actionable items. Return empty list if no clear commitments or tasks exist."
    )


class ActionItemRecord(ActionItemExtraction):
    """Full database record representation for an action item."""
    id: str
    user_id: str
    transcript_id: str
    project_id: Optional[str] = None
    status: StatusLiteral = "Pending Review"
    project_name: Optional[str] = None
    meeting_name: Optional[str] = None
    meeting_date: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

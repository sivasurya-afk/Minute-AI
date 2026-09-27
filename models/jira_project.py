"""
Pydantic data models for Jira Projects.
Used for classification context and project management.
"""

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, field_validator


class JiraProjectBase(BaseModel):
    project_name: str = Field(..., min_length=1, max_length=100, description="Display name of the Jira project")
    project_key: str = Field(..., min_length=1, max_length=20, description="Uppercase Jira key, e.g., 'FRONT', 'CORE'")
    description: Optional[str] = Field(None, description="Detailed scope of the project for LLM classification")
    team_name: Optional[str] = Field(None, description="Team or department managing this project")
    keywords: List[str] = Field(default_factory=list, description="Keywords and tags associated with this project")
    is_active: bool = Field(default=True, description="Whether this project is active for AI classification")

    @field_validator("project_key")
    @classmethod
    def format_project_key(cls, v: str) -> str:
        key = v.strip().upper()
        if not key.replace("-", "").isalnum():
            raise ValueError("Project key must contain only letters, numbers, and hyphens.")
        return key

    @field_validator("project_name")
    @classmethod
    def clean_name(cls, v: str) -> str:
        name = v.strip()
        if not name:
            raise ValueError("Project name cannot be empty.")
        return name


class JiraProjectCreate(JiraProjectBase):
    pass


class JiraProjectUpdate(BaseModel):
    project_name: Optional[str] = None
    project_key: Optional[str] = None
    description: Optional[str] = None
    team_name: Optional[str] = None
    keywords: Optional[List[str]] = None
    is_active: Optional[bool] = None


class JiraProjectRecord(JiraProjectBase):
    id: str
    user_id: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

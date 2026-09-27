"""
Pydantic data models for Transcripts.
"""

from typing import Optional, Literal
from datetime import datetime, date
from pydantic import BaseModel, Field, field_validator


SourceTypeLiteral = Literal["paste", "txt", "vtt", "srt", "audio"]
ProcessingStatusLiteral = Literal["pending", "processed", "failed"]


class TranscriptBase(BaseModel):
    meeting_name: str = Field(..., min_length=1, max_length=200, description="Title of the meeting")
    meeting_date: date = Field(default_factory=date.today, description="Date the meeting occurred")
    transcript_text: str = Field(..., min_length=1, description="Raw or parsed transcript text content")
    source_type: SourceTypeLiteral = Field(default="paste", description="Input source format")
    processing_status: ProcessingStatusLiteral = Field(default="processed", description="Status of extraction")

    @field_validator("meeting_name")
    @classmethod
    def clean_title(cls, v: str) -> str:
        name = v.strip()
        if not name:
            raise ValueError("Meeting name cannot be empty.")
        return name


class TranscriptCreate(TranscriptBase):
    pass


class TranscriptRecord(TranscriptBase):
    id: str
    user_id: str
    action_item_count: int = 0
    approved_count: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

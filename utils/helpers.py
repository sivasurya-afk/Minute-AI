"""
Presentation, formatting, and deduplication helper functions for Minute AI.
"""

from typing import List, Dict, Any, Optional
import hashlib
import re
from datetime import datetime


def compute_content_hash(text: str) -> str:
    """Compute SHA-256 hash of normalized text for duplicate detection."""
    normalized = re.sub(r"\s+", " ", text.strip().lower())
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def get_status_badge(status: str) -> str:
    """Return HTML badge snippet with modern styling for task status."""
    status_map = {
        "Pending Review": {"bg": "#FEF3C7", "text": "#92400E", "border": "#FCD34D"},
        "Approved": {"bg": "#D1FAE5", "text": "#065F46", "border": "#6EE7B7"},
        "Needs Clarification": {"bg": "#E0E7FF", "text": "#3730A3", "border": "#A5B4FC"},
        "Rejected": {"bg": "#FEE2E2", "text": "#991B1B", "border": "#FCA5A5"},
    }
    style = status_map.get(status, {"bg": "#F3F4F6", "text": "#374151", "border": "#D1D5DB"})
    return (
        f'<span style="background-color: {style["bg"]}; color: {style["text"]}; '
        f'border: 1px solid {style["border"]}; padding: 3px 8px; border-radius: 9999px; '
        f'font-size: 0.78rem; font-weight: 600; display: inline-block;">'
        f'{status}</span>'
    )


def get_priority_badge(priority: Optional[str]) -> str:
    """Return HTML badge snippet for task priority."""
    if not priority:
        return '<span style="color: #9CA3AF; font-size: 0.8rem;">—</span>'

    priority_map = {
        "Highest": {"bg": "#FEE2E2", "text": "#991B1B", "border": "#EF4444"},
        "High": {"bg": "#FFEDD5", "text": "#9A3412", "border": "#F97316"},
        "Medium": {"bg": "#FEF9C3", "text": "#854D0E", "border": "#EAB308"},
        "Low": {"bg": "#E0F2FE", "text": "#075985", "border": "#38BDF8"},
        "Lowest": {"bg": "#F3F4F6", "text": "#4B5563", "border": "#9CA3AF"},
    }
    style = priority_map.get(priority, {"bg": "#F3F4F6", "text": "#4B5563", "border": "#9CA3AF"})
    return (
        f'<span style="background-color: {style["bg"]}; color: {style["text"]}; '
        f'border: 1px solid {style["border"]}; padding: 2px 7px; border-radius: 6px; '
        f'font-size: 0.75rem; font-weight: 600;">'
        f'{priority}</span>'
    )


def get_type_badge(action_type: str) -> str:
    """Return HTML badge snippet for action item type."""
    type_map = {
        "bug": {"bg": "#FEE2E2", "text": "#B91C1C", "icon": "🐛"},
        "feature": {"bg": "#DCFCE7", "text": "#15803D", "icon": "✨"},
        "investigation": {"bg": "#F3E8FF", "text": "#6B21A8", "icon": "🔍"},
        "follow-up": {"bg": "#E0F2FE", "text": "#0369A1", "icon": "📌"},
        "task": {"bg": "#F1F5F9", "text": "#475569", "icon": "📋"},
    }
    style = type_map.get(action_type, {"bg": "#F1F5F9", "text": "#475569", "icon": "📋"})
    return (
        f'<span style="background-color: {style["bg"]}; color: {style["text"]}; '
        f'padding: 2px 7px; border-radius: 6px; font-size: 0.75rem; font-weight: 500;">'
        f'{style["icon"]} {action_type}</span>'
    )


def calculate_jaccard_similarity(text1: str, text2: str) -> float:
    """Calculate token-level Jaccard similarity between two texts."""
    words1 = set(re.findall(r"\w+", text1.lower()))
    words2 = set(re.findall(r"\w+", text2.lower()))
    if not words1 or not words2:
        return 0.0
    intersection = len(words1.intersection(words2))
    union = len(words1.union(words2))
    return intersection / union if union > 0 else 0.0


def deduplicate_extracted_items(items: List[Dict[str, Any]], threshold: float = 0.75) -> List[Dict[str, Any]]:
    """
    Deduplicates a list of extracted action items based on title and excerpt similarity.
    Keeps the item with the higher confidence score.
    """
    if len(items) <= 1:
        return items

    unique_items: List[Dict[str, Any]] = []

    for item in items:
        is_duplicate = False
        title = item.get("action_title", "")
        excerpt = item.get("source_excerpt", "")

        for idx, existing in enumerate(unique_items):
            existing_title = existing.get("action_title", "")
            existing_excerpt = existing.get("source_excerpt", "")

            title_sim = calculate_jaccard_similarity(title, existing_title)
            excerpt_sim = calculate_jaccard_similarity(excerpt, existing_excerpt)

            # If titles or source excerpts are sufficiently similar
            if title_sim >= threshold or excerpt_sim >= 0.85:
                is_duplicate = True
                # Keep the one with the higher confidence score or more detailed description
                if item.get("confidence_score", 0) > existing.get("confidence_score", 0):
                    unique_items[idx] = item
                break

        if not is_duplicate:
            unique_items.append(item)

    return unique_items


def format_iso_date(date_val: Any) -> str:
    """Format any date representation nicely for display."""
    if not date_val:
        return "—"
    if isinstance(date_val, datetime):
        return date_val.strftime("%b %d, %Y")
    if isinstance(date_val, str):
        try:
            parsed = datetime.fromisoformat(date_val.replace("Z", "+00:00"))
            return parsed.strftime("%b %d, %Y")
        except Exception:
            return date_val
    return str(date_val)

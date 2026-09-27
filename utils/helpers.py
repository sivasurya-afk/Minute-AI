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
    """Return HTML badge snippet with modern dark-slate SaaS styling for task status."""
    status_map = {
        "Pending Review": {"bg": "rgba(245, 158, 11, 0.12)", "text": "#FBBF24", "border": "rgba(245, 158, 11, 0.35)", "dot": "#F59E0B"},
        "Approved": {"bg": "rgba(16, 185, 129, 0.12)", "text": "#34D399", "border": "rgba(16, 185, 129, 0.35)", "dot": "#10B981"},
        "Needs Clarification": {"bg": "rgba(99, 102, 241, 0.12)", "text": "#A5B4FC", "border": "rgba(99, 102, 241, 0.35)", "dot": "#6366F1"},
        "Rejected": {"bg": "rgba(244, 63, 94, 0.12)", "text": "#FB7185", "border": "rgba(244, 63, 94, 0.35)", "dot": "#F43F5E"},
    }
    style = status_map.get(status, {"bg": "rgba(148, 163, 184, 0.12)", "text": "#CBD5E1", "border": "rgba(148, 163, 184, 0.3)", "dot": "#94A3B8"})
    return (
        f'<span style="background: {style["bg"]}; color: {style["text"]}; '
        f'border: 1px solid {style["border"]}; padding: 3px 9px; border-radius: 9999px; '
        f'font-size: 0.75rem; font-weight: 600; letter-spacing: 0.02em; display: inline-flex; align-items: center; gap: 5px; box-shadow: 0 1px 2px rgba(0,0,0,0.2);">'
        f'<span style="width: 6px; height: 6px; border-radius: 50%; background-color: {style["dot"]}; box-shadow: 0 0 6px {style["dot"]}; display: inline-block;"></span>'
        f'{status}</span>'
    )


def get_priority_badge(priority: Optional[str]) -> str:
    """Return HTML badge snippet for task priority."""
    if not priority:
        return '<span style="color: #64748B; font-size: 0.8rem;">—</span>'

    priority_map = {
        "Highest": {"bg": "rgba(239, 68, 68, 0.15)", "text": "#F87171", "border": "rgba(239, 68, 68, 0.35)", "dot": "#EF4444"},
        "High": {"bg": "rgba(249, 115, 22, 0.15)", "text": "#FB923C", "border": "rgba(249, 115, 22, 0.35)", "dot": "#F97316"},
        "Medium": {"bg": "rgba(234, 179, 8, 0.15)", "text": "#FACC15", "border": "rgba(234, 179, 8, 0.35)", "dot": "#EAB308"},
        "Low": {"bg": "rgba(59, 130, 246, 0.15)", "text": "#60A5FA", "border": "rgba(59, 130, 246, 0.35)", "dot": "#3B82F6"},
        "Lowest": {"bg": "rgba(148, 163, 184, 0.12)", "text": "#94A3B8", "border": "rgba(148, 163, 184, 0.25)", "dot": "#64748B"},
    }
    style = priority_map.get(priority, {"bg": "rgba(148, 163, 184, 0.12)", "text": "#94A3B8", "border": "rgba(148, 163, 184, 0.25)", "dot": "#64748B"})
    return (
        f'<span style="background: {style["bg"]}; color: {style["text"]}; '
        f'border: 1px solid {style["border"]}; padding: 2px 8px; border-radius: 6px; '
        f'font-size: 0.73rem; font-weight: 600; display: inline-flex; align-items: center; gap: 4px;">'
        f'<span style="width: 5px; height: 5px; border-radius: 50%; background-color: {style["dot"]};"></span>'
        f'{priority}</span>'
    )


def get_type_badge(action_type: str) -> str:
    """Return HTML badge snippet for action item type."""
    type_map = {
        "bug": {"bg": "rgba(239, 68, 68, 0.12)", "text": "#FCA5A5", "border": "rgba(239, 68, 68, 0.25)", "icon": "🐛"},
        "feature": {"bg": "rgba(16, 185, 129, 0.12)", "text": "#6EE7B7", "border": "rgba(16, 185, 129, 0.25)", "icon": "✨"},
        "investigation": {"bg": "rgba(168, 85, 247, 0.12)", "text": "#D8B4FE", "border": "rgba(168, 85, 247, 0.25)", "icon": "🔍"},
        "follow-up": {"bg": "rgba(56, 189, 248, 0.12)", "text": "#7DD3FC", "border": "rgba(56, 189, 248, 0.25)", "icon": "📌"},
        "task": {"bg": "rgba(148, 163, 184, 0.12)", "text": "#CBD5E1", "border": "rgba(148, 163, 184, 0.25)", "icon": "📋"},
    }
    style = type_map.get(action_type, {"bg": "rgba(148, 163, 184, 0.12)", "text": "#CBD5E1", "border": "rgba(148, 163, 184, 0.25)", "icon": "📋"})
    return (
        f'<span style="background: {style["bg"]}; color: {style["text"]}; border: 1px solid {style["border"]}; '
        f'padding: 2px 8px; border-radius: 6px; font-size: 0.73rem; font-weight: 500; display: inline-flex; align-items: center; gap: 4px;">'
        f'{style["icon"]} {action_type}</span>'
    )


def get_confidence_badge(score: float) -> str:
    """Return HTML badge snippet with visual progress bar for AI confidence score."""
    pct = int(score * 100) if score <= 1.0 else int(score)
    if pct >= 85:
        color = "#10B981"
        bg = "rgba(16, 185, 129, 0.12)"
    elif pct >= 70:
        color = "#F59E0B"
        bg = "rgba(245, 158, 11, 0.12)"
    else:
        color = "#EF4444"
        bg = "rgba(239, 68, 68, 0.12)"

    return (
        f'<div style="display: inline-flex; align-items: center; gap: 6px; background: {bg}; padding: 2px 7px; border-radius: 6px; font-size: 0.72rem; font-weight: 600; color: {color}; border: 1px solid {color}33;">'
        f'<span>AI {pct}%</span>'
        f'<div style="width: 28px; height: 4px; background: rgba(255,255,255,0.1); border-radius: 2px; overflow: hidden;">'
        f'<div style="width: {pct}%; height: 100%; background: {color};"></div>'
        f'</div></div>'
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

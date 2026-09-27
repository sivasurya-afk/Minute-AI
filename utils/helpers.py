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
    """Return HTML badge snippet matching Stitch Executive Precision design system."""
    status_map = {
        "Pending Review": {"bg": "#FFFBEB", "text": "#92400E", "border": "#FDE68A", "dot": "#F59E0B"},
        "Approved": {"bg": "#ECFDF5", "text": "#065F46", "border": "#A7F3D0", "dot": "#10B981"},
        "Needs Clarification": {"bg": "#EEF2FF", "text": "#3730A3", "border": "#C7D2FE", "dot": "#6366F1"},
        "Rejected": {"bg": "#FEF2F2", "text": "#991B1B", "border": "#FECACA", "dot": "#EF4444"},
    }
    style = status_map.get(status, {"bg": "#F3F4F6", "text": "#4B5563", "border": "#E5E7EB", "dot": "#9CA3AF"})
    return (
        f'<span style="background: {style["bg"]}; color: {style["text"]}; '
        f'border: 1px solid {style["border"]}; padding: 3px 9px; border-radius: 9999px; '
        f'font-size: 0.75rem; font-weight: 600; letter-spacing: 0.02em; display: inline-flex; align-items: center; gap: 5px; box-shadow: 0 1px 2px rgba(0,0,0,0.03);">'
        f'<span style="width: 6px; height: 6px; border-radius: 50%; background-color: {style["dot"]}; display: inline-block;"></span>'
        f'{status}</span>'
    )


def get_priority_badge(priority: Optional[str]) -> str:
    """Return HTML badge snippet for task priority."""
    if not priority:
        return '<span style="color: #9CA3AF; font-size: 0.8rem;">—</span>'

    priority_map = {
        "Highest": {"bg": "#FEF2F2", "text": "#DC2626", "border": "#FCA5A5", "dot": "#EF4444"},
        "High": {"bg": "#FFF7ED", "text": "#C2410C", "border": "#FDBA74", "dot": "#F97316"},
        "Medium": {"bg": "#FEFCE8", "text": "#A16207", "border": "#FDE047", "dot": "#EAB308"},
        "Low": {"bg": "#F0F9FF", "text": "#0369A1", "border": "#BAE6FD", "dot": "#0EA5E9"},
        "Lowest": {"bg": "#F8FAFC", "text": "#475569", "border": "#E2E8F0", "dot": "#94A3B8"},
    }
    style = priority_map.get(priority, {"bg": "#F8FAFC", "text": "#475569", "border": "#E2E8F0", "dot": "#94A3B8"})
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
        "bug": {"bg": "#FEF2F2", "text": "#991B1B", "border": "#FECACA", "icon": "🐛"},
        "feature": {"bg": "#ECFDF5", "text": "#065F46", "border": "#A7F3D0", "icon": "✨"},
        "investigation": {"bg": "#FAF5FF", "text": "#6B21A8", "border": "#E9D5FF", "icon": "🔍"},
        "follow-up": {"bg": "#F0F9FF", "text": "#0369A1", "border": "#BAE6FD", "icon": "📌"},
        "task": {"bg": "#F1F5F9", "text": "#334155", "border": "#E2E8F0", "icon": "📋"},
    }
    style = type_map.get(action_type, {"bg": "#F1F5F9", "text": "#334155", "border": "#E2E8F0", "icon": "📋"})
    return (
        f'<span style="background: {style["bg"]}; color: {style["text"]}; border: 1px solid {style["border"]}; '
        f'padding: 2px 8px; border-radius: 6px; font-size: 0.73rem; font-weight: 500; display: inline-flex; align-items: center; gap: 4px;">'
        f'{style["icon"]} {action_type}</span>'
    )


def get_confidence_badge(score: float) -> str:
    """Return HTML badge snippet with visual progress bar for AI confidence score."""
    pct = int(score * 100) if score <= 1.0 else int(score)
    if pct >= 85:
        color = "#059669"
        bg = "#ECFDF5"
        border = "#A7F3D0"
    elif pct >= 70:
        color = "#D97706"
        bg = "#FFFBEB"
        border = "#FDE68A"
    else:
        color = "#DC2626"
        bg = "#FEF2F2"
        border = "#FECACA"

    return (
        f'<div style="display: inline-flex; align-items: center; gap: 6px; background: {bg}; padding: 2px 7px; border-radius: 6px; font-size: 0.72rem; font-weight: 600; color: {color}; border: 1px solid {border};">'
        f'<span>AI {pct}%</span>'
        f'<div style="width: 26px; height: 4px; background: rgba(0,0,0,0.08); border-radius: 2px; overflow: hidden;">'
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

from fastapi import APIRouter, Header
from typing import Optional, Dict, Any, List
from collections import Counter
from database.repositories import ActionItemRepository, ProjectRepository, TranscriptRepository
from utils.auth import DEMO_USER

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])

def get_user_id(authorization: Optional[str] = Header(None)) -> str:
    if not authorization or "demo" in authorization.lower():
        return DEMO_USER["id"]
    return DEMO_USER["id"]

@router.get("/summary")
def get_dashboard_summary(authorization: Optional[str] = Header(None)):
    user_id = get_user_id(authorization)
    a_repo = ActionItemRepository()
    p_repo = ProjectRepository()
    t_repo = TranscriptRepository()

    all_items = a_repo.get_action_items(user_id)
    all_projects = p_repo.get_projects(user_id)
    transcripts = t_repo.get_transcripts(user_id)

    metrics = {
        "total_transcripts": len(transcripts),
        "total_action_items": len(all_items),
        "awaiting_review": len([i for i in all_items if i.get("status") == "Pending Review"]),
        "requiring_clarification": len([i for i in all_items if i.get("status") == "Needs Clarification" or i.get("clarification_required")]),
        "jira_projects_count": len(all_projects),
        "approved_items": len([i for i in all_items if i.get("status") == "Approved"]),
    }

    # Calculate chart breakdowns
    # 1. By Project
    project_counts = Counter()
    for item in all_items:
        key = item.get("jira_project_key") or "Unassigned"
        project_counts[key] += 1
    by_project = [{"project": k, "count": v} for k, v in project_counts.most_common()]

    # 2. By Status
    status_counts = Counter()
    for item in all_items:
        st_val = item.get("status") or "Pending Review"
        status_counts[st_val] += 1
    by_status = [{"status": k, "count": v} for k, v in status_counts.items()]

    # 3. By Priority
    priority_order = ["Highest", "High", "Medium", "Low", "Lowest", "Unspecified"]
    p_counts = Counter()
    for item in all_items:
        p_val = item.get("priority") or "Unspecified"
        p_counts[p_val] += 1
    by_priority = [{"priority": p, "count": p_counts[p]} for p in priority_order if p_counts[p] > 0]

    # 4. Over Time
    date_counts = Counter()
    for item in all_items:
        created = item.get("created_at")
        date_str = str(created)[:10] if created else "Unknown"
        date_counts[date_str] += 1
    by_time = [{"date": k, "count": v} for k, v in sorted(date_counts.items())]

    # Recent transcripts (first 5)
    recent_transcripts = transcripts[:5]

    return {
        "metrics": metrics,
        "charts": {
            "by_project": by_project,
            "by_status": by_status,
            "by_priority": by_priority,
            "by_time": by_time,
        },
        "recent_transcripts": recent_transcripts,
    }

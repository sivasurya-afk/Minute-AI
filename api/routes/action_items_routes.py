from fastapi import APIRouter, HTTPException, Header, Query
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from database.repositories import ActionItemRepository
from utils.auth import DEMO_USER

router = APIRouter(prefix="/api/action-items", tags=["action_items"])

def get_user_id(authorization: Optional[str] = Header(None)) -> str:
    if not authorization or "demo" in authorization.lower():
        return DEMO_USER["id"]
    return DEMO_USER["id"]

class UpdateFieldsRequest(BaseModel):
    action_title: Optional[str] = None
    description: Optional[str] = None
    assignee: Optional[str] = None
    jira_project_key: Optional[str] = None
    priority: Optional[str] = None
    due_date: Optional[str] = None
    status: Optional[str] = None

class StatusUpdateRequest(BaseModel):
    status: str

@router.get("")
def list_action_items(
    authorization: Optional[str] = Header(None),
    search: Optional[str] = None,
    project_key: Optional[str] = None,
    assignee: Optional[str] = None,
    priority: Optional[str] = None,
    status: Optional[str] = None,
    action_type: Optional[str] = None,
    transcript_id: Optional[str] = None,
):
    user_id = get_user_id(authorization)
    repo = ActionItemRepository()
    filters = {}
    if assignee:
        filters["assignee"] = assignee
    if priority and priority != "All":
        filters["priority"] = priority
    if status and status != "All":
        filters["status"] = status
    if action_type and action_type != "All":
        filters["action_type"] = action_type
    if transcript_id:
        filters["transcript_id"] = transcript_id

    items = repo.get_action_items(user_id, filters=filters, search=search)

    if project_key and project_key != "All":
        items = [i for i in items if (i.get("jira_project_key") or "") == project_key]

    return {"action_items": items, "count": len(items)}

@router.put("/{item_id}")
def update_action_item(item_id: str, req: UpdateFieldsRequest, authorization: Optional[str] = Header(None)):
    user_id = get_user_id(authorization)
    repo = ActionItemRepository()
    fields = req.dict(exclude_unset=True)
    try:
        updated = repo.update_action_item_fields(user_id, item_id, fields)
        return {"success": True, "action_item": updated}
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))

@router.patch("/{item_id}/status")
def update_status(item_id: str, req: StatusUpdateRequest, authorization: Optional[str] = Header(None)):
    user_id = get_user_id(authorization)
    repo = ActionItemRepository()
    valid_statuses = ["Pending Review", "Approved", "Needs Clarification", "Rejected"]
    if req.status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of {valid_statuses}")

    try:
        updated = repo.update_action_item_status(user_id, item_id, req.status)
        return {"success": True, "action_item": updated}
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))

@router.delete("/{item_id}")
def delete_action_item(item_id: str, authorization: Optional[str] = Header(None)):
    user_id = get_user_id(authorization)
    repo = ActionItemRepository()
    repo.delete_action_item(user_id, item_id)
    return {"success": True, "deleted_id": item_id}

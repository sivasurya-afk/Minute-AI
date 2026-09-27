from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from database.repositories import ProjectRepository
from utils.validators import validate_jira_project_key
from utils.auth import DEMO_USER

router = APIRouter(prefix="/api/projects", tags=["projects"])

def get_user_id(authorization: Optional[str] = Header(None)) -> str:
    # Default to demo user if no bearer or demo
    if not authorization or "demo" in authorization.lower():
        return DEMO_USER["id"]
    return DEMO_USER["id"]

class CreateProjectRequest(BaseModel):
    project_name: str
    project_key: str
    description: str = ""
    team_name: str = "General"
    keywords: List[str] = []
    is_active: bool = True

class UpdateProjectRequest(BaseModel):
    project_name: str
    description: str = ""
    team_name: str = "General"
    keywords: List[str] = []
    is_active: Optional[bool] = None

@router.get("")
def list_projects(authorization: Optional[str] = Header(None), active_only: bool = False):
    user_id = get_user_id(authorization)
    repo = ProjectRepository()
    projects = repo.get_projects(user_id, active_only=active_only)
    return {"projects": projects}

@router.post("")
def create_project(req: CreateProjectRequest, authorization: Optional[str] = Header(None)):
    user_id = get_user_id(authorization)
    valid_key, err = validate_jira_project_key(req.project_key)
    if not valid_key:
        raise HTTPException(status_code=400, detail=err)

    repo = ProjectRepository()
    try:
        project = repo.create_project(
            user_id=user_id,
            project_data={
                "project_name": req.project_name.strip(),
                "project_key": req.project_key.strip().upper(),
                "description": req.description.strip(),
                "team_name": req.team_name.strip() or "General",
                "keywords": [k.lower().strip() for k in req.keywords if k.strip()],
                "is_active": req.is_active,
            }
        )
        return {"success": True, "project": project}
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))

@router.put("/{project_id}")
def update_project(project_id: str, req: UpdateProjectRequest, authorization: Optional[str] = Header(None)):
    user_id = get_user_id(authorization)
    repo = ProjectRepository()
    try:
        update_data = {
            "project_name": req.project_name.strip(),
            "description": req.description.strip(),
            "team_name": req.team_name.strip(),
            "keywords": [k.lower().strip() for k in req.keywords if k.strip()],
        }
        if req.is_active is not None:
            update_data["is_active"] = req.is_active
        updated = repo.update_project(user_id, project_id, update_data)
        return {"success": True, "project": updated}
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))

@router.patch("/{project_id}/toggle")
def toggle_project(project_id: str, is_active: bool, authorization: Optional[str] = Header(None)):
    user_id = get_user_id(authorization)
    repo = ProjectRepository()
    updated = repo.toggle_active(user_id, project_id, is_active)
    return {"success": True, "project": updated}

@router.delete("/{project_id}")
def delete_project(project_id: str, authorization: Optional[str] = Header(None)):
    user_id = get_user_id(authorization)
    repo = ProjectRepository()
    repo.delete_project(user_id, project_id)
    return {"success": True, "deleted_id": project_id}

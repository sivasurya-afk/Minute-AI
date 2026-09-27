from fastapi import APIRouter, Header, Response
from typing import Optional
from database.repositories import ActionItemRepository
from services.export_service import ExportService
from utils.auth import DEMO_USER

router = APIRouter(prefix="/api/export", tags=["export"])

def get_user_id(authorization: Optional[str] = Header(None)) -> str:
    if not authorization or "demo" in authorization.lower():
        return DEMO_USER["id"]
    return DEMO_USER["id"]

@router.get("/csv")
def export_csv(authorization: Optional[str] = Header(None)):
    user_id = get_user_id(authorization)
    repo = ActionItemRepository()
    items = repo.get_action_items(user_id)
    csv_bytes = ExportService.to_csv(items)
    return Response(
        content=csv_bytes,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=minute_ai_action_items.csv"}
    )

@router.get("/excel")
def export_excel(authorization: Optional[str] = Header(None)):
    user_id = get_user_id(authorization)
    repo = ActionItemRepository()
    items = repo.get_action_items(user_id)
    xlsx_bytes = ExportService.to_excel(items)
    return Response(
        content=xlsx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=minute_ai_action_items.xlsx"}
    )

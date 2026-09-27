from fastapi import APIRouter
from pydantic import BaseModel
import os
from services.groq_service import AVAILABLE_GROQ_MODELS, DEFAULT_LLM_MODEL, DEFAULT_TRANSCRIPTION_MODEL, GroqService
from database.supabase_client import get_supabase_client

router = APIRouter(prefix="/api/settings", tags=["settings"])

class UpdateSettingsRequest(BaseModel):
    groq_model: str
    confidence_threshold: float

@router.get("")
def get_settings():
    groq_service = GroqService.get_instance()
    groq_key = os.getenv("GROQ_API_KEY", "")
    has_groq = groq_service.is_configured()

    client = get_supabase_client()
    is_connected = client is not None

    return {
        "groq_model": os.getenv("GROQ_LLM_MODEL", DEFAULT_LLM_MODEL),
        "available_models": AVAILABLE_GROQ_MODELS,
        "transcription_model": DEFAULT_TRANSCRIPTION_MODEL,
        "confidence_threshold": float(os.getenv("CONFIDENCE_THRESHOLD", 0.70)),
        "diagnostics": {
            "groq_configured": has_groq,
            "groq_key_masked": (groq_key[:6] + "••••••••" + groq_key[-4:]) if len(groq_key) > 10 else "Configured",
            "supabase_connected": is_connected,
            "supabase_url": os.getenv("SUPABASE_URL", "https://qklcxzdumitujatjoxqn.supabase.co"),
            "supabase_ref": "qklcxzdumitujatjoxqn"
        }
    }

@router.post("")
def update_settings(req: UpdateSettingsRequest):
    os.environ["GROQ_LLM_MODEL"] = req.groq_model
    os.environ["CONFIDENCE_THRESHOLD"] = str(req.confidence_threshold)
    return {"success": True, "settings": get_settings()}

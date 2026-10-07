from fastapi import APIRouter, HTTPException, Header, UploadFile, File, Form
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import date
from database.repositories import TranscriptRepository, ActionItemRepository, ProjectRepository
from utils.transcript_parser import TranscriptParser
from services.action_extractor import ActionExtractor
from services.groq_service import GroqService
from services.transcription_service import TranscriptionService
from utils.auth import DEMO_USER
from services.action_extractor import _generate_offline_extracted_items

router = APIRouter(prefix="/api/transcripts", tags=["transcripts"])

def get_user_id(authorization: Optional[str] = Header(None)) -> str:
    if not authorization or "demo" in authorization.lower():
        return DEMO_USER["id"]
    return DEMO_USER["id"]

class ProcessTextRequest(BaseModel):
    transcript_text: str
    meeting_name: str = "Team Sync Meeting"
    meeting_date: Optional[str] = None
    source_type: str = "paste"

@router.get("")
def list_transcripts(authorization: Optional[str] = Header(None)):
    user_id = get_user_id(authorization)
    repo = TranscriptRepository()
    transcripts = repo.get_transcripts(user_id)
    return {"transcripts": transcripts}

@router.get("/{transcript_id}")
def get_transcript(transcript_id: str, authorization: Optional[str] = Header(None)):
    user_id = get_user_id(authorization)
    t_repo = TranscriptRepository()
    a_repo = ActionItemRepository()
    transcript = t_repo.get_transcript_by_id(user_id, transcript_id)
    if not transcript:
        raise HTTPException(status_code=404, detail="Transcript not found")
    items = a_repo.get_action_items(user_id, filters={"transcript_id": transcript_id})
    return {"transcript": transcript, "action_items": items}

@router.post("/process-text")
def process_text(req: ProcessTextRequest, authorization: Optional[str] = Header(None)):
    user_id = get_user_id(authorization)
    raw_text = req.transcript_text.strip()
    if not raw_text:
        raise HTTPException(status_code=400, detail="Transcript content cannot be empty.")

    t_repo = TranscriptRepository()
    a_repo = ActionItemRepository()
    p_repo = ProjectRepository()

    meeting_date_val = req.meeting_date or str(date.today())

    # Duplicate check
    existing = t_repo.find_duplicate(user_id, req.meeting_name, meeting_date_val)
    if existing:
        items = a_repo.get_action_items(user_id, filters={"transcript_id": existing["id"]})
        return {
            "is_duplicate": True,
            "message": "Transcript with this meeting name and date has already been processed. Returning existing record.",
            "transcript": existing,
            "action_items": items,
        }

    # Parse
    parsed_text = TranscriptParser.parse(raw_text, req.source_type)
    if not parsed_text:
        raise HTTPException(status_code=400, detail="Unable to extract meaningful text from transcript.")

    # Active projects for classification
    active_projects = p_repo.get_projects(user_id, active_only=True)

    # Groq extraction
    groq_service = GroqService.get_instance()
    extractor = ActionExtractor(groq_service=groq_service)

    if groq_service.is_configured():
        success, extracted_items, err_msg = extractor.extract_action_items(
            transcript_text=parsed_text,
            active_projects=active_projects,
            meeting_name=req.meeting_name,
        )
        if not success:
            raise HTTPException(status_code=500, detail=f"AI extraction failed: {err_msg}")
    else:
        extracted_items = _generate_offline_extracted_items(parsed_text, active_projects)

    # Save transcript
    meeting_date_val = req.meeting_date or str(date.today())
    new_tr = t_repo.create_transcript(
        user_id=user_id,
        transcript_data={
            "meeting_name": req.meeting_name.strip(),
            "meeting_date": meeting_date_val,
            "transcript_text": raw_text,
            "source_type": req.source_type,
            "processing_status": "processed",
        }
    )

    # Bulk save action items
    saved_items = a_repo.bulk_create_action_items(user_id, new_tr["id"], extracted_items)

    return {
        "success": True,
        "is_duplicate": False,
        "transcript": new_tr,
        "action_items": saved_items,
        "count": len(saved_items),
    }

@router.post("/process-file")
async def process_file(
    file: UploadFile = File(...),
    meeting_name: str = Form("Uploaded Meeting"),
    meeting_date: Optional[str] = Form(None),
    authorization: Optional[str] = Header(None),
):
    user_id = get_user_id(authorization)
    filename = file.filename or "upload.txt"
    content_bytes = await file.read()

    # Determine extension
    ext = filename.split(".")[-1].lower() if "." in filename else "txt"

    groq_service = GroqService.get_instance()

    # Handle Audio
    if ext in ["mp3", "wav", "m4a", "ogg", "flac"]:
        trans_service = TranscriptionService(groq_service)
        if not trans_service.groq_service.is_configured():
            raise HTTPException(status_code=400, detail="Groq API key not configured for audio transcription.")
        success, raw_text_or_err = trans_service.transcribe_audio_bytes(content_bytes, filename)
        if not success or not raw_text_or_err:
            raise HTTPException(status_code=500, detail=f"Whisper transcription failed: {raw_text_or_err}")
        raw_text = raw_text_or_err
        source_type = "audio"
    else:
        # Text based
        try:
            raw_text = content_bytes.decode("utf-8", errors="replace")
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to decode text file: {e}")
        source_type = ext if ext in ["vtt", "srt", "txt"] else "txt"

    req = ProcessTextRequest(
        transcript_text=raw_text,
        meeting_name=meeting_name,
        meeting_date=meeting_date,
        source_type=source_type,
    )
    return process_text(req, authorization)

@router.post("/{transcript_id}/reprocess")
def reprocess_transcript(transcript_id: str, authorization: Optional[str] = Header(None)):
    user_id = get_user_id(authorization)
    t_repo = TranscriptRepository()
    a_repo = ActionItemRepository()
    p_repo = ProjectRepository()

    tr = t_repo.get_transcript_by_id(user_id, transcript_id)
    if not tr:
        raise HTTPException(status_code=404, detail="Transcript not found")

    a_repo.delete_action_items_by_transcript(user_id, transcript_id)
    active_projects = p_repo.get_projects(user_id, active_only=True)
    groq_service = GroqService.get_instance()
    extractor = ActionExtractor(groq_service=groq_service)

    raw_text = tr.get("transcript_text", "")
    if groq_service.is_configured():
        success, new_items, err = extractor.extract_action_items(
            transcript_text=raw_text,
            active_projects=active_projects,
            meeting_name=tr.get("meeting_name", ""),
        )
        if not success:
            raise HTTPException(status_code=500, detail=f"Reprocessing error: {err}")
    else:
        new_items = _generate_offline_extracted_items(raw_text, active_projects)

    saved_items = a_repo.bulk_create_action_items(user_id, transcript_id, new_items)
    t_repo.update_status(user_id, transcript_id, "processed")

    return {
        "success": True,
        "action_items": saved_items,
        "count": len(saved_items)
    }

@router.delete("/{transcript_id}")
def delete_transcript(transcript_id: str, authorization: Optional[str] = Header(None)):
    user_id = get_user_id(authorization)
    t_repo = TranscriptRepository()
    t_repo.delete_transcript(user_id, transcript_id)
    return {"success": True, "deleted_id": transcript_id}

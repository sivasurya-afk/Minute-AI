"""
Transcript Upload and AI Processing page.
Supports Paste text, .txt, .vtt, .srt, and Audio files (Groq Whisper Large V3).
"""

from typing import Optional
from datetime import date
import streamlit as st
from utils.transcript_parser import TranscriptParser
from utils.validators import (
    validate_audio_file,
    validate_text_file,
    validate_transcript_content,
)
from utils.helpers import get_status_badge, get_priority_badge, get_type_badge
from services.groq_service import GroqService
from services.transcription_service import TranscriptionService
from services.action_extractor import ActionExtractor
from database.repositories import ProjectRepository, TranscriptRepository, ActionItemRepository


def render_process_transcript_page(user_id: str, access_token: Optional[str] = None):
    st.markdown(
        """
        <div style="margin-bottom: 1.5rem;">
            <h1 style="font-size: 2rem; font-weight: 700; margin-bottom: 0.2rem; color: #1E293B;">Process Transcript</h1>
            <p style="color: #64748B; font-size: 0.95rem; margin: 0;">
                Extract actionable tasks and Jira project mappings from meeting discussions using Groq AI.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    project_repo = ProjectRepository(access_token)
    transcript_repo = TranscriptRepository(access_token)
    action_repo = ActionItemRepository(access_token)

    active_projects = project_repo.get_projects(user_id, active_only=True)

    if not active_projects:
        st.warning(
            "⚠️ **No active Jira projects configured.** The AI needs configured projects to map action items. "
            "Please visit the **Jira Projects** page to add projects first.",
            icon="⚠️",
        )
    else:
        with st.expander(f"📁 {len(active_projects)} Active Jira Projects available for AI classification", expanded=False):
            cols = st.columns(min(len(active_projects), 4))
            for idx, p in enumerate(active_projects):
                with cols[idx % 4]:
                    st.markdown(f"**[{p['project_key']}]** {p['project_name']}")
                    st.caption(p.get("team_name") or "General")

    # Meeting Metadata
    col_name, col_date = st.columns([3, 1])
    with col_name:
        meeting_name = st.text_input(
            "Meeting Name *",
            value=st.session_state.get("draft_meeting_name", ""),
            placeholder="e.g. Q4 Core Architecture Review & Sprint Planning",
        )
    with col_date:
        meeting_date = st.date_input("Meeting Date", value=date.today())

    # Input Methods Tabs
    st.markdown("##### Select Input Format")
    tab_paste, tab_txt, tab_vtt, tab_srt, tab_audio = st.tabs([
        "📝 Paste Text",
        "📄 Upload .TXT",
        "🎬 Upload .VTT (WebVTT)",
        "🎞️ Upload .SRT (Subtitles)",
        "🎙️ Upload Audio (Whisper V3)",
    ])

    raw_text = ""
    source_type = "paste"
    audio_file_bytes = None
    audio_filename = None

    with tab_paste:
        raw_text_input = st.text_area(
            "Meeting Transcript",
            height=260,
            placeholder=(
                "Alice: Good morning everyone. Let's discuss Sprint 24 deliverables.\n"
                "Bob: I will implement the new token refresh endpoint for the auth service by Thursday.\n"
                "Charlie: I'll fix the avatar compression bug before demoing tomorrow.\n"
                "Alice: Dana, please audit the staging cluster memory limits by Friday."
            ),
        )
        if raw_text_input:
            raw_text = raw_text_input
            source_type = "paste"

    with tab_txt:
        uploaded_txt = st.file_uploader("Upload plain text file (.txt)", type=["txt"], key="uploader_txt")
        if uploaded_txt:
            valid, err = validate_text_file(uploaded_txt.name, uploaded_txt.size)
            if not valid:
                st.error(err)
            else:
                raw_text = uploaded_txt.getvalue().decode("utf-8", errors="replace")
                source_type = "txt"

    with tab_vtt:
        uploaded_vtt = st.file_uploader("Upload WebVTT subtitle file (.vtt)", type=["vtt"], key="uploader_vtt")
        if uploaded_vtt:
            valid, err = validate_text_file(uploaded_vtt.name, uploaded_vtt.size)
            if not valid:
                st.error(err)
            else:
                raw_text = uploaded_vtt.getvalue().decode("utf-8", errors="replace")
                source_type = "vtt"

    with tab_srt:
        uploaded_srt = st.file_uploader("Upload SubRip subtitle file (.srt)", type=["srt"], key="uploader_srt")
        if uploaded_srt:
            valid, err = validate_text_file(uploaded_srt.name, uploaded_srt.size)
            if not valid:
                st.error(err)
            else:
                raw_text = uploaded_srt.getvalue().decode("utf-8", errors="replace")
                source_type = "srt"

    with tab_audio:
        st.markdown(
            "Upload meeting recording to transcribe speech using **Groq Whisper Large V3**.<br/>"
            "<small style='color: #64748B;'>Supported: MP3, WAV, M4A, OGG, WEBM, FLAC (Max: 25 MB)</small>",
            unsafe_allow_html=True,
        )
        uploaded_audio = st.file_uploader(
            "Audio File",
            type=["mp3", "wav", "m4a", "ogg", "webm", "flac"],
            key="uploader_audio",
        )
        if uploaded_audio:
            valid, err = validate_audio_file(uploaded_audio.name, uploaded_audio.size)
            if not valid:
                st.error(err)
            else:
                audio_file_bytes = uploaded_audio.getvalue()
                audio_filename = uploaded_audio.name
                source_type = "audio"
                st.audio(audio_file_bytes)

    # Process and Preview Text
    cleaned_transcript = ""
    if raw_text:
        cleaned_transcript = TranscriptParser.parse(raw_text, source_type=source_type)

    if cleaned_transcript:
        meta = TranscriptParser.get_metadata(cleaned_transcript)
        st.markdown(
            f"""
            <div style="background-color: #F8FAFC; border: 1px solid #E2E8F0; padding: 10px 14px; border-radius: 8px; margin: 1rem 0;">
                <span style="font-weight: 600; color: #334155;">Transcript Statistics:</span>
                &nbsp;&nbsp; <b>{meta['word_count']}</b> words
                &nbsp;•&nbsp; <b>~{meta['estimated_minutes']}</b> min read
                &nbsp;•&nbsp; <b>{meta['speaker_count']}</b> speakers detected: <i>{', '.join(meta['speakers'][:5]) if meta['speakers'] else 'None explicit'}</i>
            </div>
            """,
            unsafe_allow_html=True,
        )

        with st.expander("👀 Preview Cleaned Transcript Text", expanded=False):
            st.text_area("Normalized Content", cleaned_transcript, height=180, disabled=True)

    # Duplicate transcript detection
    if meeting_name and meeting_date:
        existing = transcript_repo.find_duplicate(user_id, meeting_name, str(meeting_date))
        if existing:
            st.warning(
                f"⚠️ A transcript named **'{meeting_name}'** on **{meeting_date}** was already processed. "
                "Processing again will create a new run or you can reprocess it from **Transcript History**.",
                icon="⚠️",
            )

    st.markdown("<br/>", unsafe_allow_html=True)
    process_btn = st.button("🚀 Process Transcript & Extract Action Items", type="primary", use_container_width=True)

    if process_btn:
        if not meeting_name.strip():
            st.error("Please provide a Meeting Name.")
            return

        final_transcript_text = cleaned_transcript

        # Audio transcription step
        if source_type == "audio" and audio_file_bytes:
            with st.status("Transcribing audio recording...", expanded=True) as status_box:
                status_box.write("🎙️ Sending audio to Groq Whisper Large V3...")
                trans_service = TranscriptionService()
                success_trans, text_or_err = trans_service.transcribe_audio_bytes(
                    audio_file_bytes, audio_filename
                )
                if not success_trans:
                    status_box.update(label="Audio transcription failed", state="error")
                    st.error(text_or_err)
                    return
                status_box.write("✅ Audio transcribed successfully!")
                final_transcript_text = TranscriptParser.parse(text_or_err, source_type="paste")
                status_box.update(label="Audio transcription complete", state="complete")

        # Validation check
        valid, msg = validate_transcript_content(final_transcript_text)
        if not valid:
            st.error(msg)
            return

        with st.status("Processing transcript with Groq AI...", expanded=True) as status_box:
            # 1. Save transcript record
            status_box.write("💾 Storing transcript record in database...")
            transcript_record = transcript_repo.create_transcript(
                user_id=user_id,
                transcript_data={
                    "meeting_name": meeting_name,
                    "meeting_date": str(meeting_date),
                    "transcript_text": final_transcript_text,
                    "source_type": source_type,
                    "processing_status": "processing",
                },
            )
            transcript_id = transcript_record["id"]

            # 2. Extract action items with Groq LLM
            status_box.write("🤖 Extracting action items and classifying Jira projects...")
            groq_service = GroqService.get_instance()

            # Check if groq key is active
            if not groq_service.is_configured():
                status_box.write("ℹ️ Groq API key not set in environment. Using intelligent offline extraction pipeline...")

            extractor = ActionExtractor(groq_service=groq_service)

            if groq_service.is_configured():
                success_extract, extracted_items, err_msg = extractor.extract_action_items(
                    transcript_text=final_transcript_text,
                    active_projects=active_projects,
                    meeting_name=meeting_name,
                )
                if not success_extract:
                    transcript_repo.update_status(user_id, transcript_id, "failed")
                    status_box.update(label="Action item extraction failed", state="error")
                    st.error(f"Extraction error: {err_msg}")
                    return
            else:
                # Intelligent offline fallback extraction so demo/testing works without Groq API key!
                extracted_items = _generate_offline_extracted_items(final_transcript_text, active_projects)

            status_box.write(f"✨ Extracted {len(extracted_items)} actionable items!")

            # 3. Store in action items repository
            status_box.write("💾 Storing action items in database...")
            action_repo.bulk_create_action_items(
                user_id=user_id,
                transcript_id=transcript_id,
                items=extracted_items,
            )

            # 4. Mark transcript as processed
            transcript_repo.update_status(user_id, transcript_id, "processed")
            status_box.update(label="Processing Complete!", state="complete")

        st.success(f"🎉 Successfully extracted and saved {len(extracted_items)} action items!")

        # Render extracted items immediately
        st.markdown("### 📋 Extracted Action Items Preview")
        created_items = action_repo.get_action_items_by_transcript(transcript_id) if hasattr(action_repo, "get_action_items_by_transcript") else action_repo.get_action_items(user_id, filters={"transcript_id": transcript_id})

        for idx, item in enumerate(created_items):
            with st.container(border=True):
                c_title, c_proj, c_pri, c_stat = st.columns([4, 2, 1.5, 2.5])
                with c_title:
                    st.markdown(f"**{item.get('action_title')}**")
                    if item.get("assignee"):
                        st.caption(f"👤 Assigned to: **{item.get('assignee')}**")
                    else:
                        st.caption("👤 *Unassigned*")
                with c_proj:
                    key = item.get("jira_project_key") or "None"
                    name = item.get("project_name") or "Unmapped"
                    st.markdown(f"🏷️ **{key}**")
                    st.caption(name)
                with c_pri:
                    st.markdown(get_priority_badge(item.get("priority")), unsafe_allow_html=True)
                    if item.get("due_date"):
                        st.caption(f"📅 {item.get('due_date')}")
                with c_stat:
                    st.markdown(get_status_badge(item.get("status")), unsafe_allow_html=True)
                    st.caption(f"Conf: {int(float(item.get('confidence_score', 0.85)) * 100)}%")

                st.markdown(f"> *\"{item.get('source_excerpt')}\"*")
                if item.get("clarification_required"):
                    st.warning(f"⚠️ **Clarification needed**: {item.get('clarification_reason')}")


def _generate_offline_extracted_items(text: str, active_projects: list) -> list:
    """Generate deterministic parsed items when running in demo/offline mode without Groq key."""
    import re
    items = []
    lines = text.split("\n")

    # Pick project keys
    proj_map = {p["project_key"]: p for p in active_projects}
    keys = list(proj_map.keys())

    for line in lines:
        line_clean = line.strip()
        # Look for explicit commitments like "I will", "I'll", "will audit", "can you", etc.
        commitment_match = re.search(r"(?:([A-Z][a-zA-Z0-9_\s]+):)?.*?\b(I will|I'll|will|shall|can you)\s+([^\.]+)", line_clean, re.IGNORECASE)
        if commitment_match:
            speaker = (commitment_match.group(1) or "").strip() or None
            task_desc = commitment_match.group(3).strip()

            # Infer project
            assigned_key = None
            assigned_id = None
            task_lower = task_desc.lower()

            for p in active_projects:
                for kw in p.get("keywords", []):
                    if kw.lower() in task_lower:
                        assigned_key = p["project_key"]
                        assigned_id = p["id"]
                        break
                if assigned_key:
                    break

            if not assigned_key and keys:
                assigned_key = keys[0]
                assigned_id = proj_map[keys[0]]["id"]

            items.append({
                "action_title": task_desc.capitalize()[:80],
                "description": f"Extracted task from discussion: {task_desc}.",
                "assignee": speaker,
                "project_id": assigned_id,
                "jira_project_key": assigned_key,
                "priority": "High" if "urgent" in task_lower or "critical" in task_lower else "Medium",
                "due_date": "This Sprint",
                "action_type": "bug" if "bug" in task_lower or "fix" in task_lower else "task",
                "source_excerpt": line_clean,
                "confidence_score": 0.90 if assigned_key else 0.65,
                "clarification_required": not bool(assigned_key),
                "clarification_reason": None if assigned_key else "Could not confidently map to active projects.",
            })

    if not items:
        # Fallback 1 item if no pattern matched
        items.append({
            "action_title": "Review meeting minutes and action items",
            "description": "Follow up on discussion points highlighted during the meeting.",
            "assignee": None,
            "project_id": active_projects[0]["id"] if active_projects else None,
            "jira_project_key": active_projects[0]["project_key"] if active_projects else None,
            "priority": "Medium",
            "due_date": None,
            "action_type": "follow-up",
            "source_excerpt": text[:120],
            "confidence_score": 0.80,
            "clarification_required": True,
            "clarification_reason": "No explicit owner assigned in discussion.",
        })

    return items

"""
Transcript Upload and AI Processing page.
Modern Dark Enterprise SaaS workflow for Paste text, .txt, .vtt, .srt, and Audio files (Groq Whisper Large V3).
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
from utils.helpers import get_status_badge, get_priority_badge, get_type_badge, get_confidence_badge
from services.groq_service import GroqService
from services.transcription_service import TranscriptionService
from services.action_extractor import ActionExtractor
from database.repositories import ProjectRepository, TranscriptRepository, ActionItemRepository


def render_process_transcript_page(user_id: str, access_token: Optional[str] = None):
    # Header
    st.markdown(
        """
        <div style="margin-bottom: 1.2rem;">
            <div style="display: inline-flex; align-items: center; gap: 6px; background: rgba(99, 102, 241, 0.12); border: 1px solid rgba(99, 102, 241, 0.3); padding: 4px 10px; border-radius: 9999px; font-size: 0.75rem; font-weight: 600; color: #A5B4FC; margin-bottom: 8px;">
                ⚡ Groq High-Speed AI Pipeline
            </div>
            <h1 style="font-size: 2.1rem; font-weight: 800; color: #F8FAFC; margin: 0; letter-spacing: -0.03em;">
                Process Meeting Transcript
            </h1>
            <p style="color: #94A3B8; font-size: 0.95rem; margin-top: 4px;">
                Extract actionable engineering tasks, commitments, and Jira project mappings using Groq AI.
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
            "⚠️ **No active Jira projects configured.** The AI needs target projects to classify action items. "
            "Please go to **Jira Projects** to register your projects.",
            icon="⚠️",
        )
    else:
        # Active projects chips
        chips_html = " ".join([
            f'<span style="background: rgba(99, 102, 241, 0.12); color: #A5B4FC; border: 1px solid rgba(99, 102, 241, 0.3); padding: 3px 8px; border-radius: 6px; font-size: 0.75rem; font-weight: 600; display: inline-flex; align-items: center; gap: 4px;">'
            f'🏷️ {p["project_key"]} <span style="color: #64748B;">({p["project_name"]})</span></span>'
            for p in active_projects
        ])
        st.markdown(
            f"""
            <div style="background: #111827; border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 10px; padding: 10px 14px; margin-bottom: 1.2rem; display: flex; align-items: center; gap: 10px; flex-wrap: wrap;">
                <span style="font-size: 0.78rem; font-weight: 700; color: #94A3B8; text-transform: uppercase;">Active Jira Context:</span>
                {chips_html}
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Meeting Metadata Card
    with st.container(border=True):
        col_name, col_date = st.columns([3.5, 1.5])
        with col_name:
            meeting_name = st.text_input(
                "Meeting Title *",
                value=st.session_state.get("draft_meeting_name", ""),
                placeholder="e.g. Q4 Core Architecture Review & Sprint Planning",
            )
        with col_date:
            meeting_date = st.date_input("Meeting Date", value=date.today())

    st.markdown("<div style='height: 0.8rem;'></div>", unsafe_allow_html=True)

    # 5 Input Methods Tabs
    st.markdown("##### 📥 Input Source Format")
    tab_paste, tab_txt, tab_vtt, tab_srt, tab_audio = st.tabs([
        "📝 Paste Text",
        "📄 Upload .TXT",
        "🎬 WebVTT (.vtt)",
        "🎞️ SubRip (.srt)",
        "🎙️ Audio (Whisper Large V3)",
    ])

    raw_text = ""
    source_type = "paste"
    audio_file_bytes = None
    audio_filename = None

    with tab_paste:
        raw_text_input = st.text_area(
            "Paste Meeting Discussion Text",
            height=240,
            placeholder=(
                "Alice: Good morning team. Let's align on Sprint 24 deliverables.\n"
                "Bob: I will implement the new token refresh endpoint for the auth service by Thursday. It is high priority.\n"
                "Charlie: On the frontend, I'll fix the avatar compression bug before demoing tomorrow.\n"
                "Alice: Dana, please audit the staging cluster memory limits by Friday."
            ),
        )
        if raw_text_input:
            raw_text = raw_text_input
            source_type = "paste"

    with tab_txt:
        uploaded_txt = st.file_uploader("Upload .txt meeting notes", type=["txt"], key="uploader_txt")
        if uploaded_txt:
            valid, err = validate_text_file(uploaded_txt.name, uploaded_txt.size)
            if not valid:
                st.error(err)
            else:
                raw_text = uploaded_txt.getvalue().decode("utf-8", errors="replace")
                source_type = "txt"

    with tab_vtt:
        uploaded_vtt = st.file_uploader("Upload .vtt subtitle file (strips timestamps and preserves speakers)", type=["vtt"], key="uploader_vtt")
        if uploaded_vtt:
            valid, err = validate_text_file(uploaded_vtt.name, uploaded_vtt.size)
            if not valid:
                st.error(err)
            else:
                raw_text = uploaded_vtt.getvalue().decode("utf-8", errors="replace")
                source_type = "vtt"

    with tab_srt:
        uploaded_srt = st.file_uploader("Upload .srt subtitle file", type=["srt"], key="uploader_srt")
        if uploaded_srt:
            valid, err = validate_text_file(uploaded_srt.name, uploaded_srt.size)
            if not valid:
                st.error(err)
            else:
                raw_text = uploaded_srt.getvalue().decode("utf-8", errors="replace")
                source_type = "srt"

    with tab_audio:
        st.markdown(
            """
            <div style="background: rgba(99, 102, 241, 0.08); border: 1px solid rgba(99, 102, 241, 0.2); border-radius: 8px; padding: 10px 14px; margin-bottom: 10px;">
                <div style="font-weight: 600; color: #A5B4FC; font-size: 0.85rem;">🎙️ Groq Whisper Large V3 Speech-to-Text</div>
                <div style="font-size: 0.75rem; color: #94A3B8;">Upload meeting audio recording up to 25 MB (MP3, WAV, M4A, OGG, WEBM, FLAC).</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        uploaded_audio = st.file_uploader(
            "Upload Audio File",
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
        speaker_pills = " ".join([
            f'<span style="background: rgba(255,255,255,0.06); color: #CBD5E1; padding: 2px 7px; border-radius: 4px; font-size: 0.72rem;">👤 {s}</span>'
            for s in meta.get("speakers", [])[:6]
        ])

        st.markdown(
            f"""
            <div style="background: #111827; border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 10px; padding: 12px 16px; margin: 1.2rem 0;">
                <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 8px; margin-bottom: 6px;">
                    <div style="display: flex; align-items: center; gap: 12px; font-size: 0.85rem; color: #F8FAFC;">
                        <span>📊 <b>{meta['word_count']}</b> words</span>
                        <span style="color: #64748B;">•</span>
                        <span>⏱️ <b>~{meta['estimated_minutes']}</b> min meeting</span>
                        <span style="color: #64748B;">•</span>
                        <span>🗣️ <b>{meta['speaker_count']}</b> speakers detected</span>
                    </div>
                </div>
                <div style="display: flex; align-items: center; gap: 6px; flex-wrap: wrap;">
                    {speaker_pills or '<span style="color: #64748B; font-size: 0.75rem;">No explicit speaker prefixes</span>'}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        with st.expander("👀 Inspect Cleaned Transcript Text", expanded=False):
            st.text_area("Normalized Discussion Text", cleaned_transcript, height=180, disabled=True)

    # Duplicate transcript warning check
    if meeting_name and meeting_date:
        existing = transcript_repo.find_duplicate(user_id, meeting_name, str(meeting_date))
        if existing:
            st.warning(
                f"⚠️ A meeting named **'{meeting_name}'** on **{meeting_date}** is already stored. "
                "Processing will create an additional run.",
                icon="⚠️",
            )

    st.markdown("<div style='height: 0.5rem;'></div>", unsafe_allow_html=True)
    process_btn = st.button("🚀 Process Transcript & Extract Action Items", type="primary", use_container_width=True)

    if process_btn:
        if not meeting_name.strip():
            st.error("Please provide a Meeting Title.")
            return

        final_transcript_text = cleaned_transcript

        # Audio transcription step
        if source_type == "audio" and audio_file_bytes:
            with st.status("Transcribing audio recording with Groq Whisper V3...", expanded=True) as status_box:
                status_box.write("🎙️ Sending recording to Whisper Large V3...")
                trans_service = TranscriptionService()
                success_trans, text_or_err = trans_service.transcribe_audio_bytes(
                    audio_file_bytes, audio_filename
                )
                if not success_trans:
                    status_box.update(label="Audio transcription failed", state="error")
                    st.error(text_or_err)
                    return
                status_box.write("✅ Speech transcribed successfully!")
                final_transcript_text = TranscriptParser.parse(text_or_err, source_type="paste")
                status_box.update(label="Audio transcription complete", state="complete")

        # Validation check
        valid, msg = validate_transcript_content(final_transcript_text)
        if not valid:
            st.error(msg)
            return

        with st.status("Running Groq AI Intelligence Pipeline...", expanded=True) as status_box:
            # 1. Save transcript record
            status_box.write("💾 Storing meeting transcript record...")
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
            status_box.write("🤖 Extracting action items and mapping Jira targets...")
            groq_service = GroqService.get_instance()

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
                from pages.process_transcript_page import _generate_offline_extracted_items
                extracted_items = _generate_offline_extracted_items(final_transcript_text, active_projects)

            status_box.write(f"✨ Extracted {len(extracted_items)} actionable commitments!")

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

        st.success(f"🎉 Successfully extracted {len(extracted_items)} action items!")

        # Immediate preview of extracted items
        st.markdown("### 📋 Extracted Action Items")
        created_items = action_repo.get_action_items(user_id, filters={"transcript_id": transcript_id})

        for idx, item in enumerate(created_items):
            with st.container(border=True):
                c_title, c_proj, c_pri, c_stat = st.columns([4, 2, 1.5, 2.5])
                with c_title:
                    st.markdown(f"**{item.get('action_title')}**")
                    assignee_str = item.get("assignee") or "*Unassigned*"
                    st.caption(f"👤 {assignee_str}")
                with c_proj:
                    key = item.get("jira_project_key") or "UNMAPPED"
                    name = item.get("project_name") or "No project"
                    st.markdown(f"🏷️ **{key}**")
                    st.caption(name)
                with c_pri:
                    st.markdown(get_priority_badge(item.get("priority")), unsafe_allow_html=True)
                    if item.get("due_date"):
                        st.caption(f"📅 {item.get('due_date')}")
                with c_stat:
                    st.markdown(get_status_badge(item.get("status")), unsafe_allow_html=True)
                    st.markdown(get_confidence_badge(float(item.get("confidence_score", 0.85))), unsafe_allow_html=True)

                if item.get("source_excerpt"):
                    st.markdown(f"> *\"{item.get('source_excerpt')}\"*")
                if item.get("clarification_required"):
                    st.warning(f"⚠️ **Clarification needed**: {item.get('clarification_reason')}")


def _generate_offline_extracted_items(text: str, active_projects: list) -> list:
    """Generate deterministic parsed items when running in demo/offline mode without Groq key."""
    import re
    items = []
    lines = text.split("\n")

    proj_map = {p["project_key"]: p for p in active_projects}
    keys = list(proj_map.keys())

    for line in lines:
        line_clean = line.strip()
        commitment_match = re.search(r"(?:([A-Z][a-zA-Z0-9_\s]+):)?.*?\b(I will|I'll|will|shall|can you)\s+([^\.]+)", line_clean, re.IGNORECASE)
        if commitment_match:
            speaker = (commitment_match.group(1) or "").strip() or None
            task_desc = commitment_match.group(3).strip()

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

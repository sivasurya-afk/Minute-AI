"""
Transcript History page for Minute AI.
View past transcripts, inspect original text and extracted items, reprocess, or delete.
"""

from typing import Optional
from datetime import date
import streamlit as st
from database.repositories import TranscriptRepository, ActionItemRepository, ProjectRepository
from services.action_extractor import ActionExtractor
from services.groq_service import GroqService
from utils.helpers import format_iso_date, get_status_badge


def render_transcript_history_page(user_id: str, access_token: Optional[str] = None):
    st.markdown(
        """
        <div style="margin-bottom: 1.5rem;">
            <h1 style="font-size: 2rem; font-weight: 700; margin-bottom: 0.2rem; color: #1E293B;">Transcript History</h1>
            <p style="color: #64748B; font-size: 0.95rem; margin: 0;">
                Archive of past meeting transcripts and extraction runs. Inspect, reprocess, or manage.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    transcript_repo = TranscriptRepository(access_token)
    action_repo = ActionItemRepository(access_token)
    project_repo = ProjectRepository(access_token)

    transcripts = transcript_repo.get_transcripts(user_id)

    # Search & Date Filter
    c_search, c_date_filter = st.columns([3, 1])
    with c_search:
        search_query = st.text_input("Search Meeting Name", placeholder="Type meeting title...")
    with c_date_filter:
        filter_date = st.date_input("Filter by Meeting Date", value=None)

    # Filter list
    filtered_transcripts = transcripts
    if search_query.strip():
        q = search_query.strip().lower()
        filtered_transcripts = [t for t in filtered_transcripts if q in t.get("meeting_name", "").lower()]
    if filter_date:
        filtered_transcripts = [t for t in filtered_transcripts if str(t.get("meeting_date", "")) == str(filter_date)]

    st.markdown(f"**{len(filtered_transcripts)}** transcripts found")
    st.markdown("<hr style='margin: 0.8rem 0 1.2rem 0; border: none; border-top: 1px solid #E2E8F0;'/>", unsafe_allow_html=True)

    if not filtered_transcripts:
        st.info("No transcripts found matching your criteria.")
        return

    # List of Transcripts
    for tr in filtered_transcripts:
        tr_id = tr["id"]
        with st.container(border=True):
            col_info, col_counts, col_ops = st.columns([4, 2, 2])

            with col_info:
                st.markdown(f"### {tr.get('meeting_name')}")
                st.caption(
                    f"📅 Meeting Date: **{tr.get('meeting_date')}** &nbsp;•&nbsp; "
                    f"Uploaded: {format_iso_date(tr.get('created_at'))} &nbsp;•&nbsp; "
                    f"Source: `{tr.get('source_type', 'paste').upper()}`"
                )

            with col_counts:
                st.metric(
                    label="Action Items",
                    value=tr.get("action_item_count", 0),
                    delta=f"{tr.get('approved_count', 0)} Approved",
                    delta_color="normal",
                )

            with col_ops:
                status_val = tr.get("processing_status", "processed").title()
                st.markdown(
                    f'<span style="background-color: #F1F5F9; color: #334155; padding: 4px 8px; border-radius: 4px; font-weight: 600; font-size: 0.8rem;">Status: {status_val}</span>',
                    unsafe_allow_html=True,
                )

            # Details expander: original transcript and associated items
            with st.expander(f"📜 View Transcript & Associated Items", expanded=False):
                tab_text, tab_items, tab_manage = st.tabs(["Original Transcript", "Extracted Items", "Manage / Reprocess"])

                with tab_text:
                    st.text_area(
                        "Original Content",
                        value=tr.get("transcript_text", ""),
                        height=200,
                        disabled=True,
                        key=f"text_{tr_id}",
                    )

                with tab_items:
                    items = action_repo.get_action_items(user_id, filters={"transcript_id": tr_id})
                    if items:
                        for i in items:
                            col_t, col_s = st.columns([5, 2])
                            with col_t:
                                st.markdown(f"**{i.get('action_title')}**")
                                st.caption(f"Project: **{i.get('jira_project_key') or 'None'}** | Assignee: **{i.get('assignee') or 'Unassigned'}**")
                            with col_s:
                                st.markdown(get_status_badge(i.get("status")), unsafe_allow_html=True)
                            st.markdown(f"> *\"{i.get('source_excerpt', '')}\"*")
                            st.markdown("<hr style='margin: 4px 0;'/>", unsafe_allow_html=True)
                    else:
                        st.write("No action items found for this transcript.")

                with tab_manage:
                    st.markdown("##### Transcript Actions")
                    col_reproc, col_del = st.columns(2)

                    with col_reproc:
                        st.info("🔄 **Reprocess Transcript**: Deletes previously extracted action items and re-runs AI extraction safely.")
                        if st.button("Reprocess with AI", key=f"reproc_{tr_id}", type="primary"):
                            with st.spinner("Reprocessing transcript..."):
                                # 1. Delete previous items
                                action_repo.delete_action_items_by_transcript(user_id, tr_id)

                                # 2. Extract with AI
                                active_projects = project_repo.get_projects(user_id, active_only=True)
                                groq_service = GroqService.get_instance()
                                extractor = ActionExtractor(groq_service=groq_service)

                                if groq_service.is_configured():
                                    success, new_items, err = extractor.extract_action_items(
                                        transcript_text=tr.get("transcript_text", ""),
                                        active_projects=active_projects,
                                        meeting_name=tr.get("meeting_name", ""),
                                    )
                                else:
                                    from pages.process_transcript_page import _generate_offline_extracted_items
                                    new_items = _generate_offline_extracted_items(tr.get("transcript_text", ""), active_projects)
                                    success = True

                                if success:
                                    action_repo.bulk_create_action_items(user_id, tr_id, new_items)
                                    transcript_repo.update_status(user_id, tr_id, "processed")
                                    st.success(f"Successfully reprocessed! Extracted {len(new_items)} items.")
                                    st.rerun()
                                else:
                                    st.error(f"Reprocessing failed: {err}")

                    with col_del:
                        st.warning("⚠️ **Delete Transcript**: Permanently removes this transcript and its action items.")
                        confirm_del = st.checkbox("Confirm Deletion", key=f"confirm_del_{tr_id}")
                        if st.button("Delete Forever", key=f"del_{tr_id}", disabled=not confirm_del, type="secondary"):
                            transcript_repo.delete_transcript(user_id, tr_id)
                            st.success("Transcript deleted.")
                            st.rerun()

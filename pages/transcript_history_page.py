"""
Transcript History page for Minute AI.
Modern Dark Enterprise SaaS archive for reviewing past transcripts, safe AI reprocessing, and deletion.
"""

from typing import Optional
from datetime import date
import streamlit as st
from database.repositories import TranscriptRepository, ActionItemRepository, ProjectRepository
from services.action_extractor import ActionExtractor
from services.groq_service import GroqService
from utils.helpers import format_iso_date, get_status_badge, get_priority_badge, get_type_badge


def render_transcript_history_page(user_id: str, access_token: Optional[str] = None):
    # Header
    st.markdown(
        """
        <div style="margin-bottom: 1.2rem;">
            <h1 style="font-size: 2.1rem; font-weight: 800; color: #111827; margin: 0; letter-spacing: -0.03em;">
                Transcript History
            </h1>
            <p style="color: #6B7280; font-size: 0.95rem; margin-top: 4px;">
                Historical archive of all processed meeting discussions, extraction runs, and linked action items.
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
        search_query = st.text_input("🔍 Search Meetings Archive", placeholder="Filter by meeting title...")
    with c_date_filter:
        filter_date = st.date_input("Meeting Date Filter", value=None)

    filtered_transcripts = transcripts
    if search_query.strip():
        q = search_query.strip().lower()
        filtered_transcripts = [t for t in filtered_transcripts if q in t.get("meeting_name", "").lower()]
    if filter_date:
        filtered_transcripts = [t for t in filtered_transcripts if str(t.get("meeting_date", "")) == str(filter_date)]

    st.markdown(
        f"""
        <div style="font-size: 0.85rem; color: #6B7280; margin-bottom: 12px;">
            Found <b style="color: #111827;">{len(filtered_transcripts)}</b> meeting transcripts
        </div>
        """,
        unsafe_allow_html=True,
    )

    if not filtered_transcripts:
        st.info("No meeting transcripts match your search criteria.")
        return

    # List of Transcripts
    for tr in filtered_transcripts:
        tr_id = tr["id"]
        status_val = tr.get("processing_status", "processed").title()
        badge_bg = "#ECFDF5" if status_val == "Processed" else "#FEF3C7"
        badge_col = "#059669" if status_val == "Processed" else "#D97706"

        with st.container(border=True):
            col_info, col_counts, col_status = st.columns([4, 2, 1.5])

            with col_info:
                st.markdown(
                    f"""
                    <div style="font-size: 1.15rem; font-weight: 700; color: #111827; margin-bottom: 4px;">
                        {tr.get('meeting_name')}
                    </div>
                    <div style="display: flex; align-items: center; gap: 8px; font-size: 0.75rem; color: #6B7280;">
                        <span style="background: #F3F4F6; color: #4B5563; border: 1px solid #E5E7EB; padding: 2px 6px; border-radius: 4px; font-family: monospace;">
                            {tr.get('source_type', 'paste').upper()}
                        </span>
                        <span>•</span>
                        <span>📅 Held: <b style="color: #374151;">{tr.get('meeting_date')}</b></span>
                        <span>•</span>
                        <span>Uploaded: {format_iso_date(tr.get('created_at'))}</span>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            with col_counts:
                st.markdown(
                    f"""
                    <div style="display: flex; gap: 14px; align-items: center; height: 100%;">
                        <div>
                            <div style="font-size: 1.3rem; font-weight: 800; color: #4F46E5;">{tr.get('action_item_count', 0)}</div>
                            <div style="font-size: 0.7rem; color: #6B7280; text-transform: uppercase;">Extracted</div>
                        </div>
                        <div>
                            <div style="font-size: 1.3rem; font-weight: 800; color: #059669;">{tr.get('approved_count', 0)}</div>
                            <div style="font-size: 0.7rem; color: #6B7280; text-transform: uppercase;">Approved</div>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            with col_status:
                st.markdown(
                    f"""
                    <div style="display: flex; justify-content: flex-end; align-items: center; height: 100%;">
                        <span style="background: {badge_bg}; color: {badge_col}; border: 1px solid {badge_col}40; padding: 4px 10px; border-radius: 6px; font-size: 0.75rem; font-weight: 600;">
                            {status_val}
                        </span>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            # Details expander: original transcript and associated items
            with st.expander(f"📜 View Full Details & Associated Items", expanded=False):
                tab_text, tab_items, tab_manage = st.tabs(["Original Transcript Text", "Linked Action Items", "Reprocess / Delete"])

                with tab_text:
                    st.text_area(
                        "Meeting Content",
                        value=tr.get("transcript_text", ""),
                        height=200,
                        disabled=True,
                        key=f"text_{tr_id}",
                    )

                with tab_items:
                    items = action_repo.get_action_items(user_id, filters={"transcript_id": tr_id})
                    if items:
                        for i in items:
                            col_t, col_s = st.columns([4.5, 2.5])
                            with col_t:
                                st.markdown(f"**{i.get('action_title')}**")
                                st.caption(f"Project: **{i.get('jira_project_key') or 'None'}** | Assignee: **{i.get('assignee') or 'Unassigned'}**")
                            with col_s:
                                st.markdown(
                                    f"<div style='text-align: right;'>{get_status_badge(i.get('status'))}</div>",
                                    unsafe_allow_html=True,
                                )
                            if i.get("source_excerpt"):
                                st.markdown(f"> *\"{i.get('source_excerpt')}\"*")
                            st.markdown("<hr style='margin: 6px 0; border: none; border-top: 1px solid #E5E7EB;'/>", unsafe_allow_html=True)
                    else:
                        st.write("No action items currently linked to this transcript.")

                with tab_manage:
                    st.markdown("##### Management Actions")
                    col_reproc, col_del = st.columns(2)

                    with col_reproc:
                        st.info("🔄 **Safe Reprocess**: Clears previous extracted items for this meeting and re-runs AI extraction without duplicate records.")
                        if st.button("Reprocess with AI Engine", key=f"reproc_{tr_id}", type="primary", use_container_width=True):
                            with st.spinner("Reprocessing transcript with Groq AI..."):
                                action_repo.delete_action_items_by_transcript(user_id, tr_id)
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
                                    st.success(f"Reprocessed successfully! Extracted {len(new_items)} items.")
                                    st.rerun()
                                else:
                                    st.error(f"Reprocessing failed: {err}")

                    with col_del:
                        st.warning("⚠️ **Permanently Delete**: Removes this transcript and all linked action items from database.")
                        confirm_del = st.checkbox("Confirm permanent deletion", key=f"confirm_del_{tr_id}")
                        if st.button("Delete Permanently", key=f"del_{tr_id}", disabled=not confirm_del, type="secondary", use_container_width=True):
                            transcript_repo.delete_transcript(user_id, tr_id)
                            st.success("Transcript deleted.")
                            st.rerun()

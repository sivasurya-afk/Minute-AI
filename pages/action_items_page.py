"""
Action Items Management page.
Modern Dark Enterprise SaaS issue board with filters, inline editing, and CSV/Excel export.
"""

from typing import Optional, Dict, Any
import streamlit as st
import pandas as pd
from database.repositories import ActionItemRepository, ProjectRepository, TranscriptRepository
from services.export_service import ExportService
from utils.helpers import get_status_badge, get_priority_badge, get_type_badge, get_confidence_badge, format_iso_date


def render_action_items_page(user_id: str, access_token: Optional[str] = None):
    # Header
    col_hdr, col_btns = st.columns([3.5, 2.5])
    with col_hdr:
        st.markdown(
            """
            <div style="margin-bottom: 1rem;">
                <h1 style="font-size: 2.1rem; font-weight: 800; color: #F8FAFC; margin: 0; letter-spacing: -0.03em;">
                    Action Items
                </h1>
                <p style="color: #94A3B8; font-size: 0.95rem; margin-top: 4px;">
                    Review, modify, approve, and export meeting tasks categorized for Jira.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    action_repo = ActionItemRepository(access_token)
    project_repo = ProjectRepository(access_token)
    transcript_repo = TranscriptRepository(access_token)

    projects = project_repo.get_projects(user_id)
    transcripts = transcript_repo.get_transcripts(user_id)

    # Search & Filter Drawer
    with st.expander("⚡ Filter & Search Tasks", expanded=True):
        col_search, col_proj, col_status = st.columns([3, 2, 2])

        with col_search:
            search_query = st.text_input("🔍 Search Action Items", placeholder="Filter by title, assignee, excerpt, or notes...")

        with col_proj:
            proj_options = ["All Projects"] + [f"{p['project_key']} - {p['project_name']}" for p in projects]
            selected_proj_label = st.selectbox("Jira Project", proj_options)
            selected_project_id = None
            if selected_proj_label != "All Projects":
                key_prefix = selected_proj_label.split(" - ")[0]
                matching_p = next((p for p in projects if p["project_key"] == key_prefix), None)
                if matching_p:
                    selected_project_id = matching_p["id"]

        with col_status:
            status_options = ["All Statuses", "Pending Review", "Approved", "Needs Clarification", "Rejected"]
            selected_status = st.selectbox("Status", status_options)
            if selected_status == "All Statuses":
                selected_status = None

        col_pri, col_type, col_assignee, col_meeting = st.columns(4)

        with col_pri:
            pri_options = ["All Priorities", "Highest", "High", "Medium", "Low", "Lowest"]
            selected_pri = st.selectbox("Priority", pri_options)
            if selected_pri == "All Priorities":
                selected_pri = None

        with col_type:
            type_options = ["All Types", "bug", "feature", "investigation", "follow-up", "task"]
            selected_type = st.selectbox("Type", type_options)
            if selected_type == "All Types":
                selected_type = None

        with col_assignee:
            assignee_filter = st.text_input("Assignee", placeholder="Filter by person...")

        with col_meeting:
            meeting_options = ["All Meetings"] + [t["meeting_name"] for t in transcripts]
            preselected_meeting_id = st.session_state.pop("filter_transcript_id", None)
            selected_meeting = st.selectbox("Origin Meeting", meeting_options)
            selected_transcript_id = preselected_meeting_id
            if selected_meeting != "All Meetings":
                matching_t = next((t for t in transcripts if t["meeting_name"] == selected_meeting), None)
                if matching_t:
                    selected_transcript_id = matching_t["id"]

    # Build filters dictionary
    filters: Dict[str, Any] = {}
    if selected_project_id:
        filters["project_id"] = selected_project_id
    if selected_status:
        filters["status"] = selected_status
    if selected_pri:
        filters["priority"] = selected_pri
    if selected_type:
        filters["action_type"] = selected_type
    if assignee_filter.strip():
        filters["assignee"] = assignee_filter.strip()
    if selected_transcript_id:
        filters["transcript_id"] = selected_transcript_id

    items = action_repo.get_action_items(user_id, filters=filters, search=search_query)

    # Action Toolbar
    col_count, col_exp_csv, col_exp_xls = st.columns([4, 1.2, 1.2])
    with col_count:
        st.markdown(
            f"""
            <div style="display: flex; align-items: center; gap: 8px; margin: 8px 0;">
                <span style="font-size: 0.95rem; font-weight: 700; color: #F8FAFC;">
                    Showing <span style="color: #818CF8;">{len(items)}</span> items
                </span>
                <span style="color: #64748B;">•</span>
                <span style="font-size: 0.8rem; color: #94A3B8;">Human-in-the-loop review</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col_exp_csv:
        csv_bytes = ExportService.to_csv(items)
        st.download_button(
            label="📥 Export CSV",
            data=csv_bytes,
            file_name="minute_ai_action_items.csv",
            mime="text/csv",
            use_container_width=True,
            disabled=(len(items) == 0),
        )
    with col_exp_xls:
        excel_bytes = ExportService.to_excel(items)
        st.download_button(
            label="📊 Export Excel",
            data=excel_bytes,
            file_name="minute_ai_action_items.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
            disabled=(len(items) == 0),
        )

    st.markdown("<hr style='margin: 0.6rem 0 1.2rem 0; border: none; border-top: 1px solid rgba(255,255,255,0.08);'/>", unsafe_allow_html=True)

    if not items:
        st.info("No action items match the selected criteria. Adjust your filters or process a new transcript.")
        return

    # Render Task Cards
    priority_border_colors = {
        "Highest": "#EF4444",
        "High": "#F97316",
        "Medium": "#EAB308",
        "Low": "#38BDF8",
        "Lowest": "#64748B",
    }

    for item in items:
        item_id = item["id"]
        status = item.get("status", "Pending Review")
        pri = item.get("priority")
        border_accent = priority_border_colors.get(pri, "#6366F1")

        with st.container(border=True):
            # Header line: Title, project key, priority, confidence, status
            c_main, c_meta = st.columns([4.2, 2.8])

            with c_main:
                # Title and assignee
                assignee_display = item.get("assignee") or "Unassigned"
                due_display = item.get("due_date") or "No deadline"
                st.markdown(
                    f"""
                    <div style="margin-bottom: 6px;">
                        <span style="font-size: 1.15rem; font-weight: 700; color: #F8FAFC; line-height: 1.25;">
                            {item.get('action_title')}
                        </span>
                    </div>
                    <div style="display: flex; flex-wrap: wrap; align-items: center; gap: 8px; margin-bottom: 8px; font-size: 0.78rem; color: #94A3B8;">
                        <span style="background: rgba(255,255,255,0.06); padding: 2px 7px; border-radius: 5px; color: #CBD5E1;">
                            👤 {assignee_display}
                        </span>
                        <span>•</span>
                        <span style="background: rgba(255,255,255,0.06); padding: 2px 7px; border-radius: 5px; color: #CBD5E1;">
                            📅 {due_display}
                        </span>
                        {f'<span>•</span><span style="color: #64748B;">From: {item.get("meeting_name")}</span>' if item.get("meeting_name") else ''}
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            with c_meta:
                # Project & Badges
                proj_key = item.get("jira_project_key") or "UNMAPPED"
                proj_name = item.get("project_name") or "No project linked"
                st.markdown(
                    f"""
                    <div style="display: flex; flex-direction: column; align-items: flex-end; gap: 6px;">
                        <div style="display: flex; align-items: center; gap: 6px;">
                            <span style="background: rgba(99, 102, 241, 0.15); color: #A5B4FC; border: 1px solid rgba(99, 102, 241, 0.3); font-size: 0.75rem; font-weight: 700; padding: 2px 8px; border-radius: 6px;">
                                🏷️ {proj_key}
                            </span>
                            {get_status_badge(status)}
                        </div>
                        <div style="display: flex; align-items: center; gap: 6px;">
                            {get_priority_badge(pri)}
                            {get_type_badge(item.get("action_type", "task"))}
                            {get_confidence_badge(float(item.get("confidence_score", 0.85)))}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            # Description
            if item.get("description"):
                st.markdown(
                    f"""
                    <div style="font-size: 0.88rem; color: #CBD5E1; line-height: 1.5; margin: 4px 0 10px 0;">
                        {item.get('description')}
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            # Verbatim source quote callout
            if item.get("source_excerpt"):
                st.markdown(
                    f"""
                    <div style="background: #0B0F17; border-left: 3px solid #6366F1; border-radius: 0 8px 8px 0; padding: 8px 12px; margin: 6px 0 12px 0;">
                        <div style="font-size: 0.7rem; font-weight: 700; color: #818CF8; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 2px;">
                            Verbatim Discussion Excerpt
                        </div>
                        <div style="font-size: 0.82rem; color: #94A3B8; font-style: italic;">
                            "{item.get('source_excerpt')}"
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            if item.get("clarification_required"):
                st.markdown(
                    f"""
                    <div style="background: rgba(245, 158, 11, 0.1); border: 1px solid rgba(245, 158, 11, 0.3); border-radius: 8px; padding: 6px 10px; margin-bottom: 10px; font-size: 0.8rem; color: #FBBF24;">
                        ⚠️ <b>Clarification Flag:</b> {item.get('clarification_reason') or 'Task requirements or target project mapping are uncertain.'}
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            # Workflow Action Buttons & Edit Toggle
            col_actions, col_edit_btn = st.columns([3.5, 1.2])

            with col_actions:
                b_app, b_clar, b_rej = st.columns(3)
                with b_app:
                    if status != "Approved":
                        if st.button("✅ Approve", key=f"app_{item_id}", use_container_width=True, type="primary"):
                            action_repo.update_action_item_status(user_id, item_id, "Approved")
                            st.rerun()

                with b_clar:
                    if status != "Needs Clarification":
                        if st.button("❓ Clarify", key=f"clar_{item_id}", use_container_width=True, type="secondary"):
                            action_repo.update_action_item_status(user_id, item_id, "Needs Clarification")
                            st.rerun()

                with b_rej:
                    if status != "Rejected":
                        if st.button("❌ Reject", key=f"rej_{item_id}", use_container_width=True, type="secondary"):
                            action_repo.update_action_item_status(user_id, item_id, "Rejected")
                            st.rerun()

            with col_edit_btn:
                show_edit = st.toggle("✏️ Edit Fields", key=f"toggle_edit_{item_id}")

            # Editable fields section
            if show_edit:
                with st.form(key=f"edit_form_{item_id}"):
                    st.markdown("##### ✏️ Edit Action Item")
                    e_title = st.text_input("Title", value=item.get("action_title", ""))
                    e_desc = st.text_area("Description", value=item.get("description", ""), height=90)

                    e_c1, e_c2 = st.columns(2)
                    with e_c1:
                        e_assignee = st.text_input("Assignee", value=item.get("assignee") or "")
                        e_due = st.text_input("Due Date", value=item.get("due_date") or "")
                    with e_c2:
                        pri_idx = ["Lowest", "Low", "Medium", "High", "Highest"].index(item.get("priority") or "Medium")
                        e_priority = st.selectbox(
                            "Priority",
                            ["Lowest", "Low", "Medium", "High", "Highest"],
                            index=pri_idx,
                        )

                        proj_keys = [p["project_key"] for p in projects]
                        current_proj_key = item.get("jira_project_key")
                        current_proj_idx = proj_keys.index(current_proj_key) if current_proj_key in proj_keys else 0
                        e_proj_key = st.selectbox("Jira Project", proj_keys if proj_keys else ["None"], index=current_proj_idx if proj_keys else 0)

                    stat_idx = ["Pending Review", "Approved", "Needs Clarification", "Rejected"].index(status)
                    e_status = st.selectbox("Status", ["Pending Review", "Approved", "Needs Clarification", "Rejected"], index=stat_idx)

                    save_submitted = st.form_submit_button("Save Changes", type="primary")
                    if save_submitted:
                        selected_proj = next((p for p in projects if p["project_key"] == e_proj_key), None)
                        updated_fields = {
                            "action_title": e_title.strip(),
                            "description": e_desc.strip(),
                            "assignee": e_assignee.strip() or None,
                            "due_date": e_due.strip() or None,
                            "priority": e_priority,
                            "jira_project_key": e_proj_key if selected_proj else None,
                            "project_id": selected_proj["id"] if selected_proj else None,
                            "status": e_status,
                        }
                        action_repo.update_action_item_fields(user_id, item_id, updated_fields)
                        st.success("Action item updated successfully!")
                        st.rerun()

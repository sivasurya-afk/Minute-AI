"""
Action Items Management page.
Provides interactive filtering, searching, editing, review status transitions, and CSV/Excel export.
"""

from typing import Optional, Dict, Any
import streamlit as st
import pandas as pd
from database.repositories import ActionItemRepository, ProjectRepository, TranscriptRepository
from services.export_service import ExportService
from utils.helpers import get_status_badge, get_priority_badge, get_type_badge, format_iso_date


def render_action_items_page(user_id: str, access_token: Optional[str] = None):
    st.markdown(
        """
        <div style="margin-bottom: 1.5rem;">
            <h1 style="font-size: 2rem; font-weight: 700; margin-bottom: 0.2rem; color: #1E293B;">Action Items</h1>
            <p style="color: #64748B; font-size: 0.95rem; margin: 0;">
                Review, modify, filter, and approve extracted tasks before they become Jira tickets.
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

    # 1. Search & Filter Bar
    with st.expander("🔍 Search & Filter Action Items", expanded=True):
        col_search, col_proj, col_status = st.columns([3, 2, 2])

        with col_search:
            search_query = st.text_input("Search Title, Description, Excerpt", placeholder="Type keywords...")

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
            selected_status = st.selectbox("Review Status", status_options)
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
            selected_type = st.selectbox("Action Type", type_options)
            if selected_type == "All Types":
                selected_type = None

        with col_assignee:
            assignee_filter = st.text_input("Assignee Filter", placeholder="e.g. Bob")

        with col_meeting:
            meeting_options = ["All Meetings"] + [t["meeting_name"] for t in transcripts]
            preselected_meeting_id = st.session_state.pop("filter_transcript_id", None)
            selected_meeting = st.selectbox("Meeting", meeting_options)
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

    # 2. Results Header & Export Buttons
    col_count, col_exp_csv, col_exp_xls = st.columns([5, 1.2, 1.2])

    with col_count:
        st.markdown(f"Showing **{len(items)}** action items matching current filters")

    with col_exp_csv:
        csv_bytes = ExportService.to_csv(items)
        st.download_button(
            label="📥 CSV",
            data=csv_bytes,
            file_name="minute_ai_action_items.csv",
            mime="text/csv",
            use_container_width=True,
            disabled=(len(items) == 0),
        )

    with col_exp_xls:
        excel_bytes = ExportService.to_excel(items)
        st.download_button(
            label="📊 Excel",
            data=excel_bytes,
            file_name="minute_ai_action_items.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
            disabled=(len(items) == 0),
        )

    st.markdown("<hr style='margin: 0.8rem 0 1.2rem 0; border: none; border-top: 1px solid #E2E8F0;'/>", unsafe_allow_html=True)

    if not items:
        st.info("No action items found matching your criteria. Try adjusting your filters or search query.")
        return

    # 3. Action Items List View
    for item in items:
        item_id = item["id"]
        status = item.get("status", "Pending Review")

        with st.container(border=True):
            # Top line: Title, project, priority, status badges
            c1, c2, c3, c4 = st.columns([4, 2, 1.5, 2.5])

            with c1:
                st.markdown(f"#### {item.get('action_title')}")
                st.caption(f"📅 Due: **{item.get('due_date') or 'None'}** &nbsp;•&nbsp; 👤 Assignee: **{item.get('assignee') or 'Unassigned'}**")

            with c2:
                proj_name = item.get("project_name") or "Unmapped Project"
                proj_key = item.get("jira_project_key") or "—"
                st.markdown(f"🏷️ **{proj_key}**")
                st.caption(proj_name)

            with c3:
                st.markdown(get_priority_badge(item.get("priority")), unsafe_allow_html=True)
                st.markdown("<div style='margin-top: 4px;'>", unsafe_allow_html=True)
                st.markdown(get_type_badge(item.get("action_type", "task")), unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)

            with c4:
                st.markdown(get_status_badge(status), unsafe_allow_html=True)
                conf = int(float(item.get("confidence_score", 0.85)) * 100)
                st.caption(f"AI Confidence: {conf}%")

            # Description and Source Excerpt
            st.write(item.get("description", ""))

            with st.expander("💬 View Source Transcript Excerpt & AI Reason", expanded=False):
                st.markdown(f"> *\"{item.get('source_excerpt', '')}\"*")
                if item.get("clarification_required"):
                    st.warning(f"⚠️ **Clarification Reason:** {item.get('clarification_reason')}")
                if item.get("meeting_name"):
                    st.caption(f"From Meeting: **{item.get('meeting_name')}** ({format_iso_date(item.get('meeting_date'))})")

            # Actions Row: Quick status buttons + Edit expander
            col_actions, col_edit_btn = st.columns([3, 1])

            with col_actions:
                b_app, b_clar, b_rej = st.columns(3)
                with b_app:
                    if status != "Approved":
                        if st.button("✅ Approve", key=f"app_{item_id}", use_container_width=True):
                            action_repo.update_action_item_status(user_id, item_id, "Approved")
                            st.success("Item marked as Approved!")
                            st.rerun()

                with b_clar:
                    if status != "Needs Clarification":
                        if st.button("❓ Clarify", key=f"clar_{item_id}", use_container_width=True):
                            action_repo.update_action_item_status(user_id, item_id, "Needs Clarification")
                            st.rerun()

                with b_rej:
                    if status != "Rejected":
                        if st.button("❌ Reject", key=f"rej_{item_id}", use_container_width=True):
                            action_repo.update_action_item_status(user_id, item_id, "Rejected")
                            st.rerun()

            with col_edit_btn:
                show_edit = st.toggle("✏️ Edit Fields", key=f"toggle_edit_{item_id}")

            # Editable fields section
            if show_edit:
                with st.form(key=f"edit_form_{item_id}"):
                    st.markdown("##### ✏️ Edit Action Item Details")
                    e_title = st.text_input("Title", value=item.get("action_title", ""))
                    e_desc = st.text_area("Description", value=item.get("description", ""), height=100)

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

                        # Project options
                        proj_keys = [p["project_key"] for p in projects]
                        current_proj_key = item.get("jira_project_key")
                        current_proj_idx = proj_keys.index(current_proj_key) if current_proj_key in proj_keys else 0
                        e_proj_key = st.selectbox("Jira Project", proj_keys if proj_keys else ["None"], index=current_proj_idx if proj_keys else 0)

                    stat_idx = ["Pending Review", "Approved", "Needs Clarification", "Rejected"].index(status)
                    e_status = st.selectbox("Status", ["Pending Review", "Approved", "Needs Clarification", "Rejected"], index=stat_idx)

                    save_submitted = st.form_submit_button("Save Changes", type="primary")
                    if save_submitted:
                        # Find corresponding project_id
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

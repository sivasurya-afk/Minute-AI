"""
Jira Projects Management page for Minute AI.
Configure target Jira projects used as context for AI semantic task classification.
"""

from typing import Optional
import streamlit as st
from database.repositories import ProjectRepository
from utils.validators import validate_jira_project_key


def render_jira_projects_page(user_id: str, access_token: Optional[str] = None):
    st.markdown(
        """
        <div style="margin-bottom: 1.5rem;">
            <h1 style="font-size: 2rem; font-weight: 700; margin-bottom: 0.2rem; color: #1E293B;">Jira Projects</h1>
            <p style="color: #64748B; font-size: 0.95rem; margin: 0;">
                Manage target Jira projects used by the AI to map and categorize extracted meeting tasks.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    project_repo = ProjectRepository(access_token)
    projects = project_repo.get_projects(user_id)

    # Search bar & Add project button
    col_search, col_add_btn = st.columns([4, 1.2])
    with col_search:
        search_query = st.text_input("Search Projects", placeholder="Search by name, key, or team...")

    # Filter projects
    filtered_projects = projects
    if search_query.strip():
        q = search_query.strip().lower()
        filtered_projects = [
            p for p in filtered_projects
            if (
                q in p.get("project_name", "").lower()
                or q in p.get("project_key", "").lower()
                or q in p.get("team_name", "").lower()
                or any(q in kw.lower() for kw in p.get("keywords", []))
            )
        ]

    # Add Project Modal / Expander
    with st.expander("➕ Add New Jira Project", expanded=False):
        with st.form("add_project_form", clear_on_submit=True):
            col_pname, col_pkey = st.columns([3, 1])
            with col_pname:
                p_name = st.text_input("Project Name *", placeholder="e.g. Mobile iOS Application")
            with col_pkey:
                p_key = st.text_input("Project Key *", placeholder="e.g. IOS").upper()

            p_desc = st.text_area(
                "Scope & Description *",
                placeholder="Explain the technical scope and responsibilities of this project for AI classification...",
                height=90,
            )

            col_team, col_kw = st.columns(2)
            with col_team:
                p_team = st.text_input("Team / Department", placeholder="e.g. Mobile Engineering")
            with col_kw:
                p_keywords = st.text_input("Keywords (comma-separated)", placeholder="swift, ios, mobile, swiftui, testflight")

            p_active = st.checkbox("Active for AI classification", value=True)

            submit_project = st.form_submit_button("Create Jira Project", type="primary")

            if submit_project:
                if not p_name.strip():
                    st.error("Project name is required.")
                else:
                    valid_key, key_err = validate_jira_project_key(p_key)
                    if not valid_key:
                        st.error(key_err)
                    else:
                        kw_list = [k.strip().lower() for k in p_keywords.split(",") if k.strip()]
                        try:
                            project_repo.create_project(
                                user_id=user_id,
                                project_data={
                                    "project_name": p_name.strip(),
                                    "project_key": p_key.strip(),
                                    "description": p_desc.strip(),
                                    "team_name": p_team.strip() or "General",
                                    "keywords": kw_list,
                                    "is_active": p_active,
                                },
                            )
                            st.success(f"Project [{p_key}] created successfully!")
                            st.rerun()
                        except ValueError as ve:
                            st.error(str(ve))

    st.markdown("<hr style='margin: 1rem 0; border: none; border-top: 1px solid #E2E8F0;'/>", unsafe_allow_html=True)

    if not filtered_projects:
        st.info("No Jira projects configured yet. Click **'Add New Jira Project'** above to register a project.")
        return

    # Projects List
    for p in filtered_projects:
        p_id = p["id"]
        is_active = p.get("is_active", True)

        with st.container(border=True):
            col_main, col_toggle, col_del = st.columns([5, 1.5, 1])

            with col_main:
                status_icon = "🟢" if is_active else "⚪"
                st.markdown(f"### {status_icon} [{p.get('project_key')}] {p.get('project_name')}")
                st.caption(f"Team: **{p.get('team_name') or 'General'}**")
                st.write(p.get("description") or "*No description provided.*")

                # Keywords
                kws = p.get("keywords") or []
                if kws:
                    kw_badges = " ".join([
                        f'<span style="background-color: #F1F5F9; color: #475569; padding: 2px 6px; border-radius: 4px; font-size: 0.75rem;">#{k}</span>'
                        for k in kws
                    ])
                    st.markdown(kw_badges, unsafe_allow_html=True)

            with col_toggle:
                st.write("Classification:")
                new_active = st.toggle("Active", value=is_active, key=f"active_toggle_{p_id}")
                if new_active != is_active:
                    project_repo.toggle_active(user_id, p_id, new_active)
                    st.rerun()

            with col_del:
                st.write("Actions:")
                if st.button("🗑️ Delete", key=f"del_proj_{p_id}", type="secondary", use_container_width=True):
                    project_repo.delete_project(user_id, p_id)
                    st.warning(f"Project [{p.get('project_key')}] deleted.")
                    st.rerun()

            # Edit toggle
            with st.expander("✏️ Edit Project Details", expanded=False):
                with st.form(key=f"edit_proj_form_{p_id}"):
                    e_name = st.text_input("Project Name", value=p.get("project_name", ""))
                    e_desc = st.text_area("Scope & Description", value=p.get("description", ""), height=80)
                    e_c1, e_c2 = st.columns(2)
                    with e_c1:
                        e_team = st.text_input("Team", value=p.get("team_name", ""))
                    with e_c2:
                        current_kw_str = ", ".join(p.get("keywords") or [])
                        e_kws = st.text_input("Keywords (comma-separated)", value=current_kw_str)

                    if st.form_submit_button("Save Changes", type="primary"):
                        kw_list = [k.strip().lower() for k in e_kws.split(",") if k.strip()]
                        project_repo.update_project(
                            user_id=user_id,
                            project_id=p_id,
                            update_data={
                                "project_name": e_name.strip(),
                                "description": e_desc.strip(),
                                "team_name": e_team.strip(),
                                "keywords": kw_list,
                            },
                        )
                        st.success("Project updated successfully!")
                        st.rerun()

"""
Jira Projects Management page for Minute AI.
Modern Dark Enterprise SaaS target project registry and classification management.
"""

from typing import Optional
import streamlit as st
from database.repositories import ProjectRepository
from utils.validators import validate_jira_project_key


def render_jira_projects_page(user_id: str, access_token: Optional[str] = None):
    # Header
    col_hdr, col_btn = st.columns([4, 1.5])
    with col_hdr:
        st.markdown(
            """
            <div style="margin-bottom: 1.2rem;">
                <h1 style="font-size: 2.1rem; font-weight: 800; color: #F8FAFC; margin: 0; letter-spacing: -0.03em;">
                    Jira Projects
                </h1>
                <p style="color: #94A3B8; font-size: 0.95rem; margin-top: 4px;">
                    Configure target Jira projects that provide semantic context for AI action item classification.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    project_repo = ProjectRepository(access_token)
    projects = project_repo.get_projects(user_id)

    # Search bar & Add project expander
    col_search, col_stats = st.columns([3.5, 1.5])
    with col_search:
        search_query = st.text_input("🔍 Search Configured Projects", placeholder="Filter by project key, name, team, or keywords...")
    with col_stats:
        active_count = len([p for p in projects if p.get("is_active", True)])
        st.markdown(
            f"""
            <div style="background: #111827; border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 8px; padding: 9px 12px; margin-top: 1.6rem; text-align: center;">
                <span style="font-size: 0.8rem; color: #94A3B8;">Active Context:</span>
                <span style="font-weight: 700; color: #10B981; font-size: 0.9rem;">{active_count} of {len(projects)}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

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

    # Add Project Card / Expander
    with st.expander("➕ Register New Jira Project", expanded=False):
        with st.form("add_project_form", clear_on_submit=True):
            st.markdown("##### Project Classification Details")
            col_pname, col_pkey = st.columns([3, 1])
            with col_pname:
                p_name = st.text_input("Project Name *", placeholder="e.g. Core Authentication Service")
            with col_pkey:
                p_key = st.text_input("Project Key *", placeholder="e.g. AUTH").upper()

            p_desc = st.text_area(
                "Scope & Responsibilities *",
                placeholder="Explain the technical scope and domain of this project so the AI can accurately match tasks...",
                height=85,
            )

            col_team, col_kw = st.columns(2)
            with col_team:
                p_team = st.text_input("Team / Squad", placeholder="e.g. Security & Identity Squad")
            with col_kw:
                p_keywords = st.text_input("Keywords (comma-separated)", placeholder="auth, oauth, jwt, login, sessions, security")

            p_active = st.checkbox("Enable for AI classification", value=True)

            submit_project = st.form_submit_button("Register Project", type="primary")

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
                            st.success(f"Project [{p_key}] registered successfully!")
                            st.rerun()
                        except ValueError as ve:
                            st.error(str(ve))

    st.markdown("<hr style='margin: 1rem 0; border: none; border-top: 1px solid rgba(255,255,255,0.08);'/>", unsafe_allow_html=True)

    if not filtered_projects:
        st.info("No Jira projects match your search query. Use 'Register New Jira Project' above to add one.")
        return

    # Modern Grid of Projects
    for p in filtered_projects:
        p_id = p["id"]
        is_active = p.get("is_active", True)

        with st.container(border=True):
            col_main, col_toggle, col_del = st.columns([4.5, 1.8, 1])

            with col_main:
                active_dot = "🟢" if is_active else "⚪"
                st.markdown(
                    f"""
                    <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 4px;">
                        <span style="font-size: 0.8rem;">{active_dot}</span>
                        <span style="background: rgba(99, 102, 241, 0.15); color: #A5B4FC; border: 1px solid rgba(99, 102, 241, 0.3); font-size: 0.8rem; font-weight: 700; padding: 2px 8px; border-radius: 6px;">
                            {p.get('project_key')}
                        </span>
                        <span style="font-size: 1.1rem; font-weight: 700; color: #F8FAFC;">
                            {p.get('project_name')}
                        </span>
                        <span style="background: rgba(255,255,255,0.06); color: #94A3B8; font-size: 0.72rem; padding: 2px 7px; border-radius: 4px;">
                            {p.get('team_name') or 'General Team'}
                        </span>
                    </div>
                    <div style="font-size: 0.85rem; color: #94A3B8; margin-bottom: 8px; line-height: 1.4;">
                        {p.get('description') or 'No description provided.'}
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                # Keywords tags
                kws = p.get("keywords") or []
                if kws:
                    kw_badges = " ".join([
                        f'<span style="background: rgba(255, 255, 255, 0.05); color: #CBD5E1; border: 1px solid rgba(255, 255, 255, 0.08); padding: 1px 6px; border-radius: 4px; font-size: 0.72rem;">#{k}</span>'
                        for k in kws
                    ])
                    st.markdown(kw_badges, unsafe_allow_html=True)

            with col_toggle:
                st.write("AI Classification:")
                new_active = st.toggle("Active Context", value=is_active, key=f"active_toggle_{p_id}")
                if new_active != is_active:
                    project_repo.toggle_active(user_id, p_id, new_active)
                    st.rerun()

            with col_del:
                st.write("Manage:")
                if st.button("🗑️ Delete", key=f"del_proj_{p_id}", type="secondary", use_container_width=True):
                    project_repo.delete_project(user_id, p_id)
                    st.rerun()

            # Edit toggle
            with st.expander("✏️ Modify Project Context", expanded=False):
                with st.form(key=f"edit_proj_form_{p_id}"):
                    e_name = st.text_input("Project Name", value=p.get("project_name", ""))
                    e_desc = st.text_area("Scope & Description", value=p.get("description", ""), height=75)
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
                        st.success("Project updated!")
                        st.rerun()

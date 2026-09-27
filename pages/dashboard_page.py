"""
Main Dashboard view for Minute AI.
Displays dynamic summary cards, Plotly charts, and recent activity.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from database.repositories import ActionItemRepository, TranscriptRepository, ProjectRepository
from utils.helpers import get_status_badge, format_iso_date


def render_dashboard_page(user_id: str, access_token: str = None):
    st.markdown(
        """
        <div style="margin-bottom: 1.5rem;">
            <h1 style="font-size: 2rem; font-weight: 700; margin-bottom: 0.2rem; color: #1E293B;">Dashboard</h1>
            <p style="color: #64748B; font-size: 0.95rem; margin: 0;">
                Real-time metrics, project classifications, and transcript processing activity.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    action_repo = ActionItemRepository(access_token)
    transcript_repo = TranscriptRepository(access_token)
    project_repo = ProjectRepository(access_token)

    # 1. Fetch Dynamic Summary Metrics
    metrics = action_repo.get_dashboard_metrics(user_id)

    # 2. Render Summary Cards
    c1, c2, c3, c4, c5, c6 = st.columns(6)

    with c1:
        st.metric(
            label="Total Transcripts",
            value=metrics["total_transcripts"],
            help="Total meeting transcripts uploaded and processed",
        )
    with c2:
        st.metric(
            label="Action Items",
            value=metrics["total_action_items"],
            help="Total tasks extracted across all meetings",
        )
    with c3:
        st.metric(
            label="Awaiting Review",
            value=metrics["awaiting_review"],
            delta=f"{metrics['awaiting_review']} pending" if metrics["awaiting_review"] > 0 else "0",
            delta_color="inverse",
            help="Items in 'Pending Review' status requiring human review",
        )
    with c4:
        st.metric(
            label="Needs Clarification",
            value=metrics["requiring_clarification"],
            delta=f"{metrics['requiring_clarification']} flagged" if metrics["requiring_clarification"] > 0 else "0",
            delta_color="inverse",
            help="Items flagged by AI for missing details or low confidence",
        )
    with c5:
        st.metric(
            label="Approved Tasks",
            value=metrics["approved_items"],
            delta=f"{metrics['approved_items']} ready" if metrics["approved_items"] > 0 else "0",
            delta_color="normal",
            help="Action items approved by the team",
        )
    with c6:
        st.metric(
            label="Jira Projects",
            value=metrics["jira_projects_count"],
            help="Configured Jira target projects",
        )

    st.markdown("<hr style='margin: 1.5rem 0; border: none; border-top: 1px solid #E2E8F0;'/>", unsafe_allow_html=True)

    # 3. Interactive Plotly Charts
    all_items = action_repo.get_action_items(user_id)

    if all_items:
        df_items = pd.DataFrame(all_items)
        df_items["project_display"] = df_items["jira_project_key"].fillna("Unassigned")
        df_items["priority_display"] = df_items["priority"].fillna("Not Specified")

        col_chart_left, col_chart_right = st.columns(2)

        with col_chart_left:
            st.markdown("##### 📁 Action Items by Jira Project")
            proj_counts = df_items["project_display"].value_counts().reset_index()
            proj_counts.columns = ["Project", "Tasks"]

            fig_proj = px.bar(
                proj_counts,
                x="Project",
                y="Tasks",
                text="Tasks",
                color="Project",
                color_discrete_sequence=px.colors.qualitative.Prism,
            )
            fig_proj.update_layout(
                margin=dict(l=20, r=20, t=20, b=20),
                height=280,
                showlegend=False,
                xaxis_title="",
                yaxis_title="Task Count",
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
            )
            fig_proj.update_traces(textposition="outside")
            st.plotly_chart(fig_proj, use_container_width=True)

        with col_chart_right:
            st.markdown("##### 🔄 Action Items by Status")
            status_counts = df_items["status"].value_counts().reset_index()
            status_counts.columns = ["Status", "Count"]

            color_map = {
                "Approved": "#10B981",
                "Pending Review": "#F59E0B",
                "Needs Clarification": "#6366F1",
                "Rejected": "#EF4444",
            }
            fig_status = px.pie(
                status_counts,
                names="Status",
                values="Count",
                hole=0.55,
                color="Status",
                color_discrete_map=color_map,
            )
            fig_status.update_layout(
                margin=dict(l=20, r=20, t=20, b=20),
                height=280,
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
            )
            st.plotly_chart(fig_status, use_container_width=True)

        col_pri, col_time = st.columns(2)

        with col_pri:
            st.markdown("##### ⚡ Action Items by Priority")
            priority_order = ["Highest", "High", "Medium", "Low", "Lowest", "Not Specified"]
            pri_series = df_items["priority_display"].value_counts()
            pri_data = [{"Priority": p, "Count": pri_series.get(p, 0)} for p in priority_order if p in pri_series]

            if pri_data:
                df_pri = pd.DataFrame(pri_data)
                fig_pri = px.bar(
                    df_pri,
                    x="Count",
                    y="Priority",
                    orientation="h",
                    text="Count",
                    color="Priority",
                    color_discrete_map={
                        "Highest": "#DC2626",
                        "High": "#EA580C",
                        "Medium": "#D97706",
                        "Low": "#2563EB",
                        "Lowest": "#64748B",
                        "Not Specified": "#94A3B8",
                    },
                )
                fig_pri.update_layout(
                    margin=dict(l=20, r=20, t=20, b=20),
                    height=260,
                    showlegend=False,
                    xaxis_title="Tasks",
                    yaxis_title="",
                    yaxis=dict(autorange="reversed"),
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                )
                fig_pri.update_traces(textposition="outside")
                st.plotly_chart(fig_pri, use_container_width=True)

        with col_time:
            st.markdown("##### 📈 Extraction Activity Over Time")
            # Extract date from created_at
            df_items["date_created"] = pd.to_datetime(df_items["created_at"]).dt.date
            time_counts = df_items.groupby("date_created").size().reset_index(name="Tasks Extracted")
            time_counts = time_counts.sort_values("date_created")

            fig_time = px.area(
                time_counts,
                x="date_created",
                y="Tasks Extracted",
                markers=True,
                color_discrete_sequence=["#3B82F6"],
            )
            fig_time.update_layout(
                margin=dict(l=20, r=20, t=20, b=20),
                height=260,
                xaxis_title="",
                yaxis_title="Tasks",
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
            )
            st.plotly_chart(fig_time, use_container_width=True)

    else:
        st.info("No action items available yet. Process a meeting transcript to generate visual metrics.")

    st.markdown("<hr style='margin: 1.5rem 0; border: none; border-top: 1px solid #E2E8F0;'/>", unsafe_allow_html=True)

    # 4. Recent Activity Table
    col_act_header, col_act_btn = st.columns([4, 1])
    with col_act_header:
        st.markdown("### 🕒 Recent Meeting Transcripts")
    with col_act_btn:
        if st.button("➕ Process Transcript", type="primary", use_container_width=True):
            st.session_state["nav_selection"] = "Process Transcript"
            st.rerun()

    transcripts = transcript_repo.get_transcripts(user_id)

    if transcripts:
        recent_transcripts = transcripts[:5]
        for tr in recent_transcripts:
            with st.container(border=True):
                c_title, c_date, c_items, c_status, c_act = st.columns([3, 1.5, 1.5, 1.5, 1.5])
                with c_title:
                    st.markdown(f"**{tr.get('meeting_name')}**")
                    st.caption(f"Source: `{tr.get('source_type', 'paste').upper()}`")
                with c_date:
                    st.write(f"📅 {tr.get('meeting_date')}")
                    st.caption(f"Processed: {format_iso_date(tr.get('created_at'))}")
                with c_items:
                    st.markdown(f"**{tr.get('action_item_count', 0)}** items")
                    st.caption(f"{tr.get('approved_count', 0)} approved")
                with c_status:
                    stat = tr.get("processing_status", "processed").title()
                    badge_color = "#10B981" if stat == "Processed" else "#F59E0B"
                    st.markdown(
                        f'<span style="background-color: #E2E8F0; color: #1E293B; padding: 3px 8px; border-radius: 4px; font-size: 0.8rem; font-weight: 600;">{stat}</span>',
                        unsafe_allow_html=True,
                    )
                with c_act:
                    if st.button("View Items", key=f"dash_view_{tr.get('id')}", use_container_width=True):
                        st.session_state["filter_transcript_id"] = tr.get("id")
                        st.session_state["nav_selection"] = "Action Items"
                        st.rerun()
    else:
        st.write("No transcripts uploaded yet.")

"""
Main Dashboard view for Minute AI.
Modern Dark Enterprise SaaS Analytics with Plotly Charts and Real-Time Metrics.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from database.repositories import ActionItemRepository, TranscriptRepository, ProjectRepository
from utils.helpers import get_status_badge, format_iso_date


def render_dashboard_page(user_id: str, access_token: str = None):
    # Hero Section
    col_hero_left, col_hero_right = st.columns([3.5, 1.5])
    with col_hero_left:
        st.markdown(
            """
            <div style="margin-bottom: 1.2rem;">
                <div style="display: inline-flex; align-items: center; gap: 6px; background: rgba(99, 102, 241, 0.12); border: 1px solid rgba(99, 102, 241, 0.3); padding: 4px 10px; border-radius: 9999px; font-size: 0.75rem; font-weight: 600; color: #A5B4FC; margin-bottom: 8px;">
                    <span style="width: 6px; height: 6px; border-radius: 50%; background: #10B981; box-shadow: 0 0 8px #10B981;"></span>
                    Live AI Engine Connected • Whisper V3 & Qwen 2.5
                </div>
                <h1 style="font-size: 2.2rem; font-weight: 800; color: #F8FAFC; margin: 0; letter-spacing: -0.03em;">
                    Meeting Intelligence Dashboard
                </h1>
                <p style="color: #94A3B8; font-size: 0.95rem; margin-top: 4px;">
                    Automated meeting action item extraction, Jira project mappings, and team commitment tracking.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col_hero_right:
        st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)
        if st.button("⚡ Process New Transcript", type="primary", use_container_width=True):
            st.session_state["nav_selection"] = "Process Transcript"
            st.rerun()

    action_repo = ActionItemRepository(access_token)
    transcript_repo = TranscriptRepository(access_token)
    project_repo = ProjectRepository(access_token)

    # Fetch Metrics
    metrics = action_repo.get_dashboard_metrics(user_id)

    # 1. Sleek Metric Cards
    c1, c2, c3, c4, c5, c6 = st.columns(6)

    def render_metric_card(title, value, subtitle, icon, color):
        return f"""
        <div style="background: #111827; border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 12px; padding: 14px 16px; box-shadow: 0 4px 12px rgba(0,0,0,0.3); position: relative; overflow: hidden;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                <span style="font-size: 0.72rem; font-weight: 700; color: #94A3B8; text-transform: uppercase; letter-spacing: 0.06em;">{title}</span>
                <span style="font-size: 1.1rem;">{icon}</span>
            </div>
            <div style="font-size: 1.85rem; font-weight: 800; color: #F8FAFC; letter-spacing: -0.02em; line-height: 1;">
                {value}
            </div>
            <div style="font-size: 0.72rem; font-weight: 600; color: {color}; margin-top: 6px;">
                {subtitle}
            </div>
        </div>
        """

    with c1:
        st.markdown(render_metric_card("Transcripts", metrics["total_transcripts"], "Uploaded meetings", "📜", "#94A3B8"), unsafe_allow_html=True)
    with c2:
        st.markdown(render_metric_card("Action Items", metrics["total_action_items"], "Extracted tasks", "🎯", "#60A5FA"), unsafe_allow_html=True)
    with c3:
        st.markdown(render_metric_card("Awaiting Review", metrics["awaiting_review"], "Needs sign-off", "⏳", "#FBBF24" if metrics["awaiting_review"] > 0 else "#94A3B8"), unsafe_allow_html=True)
    with c4:
        st.markdown(render_metric_card("Clarifications", metrics["requiring_clarification"], "Flagged by AI", "❓", "#A5B4FC" if metrics["requiring_clarification"] > 0 else "#94A3B8"), unsafe_allow_html=True)
    with c5:
        st.markdown(render_metric_card("Approved", metrics["approved_items"], "Ready for Jira", "✅", "#34D399"), unsafe_allow_html=True)
    with c6:
        st.markdown(render_metric_card("Jira Targets", metrics["jira_projects_count"], "Active projects", "📁", "#818CF8"), unsafe_allow_html=True)

    st.markdown("<div style='height: 1.4rem;'></div>", unsafe_allow_html=True)

    # 2. Modern Plotly Analytics
    all_items = action_repo.get_action_items(user_id)

    if all_items:
        df_items = pd.DataFrame(all_items)
        df_items["project_display"] = df_items["jira_project_key"].fillna("Unassigned")
        df_items["priority_display"] = df_items["priority"].fillna("Not Specified")

        col_chart_left, col_chart_right = st.columns(2)

        # Plotly dark template helper
        def apply_dark_layout(fig, height=270):
            fig.update_layout(
                margin=dict(l=10, r=10, t=10, b=10),
                height=height,
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(family="Plus Jakarta Sans, sans-serif", color="#94A3B8", size=11),
                xaxis=dict(gridcolor="rgba(255,255,255,0.06)", zerolinecolor="rgba(255,255,255,0.06)"),
                yaxis=dict(gridcolor="rgba(255,255,255,0.06)", zerolinecolor="rgba(255,255,255,0.06)"),
            )
            return fig

        with col_chart_left:
            st.markdown(
                """
                <div style="background: #111827; border: 1px solid rgba(255,255,255,0.08); border-radius: 12px; padding: 14px; margin-bottom: 1rem;">
                    <div style="font-weight: 700; font-size: 0.95rem; color: #F8FAFC; margin-bottom: 4px;">📁 Tasks by Jira Project</div>
                    <div style="font-size: 0.75rem; color: #64748B; margin-bottom: 12px;">Distribution across configured project keys</div>
                """,
                unsafe_allow_html=True,
            )
            proj_counts = df_items["project_display"].value_counts().reset_index()
            proj_counts.columns = ["Project", "Tasks"]

            fig_proj = px.bar(
                proj_counts,
                x="Project",
                y="Tasks",
                text="Tasks",
                color="Project",
                color_discrete_sequence=["#6366F1", "#8B5CF6", "#06B6D4", "#10B981", "#F59E0B"],
            )
            fig_proj.update_traces(
                textposition="outside",
                marker=dict(line=dict(width=0)),
                width=0.45,
            )
            apply_dark_layout(fig_proj)
            fig_proj.update_layout(showlegend=False, xaxis_title="", yaxis_title="")
            st.plotly_chart(fig_proj, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

        with col_chart_right:
            st.markdown(
                """
                <div style="background: #111827; border: 1px solid rgba(255,255,255,0.08); border-radius: 12px; padding: 14px; margin-bottom: 1rem;">
                    <div style="font-weight: 700; font-size: 0.95rem; color: #F8FAFC; margin-bottom: 4px;">🔄 Review Pipeline Status</div>
                    <div style="font-size: 0.75rem; color: #64748B; margin-bottom: 12px;">Human review triage breakdown</div>
                """,
                unsafe_allow_html=True,
            )
            status_counts = df_items["status"].value_counts().reset_index()
            status_counts.columns = ["Status", "Count"]

            fig_status = px.pie(
                status_counts,
                names="Status",
                values="Count",
                hole=0.62,
                color="Status",
                color_discrete_map={
                    "Approved": "#10B981",
                    "Pending Review": "#F59E0B",
                    "Needs Clarification": "#6366F1",
                    "Rejected": "#F43F5E",
                },
            )
            fig_status.update_traces(
                textinfo="percent+value",
                marker=dict(line=dict(color="#111827", width=2)),
            )
            apply_dark_layout(fig_status)
            fig_status.update_layout(showlegend=True, legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5))
            st.plotly_chart(fig_status, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

        col_pri, col_time = st.columns(2)

        with col_pri:
            st.markdown(
                """
                <div style="background: #111827; border: 1px solid rgba(255,255,255,0.08); border-radius: 12px; padding: 14px; margin-bottom: 1rem;">
                    <div style="font-weight: 700; font-size: 0.95rem; color: #F8FAFC; margin-bottom: 4px;">⚡ Tasks by Urgency & Priority</div>
                    <div style="font-size: 0.75rem; color: #64748B; margin-bottom: 12px;">Explicit priority levels identified by AI</div>
                """,
                unsafe_allow_html=True,
            )
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
                        "Highest": "#EF4444",
                        "High": "#F97316",
                        "Medium": "#FBBF24",
                        "Low": "#38BDF8",
                        "Lowest": "#64748B",
                        "Not Specified": "#475569",
                    },
                )
                fig_pri.update_traces(
                    textposition="outside",
                    width=0.45,
                )
                apply_dark_layout(fig_pri, height=250)
                fig_pri.update_layout(showlegend=False, xaxis_title="", yaxis_title="", yaxis=dict(autorange="reversed"))
                st.plotly_chart(fig_pri, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

        with col_time:
            st.markdown(
                """
                <div style="background: #111827; border: 1px solid rgba(255,255,255,0.08); border-radius: 12px; padding: 14px; margin-bottom: 1rem;">
                    <div style="font-weight: 700; font-size: 0.95rem; color: #F8FAFC; margin-bottom: 4px;">📈 Extraction Velocity</div>
                    <div style="font-size: 0.75rem; color: #64748B; margin-bottom: 12px;">Action items captured over time</div>
                """,
                unsafe_allow_html=True,
            )
            df_items["date_created"] = pd.to_datetime(df_items["created_at"]).dt.date
            time_counts = df_items.groupby("date_created").size().reset_index(name="Tasks")
            time_counts = time_counts.sort_values("date_created")

            fig_time = px.area(
                time_counts,
                x="date_created",
                y="Tasks",
                markers=True,
                color_discrete_sequence=["#818CF8"],
            )
            apply_dark_layout(fig_time, height=250)
            fig_time.update_layout(xaxis_title="", yaxis_title="")
            st.plotly_chart(fig_time, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

    else:
        st.info("No action items available yet. Process your first meeting transcript above.")

    st.markdown("<div style='height: 1.5rem;'></div>", unsafe_allow_html=True)

    # 3. Recent Transcripts Table / Feed
    st.markdown(
        """
        <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px;">
            <div>
                <h3 style="margin: 0; font-size: 1.15rem; font-weight: 800; color: #F8FAFC; letter-spacing: -0.02em;">
                    🕒 Recent Meetings Archive
                </h3>
                <span style="font-size: 0.78rem; color: #94A3B8;">Direct access to latest parsed discussions</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    transcripts = transcript_repo.get_transcripts(user_id)

    if transcripts:
        for tr in transcripts[:5]:
            with st.container(border=True):
                c_title, c_date, c_items, c_status, c_act = st.columns([3.5, 1.5, 1.5, 1.2, 1.3])
                with c_title:
                    st.markdown(f"**{tr.get('meeting_name')}**")
                    st.markdown(
                        f'<span style="background: rgba(255,255,255,0.06); color: #94A3B8; font-size: 0.7rem; padding: 2px 6px; border-radius: 4px; font-family: monospace;">'
                        f'{tr.get("source_type", "paste").upper()}</span>',
                        unsafe_allow_html=True,
                    )
                with c_date:
                    st.write(f"📅 {tr.get('meeting_date')}")
                    st.caption(f"{format_iso_date(tr.get('created_at'))}")
                with c_items:
                    st.markdown(f"**{tr.get('action_item_count', 0)}** items")
                    st.caption(f"✅ {tr.get('approved_count', 0)} approved")
                with c_status:
                    stat = tr.get("processing_status", "processed").title()
                    badge_bg = "rgba(16, 185, 129, 0.12)" if stat == "Processed" else "rgba(245, 158, 11, 0.12)"
                    badge_col = "#34D399" if stat == "Processed" else "#FBBF24"
                    st.markdown(
                        f'<span style="background: {badge_bg}; color: {badge_col}; padding: 3px 8px; border-radius: 6px; font-size: 0.75rem; font-weight: 600;">{stat}</span>',
                        unsafe_allow_html=True,
                    )
                with c_act:
                    if st.button("Inspect →", key=f"dash_view_{tr.get('id')}", use_container_width=True, type="secondary"):
                        st.session_state["filter_transcript_id"] = tr.get("id")
                        st.session_state["nav_selection"] = "Action Items"
                        st.rerun()
    else:
        st.write("No transcripts uploaded yet.")

"""
Main Dashboard view for Minute AI.
Stitch Design System: Executive Precision (Warm Minimalist Light Mode, 12-Column Grid).
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from database.repositories import ActionItemRepository, TranscriptRepository, ProjectRepository
from utils.helpers import get_status_badge, format_iso_date


def render_dashboard_page(user_id: str, access_token: str = None):
    action_repo = ActionItemRepository(access_token)
    transcript_repo = TranscriptRepository(access_token)
    project_repo = ProjectRepository(access_token)

    # 1. Executive Welcome Hero Banner
    col_hero_text, col_hero_action = st.columns([3.8, 1.2])
    with col_hero_text:
        st.markdown(
            """
            <div style="background: #FFFFFF; border: 1px solid #E5E7EB; border-radius: 14px; padding: 18px 24px; box-shadow: 0 1px 3px rgba(0,0,0,0.03); margin-bottom: 1.2rem;">
                <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 4px;">
                    <span style="background: #ECFDF5; color: #065F46; border: 1px solid #A7F3D0; font-size: 0.72rem; font-weight: 700; padding: 2px 7px; border-radius: 9999px; display: inline-flex; align-items: center; gap: 4px;">
                        <span style="width: 6px; height: 6px; border-radius: 50%; background: #10B981;"></span>
                        Live AI Engine Online
                    </span>
                    <span style="color: #9CA3AF; font-size: 0.8rem;">•</span>
                    <span style="font-size: 0.78rem; color: #6B7280; font-weight: 500;">Whisper Large V3 & Qwen 2.5</span>
                </div>
                <h2 style="font-size: 1.65rem; font-weight: 800; color: #111827; margin: 0 0 4px 0; letter-spacing: -0.025em;">
                    Meeting Action Item Intelligence
                </h2>
                <div style="font-size: 0.88rem; color: #4B5563; line-height: 1.4;">
                    Transforming conversational meeting audio & transcripts into reviewable, classified Jira action items.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col_hero_action:
        st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
        if st.button("➕ Process Transcript", type="primary", use_container_width=True):
            st.session_state["nav_selection"] = "Process Transcript"
            st.rerun()

    # 2. Fetch Dynamic KPI Metrics
    metrics = action_repo.get_dashboard_metrics(user_id)

    # 3. 6 Summary Cards
    c1, c2, c3, c4, c5, c6 = st.columns(6)

    def render_kpi_card(title, value, subtitle, icon, text_color):
        return f"""
        <div style="background: #FFFFFF; border: 1px solid #E5E7EB; border-radius: 12px; padding: 14px 16px; box-shadow: 0 1px 3px rgba(0, 0, 0, 0.03);">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                <span style="font-size: 0.72rem; font-weight: 700; color: #6B7280; text-transform: uppercase; letter-spacing: 0.05em;">{title}</span>
                <span style="font-size: 1.05rem;">{icon}</span>
            </div>
            <div style="font-size: 1.95rem; font-weight: 800; color: #111827; letter-spacing: -0.03em; line-height: 1.1;">
                {value}
            </div>
            <div style="font-size: 0.73rem; font-weight: 600; color: {text_color}; margin-top: 5px;">
                {subtitle}
            </div>
        </div>
        """

    with c1:
        st.markdown(render_kpi_card("Transcripts", metrics["total_transcripts"], "Meetings analyzed", "📜", "#6B7280"), unsafe_allow_html=True)
    with c2:
        st.markdown(render_kpi_card("Action Items", metrics["total_action_items"], "Extracted tasks", "🎯", "#4F46E5"), unsafe_allow_html=True)
    with c3:
        st.markdown(render_kpi_card("Pending Review", metrics["awaiting_review"], "Awaiting approval", "⏳", "#D97706" if metrics["awaiting_review"] > 0 else "#6B7280"), unsafe_allow_html=True)
    with c4:
        st.markdown(render_kpi_card("Clarifications", metrics["requiring_clarification"], "Flagged by AI", "❓", "#4338CA" if metrics["requiring_clarification"] > 0 else "#6B7280"), unsafe_allow_html=True)
    with c5:
        st.markdown(render_kpi_card("Approved", metrics["approved_items"], "Ready for Jira", "✅", "#059669"), unsafe_allow_html=True)
    with c6:
        st.markdown(render_kpi_card("Jira Targets", metrics["jira_projects_count"], "Active projects", "📁", "#3B82F6"), unsafe_allow_html=True)

    st.markdown("<div style='height: 1.4rem;'></div>", unsafe_allow_html=True)

    # 4. Analytics & Charts
    all_items = action_repo.get_action_items(user_id)

    if all_items:
        df_items = pd.DataFrame(all_items)
        df_items["project_display"] = df_items["jira_project_key"].fillna("Unassigned")
        df_items["priority_display"] = df_items["priority"].fillna("Not Specified")

        col_chart_left, col_chart_right = st.columns(2)

        def apply_stitch_light_layout(fig, height=270):
            fig.update_layout(
                margin=dict(l=10, r=10, t=10, b=10),
                height=height,
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(family="Inter, sans-serif", color="#4B5563", size=11),
                xaxis=dict(gridcolor="#F3F4F6", zerolinecolor="#E5E7EB"),
                yaxis=dict(gridcolor="#F3F4F6", zerolinecolor="#E5E7EB"),
            )
            return fig

        with col_chart_left:
            st.markdown(
                """
                <div style="background: #FFFFFF; border: 1px solid #E5E7EB; border-radius: 12px; padding: 16px; margin-bottom: 1rem; box-shadow: 0 1px 3px rgba(0,0,0,0.03);">
                    <div style="font-weight: 700; font-size: 0.95rem; color: #111827; margin-bottom: 2px;">📁 Tasks by Jira Project</div>
                    <div style="font-size: 0.75rem; color: #6B7280; margin-bottom: 12px;">Task volume distribution across configured Jira targets</div>
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
                color_discrete_sequence=["#4F46E5", "#0D9488", "#0284C7", "#10B981", "#F59E0B"],
            )
            fig_proj.update_traces(
                textposition="outside",
                width=0.45,
            )
            apply_stitch_light_layout(fig_proj)
            fig_proj.update_layout(showlegend=False, xaxis_title="", yaxis_title="")
            st.plotly_chart(fig_proj, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

        with col_chart_right:
            st.markdown(
                """
                <div style="background: #FFFFFF; border: 1px solid #E5E7EB; border-radius: 12px; padding: 16px; margin-bottom: 1rem; box-shadow: 0 1px 3px rgba(0,0,0,0.03);">
                    <div style="font-weight: 700; font-size: 0.95rem; color: #111827; margin-bottom: 2px;">🔄 Review Pipeline Status</div>
                    <div style="font-size: 0.75rem; color: #6B7280; margin-bottom: 12px;">Human review triage breakdown</div>
                """,
                unsafe_allow_html=True,
            )
            status_counts = df_items["status"].value_counts().reset_index()
            status_counts.columns = ["Status", "Count"]

            fig_status = px.pie(
                status_counts,
                names="Status",
                values="Count",
                hole=0.60,
                color="Status",
                color_discrete_map={
                    "Approved": "#10B981",
                    "Pending Review": "#F59E0B",
                    "Needs Clarification": "#4F46E5",
                    "Rejected": "#EF4444",
                },
            )
            fig_status.update_traces(
                textinfo="percent+value",
                marker=dict(line=dict(color="#FFFFFF", width=2)),
            )
            apply_stitch_light_layout(fig_status)
            fig_status.update_layout(showlegend=True, legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5))
            st.plotly_chart(fig_status, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

        col_pri, col_time = st.columns(2)

        with col_pri:
            st.markdown(
                """
                <div style="background: #FFFFFF; border: 1px solid #E5E7EB; border-radius: 12px; padding: 16px; margin-bottom: 1rem; box-shadow: 0 1px 3px rgba(0,0,0,0.03);">
                    <div style="font-weight: 700; font-size: 0.95rem; color: #111827; margin-bottom: 2px;">⚡ Tasks by Priority</div>
                    <div style="font-size: 0.75rem; color: #6B7280; margin-bottom: 12px;">Identified urgency levels</div>
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
                        "Highest": "#DC2626",
                        "High": "#EA580C",
                        "Medium": "#CA8A04",
                        "Low": "#0284C7",
                        "Lowest": "#64748B",
                        "Not Specified": "#94A3B8",
                    },
                )
                fig_pri.update_traces(textposition="outside", width=0.45)
                apply_stitch_light_layout(fig_pri, height=250)
                fig_pri.update_layout(showlegend=False, xaxis_title="", yaxis_title="", yaxis=dict(autorange="reversed"))
                st.plotly_chart(fig_pri, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

        with col_time:
            st.markdown(
                """
                <div style="background: #FFFFFF; border: 1px solid #E5E7EB; border-radius: 12px; padding: 16px; margin-bottom: 1rem; box-shadow: 0 1px 3px rgba(0,0,0,0.03);">
                    <div style="font-weight: 700; font-size: 0.95rem; color: #111827; margin-bottom: 2px;">📈 Extraction Velocity</div>
                    <div style="font-size: 0.75rem; color: #6B7280; margin-bottom: 12px;">Action items captured over time</div>
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
                color_discrete_sequence=["#4F46E5"],
            )
            apply_stitch_light_layout(fig_time, height=250)
            fig_time.update_layout(xaxis_title="", yaxis_title="")
            st.plotly_chart(fig_time, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

    else:
        st.info("No action items available yet. Process your first meeting transcript.")

    st.markdown("<div style='height: 1.2rem;'></div>", unsafe_allow_html=True)

    # 5. Recent Transcripts List
    st.markdown(
        """
        <div style="margin-bottom: 10px;">
            <h3 style="margin: 0; font-size: 1.15rem; font-weight: 800; color: #111827; letter-spacing: -0.02em;">
                🕒 Recent Meeting Discussions
            </h3>
            <span style="font-size: 0.78rem; color: #6B7280;">Quick inspection and task drill-down</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    transcripts = transcript_repo.get_transcripts(user_id)

    if transcripts:
        for tr in transcripts[:5]:
            with st.container(border=True):
                c_title, c_date, c_items, c_status, c_act = st.columns([3.6, 1.6, 1.6, 1.2, 1.2])
                with c_title:
                    st.markdown(f"**{tr.get('meeting_name')}**")
                    st.markdown(
                        f'<span style="background: #F1F3F5; color: #4B5563; font-size: 0.7rem; padding: 2px 6px; border-radius: 4px; font-family: monospace; font-weight: 600;">'
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
                    badge_bg = "#ECFDF5" if stat == "Processed" else "#FFFBEB"
                    badge_col = "#065F46" if stat == "Processed" else "#92400E"
                    badge_border = "#A7F3D0" if stat == "Processed" else "#FDE68A"
                    st.markdown(
                        f'<span style="background: {badge_bg}; color: {badge_col}; border: 1px solid {badge_border}; padding: 3px 8px; border-radius: 6px; font-size: 0.73rem; font-weight: 600;">{stat}</span>',
                        unsafe_allow_html=True,
                    )
                with c_act:
                    if st.button("View Items →", key=f"dash_view_{tr.get('id')}", use_container_width=True, type="secondary"):
                        st.session_state["filter_transcript_id"] = tr.get("id")
                        st.session_state["nav_selection"] = "Action Items"
                        st.rerun()
    else:
        st.write("No transcripts uploaded yet.")

"""
Minute AI - Main Streamlit Application Entrypoint.
AI-Powered Meeting Transcript to Jira Action Item Dashboard.
"""

import streamlit as st
from utils.auth import is_authenticated, get_current_user, render_auth_page, logout
from pages import (
    render_dashboard_page,
    render_process_transcript_page,
    render_action_items_page,
    render_transcript_history_page,
    render_jira_projects_page,
    render_settings_page,
)

# Page configuration
st.set_page_config(
    page_title="Minute AI — Transcript to Jira Action Item Dashboard",
    page_icon="⏱️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Inject custom modern CSS
st.markdown(
    """
    <style>
    /* Global Styles */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    /* Main container padding */
    .block-container {
        padding-top: 1.8rem;
        padding-bottom: 3rem;
        max-width: 1280px;
    }
    
    /* Cards and Containers */
    [data-testid="stMetricValue"] {
        font-size: 1.85rem !important;
        font-weight: 700 !important;
        color: #0F172A;
    }
    
    [data-testid="stMetricLabel"] {
        font-size: 0.85rem !important;
        font-weight: 600 !important;
        color: #64748B;
        text-transform: uppercase;
        letter-spacing: 0.04em;
    }
    
    /* Modern sidebar styling */
    [data-testid="stSidebar"] {
        background-color: #F8FAFC;
        border-right: 1px solid #E2E8F0;
    }
    
    /* Subtle rounded buttons */
    .stButton > button {
        border-radius: 8px;
        font-weight: 500;
        transition: all 0.15s ease;
    }
    
    /* Badges */
    .badge-pill {
        display: inline-block;
        padding: 3px 8px;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 600;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

def main():
    # 1. Enforce Authentication Guard
    if not is_authenticated():
        render_auth_page()
        return

    user = get_current_user()
    user_id = user["id"]
    access_token = user.get("access_token")

    # 2. Sidebar Branding & Navigation
    with st.sidebar:
        st.markdown(
            """
            <div style="display: flex; align-items: center; gap: 10px; padding: 0.5rem 0 1.2rem 0;">
                <span style="font-size: 2rem;">⏱️</span>
                <div>
                    <h2 style="margin: 0; font-size: 1.35rem; font-weight: 700; color: #0F172A; line-height: 1.2;">Minute AI</h2>
                    <span style="font-size: 0.78rem; color: #64748B; font-weight: 500;">Meeting to Jira Actions</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        nav_options = [
            "📊 Dashboard",
            "📝 Process Transcript",
            "✅ Action Items",
            "📜 Transcript History",
            "📁 Jira Projects",
            "⚙️ Settings",
        ]

        # Handle programmatic navigation redirects
        default_index = 0
        if "nav_selection" in st.session_state:
            target = st.session_state.pop("nav_selection")
            for idx, opt in enumerate(nav_options):
                if target in opt:
                    default_index = idx
                    break

        nav_choice = st.radio(
            "Navigation",
            nav_options,
            index=default_index,
            label_visibility="collapsed",
        )

        st.markdown("---")

        # User profile badge and logout
        is_demo = user.get("is_demo", False)
        st.markdown(
            f"""
            <div style="background-color: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 8px; padding: 10px 12px; margin-bottom: 10px;">
                <div style="font-weight: 600; font-size: 0.9rem; color: #1E293B;">
                    👤 {user.get('full_name', 'User')}
                </div>
                <div style="font-size: 0.78rem; color: #64748B;">
                    {user.get('email', '')}
                </div>
                {f'<span style="background-color: #EFF6FF; color: #1D4ED8; font-size: 0.7rem; font-weight: 600; padding: 2px 6px; border-radius: 4px; display: inline-block; margin-top: 4px;">Demo Mode</span>' if is_demo else ''}
            </div>
            """,
            unsafe_allow_html=True,
        )

        if st.button("🚪 Sign Out", use_container_width=True):
            logout()

    # 3. Page Routing
    if "Dashboard" in nav_choice:
        render_dashboard_page(user_id, access_token)
    elif "Process Transcript" in nav_choice:
        render_process_transcript_page(user_id, access_token)
    elif "Action Items" in nav_choice:
        render_action_items_page(user_id, access_token)
    elif "Transcript History" in nav_choice:
        render_transcript_history_page(user_id, access_token)
    elif "Jira Projects" in nav_choice:
        render_jira_projects_page(user_id, access_token)
    elif "Settings" in nav_choice:
        render_settings_page(user_id, access_token)


if __name__ == "__main__":
    main()

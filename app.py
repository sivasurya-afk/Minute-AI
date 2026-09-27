"""
Minute AI - Main Streamlit Application Entrypoint.
AI-Powered Meeting Transcript to Jira Action Item Dashboard.
Custom Enterprise SaaS Dark Theme.
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
    page_title="Minute AI — Meeting Intelligence to Jira",
    page_icon="⏱️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Inject custom modern enterprise CSS
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif !important;
        letter-spacing: -0.01em;
    }
    
    /* Top Header & Padding */
    .block-container {
        padding-top: 2rem !important;
        padding-bottom: 4rem !important;
        max-width: 1320px !important;
    }
    
    /* Custom Scrollbars */
    ::-webkit-scrollbar {
        width: 6px;
        height: 6px;
    }
    ::-webkit-scrollbar-track {
        background: #0B0F17;
    }
    ::-webkit-scrollbar-thumb {
        background: #1E293B;
        border-radius: 4px;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: #334155;
    }

    /* Modern elevated cards */
    .saas-card {
        background: #111827;
        border: 1px solid rgba(255, 255, 255, 0.07);
        border-radius: 12px;
        padding: 1.25rem;
        box-shadow: 0 4px 20px -2px rgba(0, 0, 0, 0.4);
        transition: transform 0.15s ease, border-color 0.15s ease;
    }
    .saas-card:hover {
        border-color: rgba(99, 102, 241, 0.35);
    }
    
    /* Hero Banner */
    .hero-banner {
        background: linear-gradient(135deg, rgba(30, 41, 59, 0.7) 0%, rgba(15, 23, 42, 0.9) 100%);
        border: 1px solid rgba(99, 102, 241, 0.2);
        border-radius: 16px;
        padding: 1.6rem 2rem;
        margin-bottom: 1.8rem;
        position: relative;
        overflow: hidden;
    }
    .hero-banner::after {
        content: "";
        position: absolute;
        top: -50%;
        right: -10%;
        width: 300px;
        height: 300px;
        background: radial-gradient(circle, rgba(99, 102, 241, 0.15) 0%, transparent 70%);
        pointer-events: none;
    }

    /* Metric cards override */
    [data-testid="stMetric"] {
        background: #131B2A !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        border-radius: 12px !important;
        padding: 1rem 1.2rem !important;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2) !important;
    }
    [data-testid="stMetricValue"] {
        font-size: 2rem !important;
        font-weight: 800 !important;
        color: #F8FAFC !important;
        letter-spacing: -0.03em !important;
    }
    [data-testid="stMetricLabel"] {
        font-size: 0.78rem !important;
        font-weight: 600 !important;
        color: #94A3B8 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.05em !important;
    }

    /* Modern Buttons */
    .stButton > button {
        border-radius: 8px !important;
        font-weight: 600 !important;
        font-size: 0.88rem !important;
        padding: 0.45rem 1rem !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1) !important;
    }
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #6366F1 0%, #4F46E5 100%) !important;
        color: #FFFFFF !important;
        border: 1px solid rgba(255, 255, 255, 0.15) !important;
        box-shadow: 0 4px 14px rgba(79, 70, 229, 0.35) !important;
    }
    .stButton > button[kind="primary"]:hover {
        transform: translateY(-1px) !important;
        box-shadow: 0 6px 20px rgba(79, 70, 229, 0.5) !important;
    }
    .stButton > button[kind="secondary"]:hover {
        border-color: rgba(99, 102, 241, 0.4) !important;
        background: #1E293B !important;
    }

    /* Form Inputs */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea,
    .stSelectbox > div > div {
        background-color: #0F172A !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 8px !important;
        color: #F8FAFC !important;
    }
    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {
        border-color: #6366F1 !important;
        box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.25) !important;
    }

    /* Modern Sidebar */
    [data-testid="stSidebar"] {
        background-color: #0B0F17 !important;
        border-right: 1px solid rgba(255, 255, 255, 0.08) !important;
    }
    [data-testid="stSidebar"] hr {
        border-color: rgba(255, 255, 255, 0.08) !important;
    }

    /* Sidebar Radio Navigation Pill Overhaul */
    [data-testid="stSidebar"] [data-testid="stRadio"] > div {
        gap: 6px !important;
    }
    [data-testid="stSidebar"] [data-testid="stRadio"] label {
        padding: 8px 12px !important;
        border-radius: 8px !important;
        transition: all 0.15s ease !important;
        cursor: pointer !important;
        background: transparent !important;
        border: 1px solid transparent !important;
        width: 100% !important;
    }
    [data-testid="stSidebar"] [data-testid="stRadio"] label:hover {
        background: rgba(255, 255, 255, 0.04) !important;
        border-color: rgba(255, 255, 255, 0.06) !important;
    }
    [data-testid="stSidebar"] [data-testid="stRadio"] label:has(input:checked) {
        background: rgba(99, 102, 241, 0.12) !important;
        border: 1px solid rgba(99, 102, 241, 0.3) !important;
        color: #A5B4FC !important;
        font-weight: 600 !important;
    }
    [data-testid="stSidebar"] [data-testid="stRadio"] input {
        display: none !important;
    }

    /* Tabs Pill Overhaul */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px !important;
        background: #0F172A !important;
        padding: 6px !important;
        border-radius: 10px !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 6px !important;
        padding: 6px 14px !important;
        color: #94A3B8 !important;
        font-weight: 500 !important;
        font-size: 0.84rem !important;
        border: none !important;
        background: transparent !important;
    }
    .stTabs [aria-selected="true"] {
        background: #1E293B !important;
        color: #F8FAFC !important;
        font-weight: 600 !important;
        box-shadow: 0 1px 3px rgba(0,0,0,0.3) !important;
    }

    /* Expanders */
    [data-testid="stExpander"] {
        background: #111827 !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        border-radius: 10px !important;
    }

    /* Monospace / Code */
    code {
        font-family: 'JetBrains Mono', monospace !important;
        font-size: 0.8rem !important;
        background: rgba(255, 255, 255, 0.06) !important;
        padding: 2px 5px !important;
        border-radius: 4px !important;
        color: #CBD5E1 !important;
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
            <div style="padding: 0.4rem 0 1.2rem 0;">
                <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 6px;">
                    <div style="width: 36px; height: 36px; border-radius: 9px; background: linear-gradient(135deg, #6366F1, #8B5CF6); display: flex; align-items: center; justify-content: center; font-size: 1.2rem; box-shadow: 0 0 15px rgba(99, 102, 241, 0.4);">
                        ⏱️
                    </div>
                    <div>
                        <div style="font-size: 1.25rem; font-weight: 800; color: #F8FAFC; line-height: 1.1; letter-spacing: -0.02em;">
                            Minute AI
                        </div>
                        <span style="font-size: 0.72rem; color: #6366F1; font-weight: 600; text-transform: uppercase; letter-spacing: 0.06em;">
                            Action Intelligence
                        </span>
                    </div>
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

        st.markdown("<hr style='margin: 1.2rem 0; border: none; border-top: 1px solid rgba(255,255,255,0.08);'/>", unsafe_allow_html=True)

        # User profile badge and logout
        is_demo = user.get("is_demo", False)
        initials = "".join([part[0].upper() for part in user.get('full_name', 'U').split()[:2]]) or "U"
        
        st.markdown(
            f"""
            <div style="background: #111827; border: 1px solid rgba(255,255,255,0.08); border-radius: 10px; padding: 10px 12px; margin-bottom: 12px;">
                <div style="display: flex; align-items: center; gap: 9px;">
                    <div style="width: 32px; height: 32px; border-radius: 50%; background: linear-gradient(135deg, #3B82F6, #6366F1); display: flex; align-items: center; justify-content: center; font-size: 0.78rem; font-weight: 700; color: white;">
                        {initials}
                    </div>
                    <div style="overflow: hidden; text-overflow: ellipsis; white-space: nowrap; flex: 1;">
                        <div style="font-weight: 600; font-size: 0.85rem; color: #F8FAFC; overflow: hidden; text-overflow: ellipsis;">
                            {user.get('full_name', 'User')}
                        </div>
                        <div style="font-size: 0.72rem; color: #94A3B8; overflow: hidden; text-overflow: ellipsis;">
                            {user.get('email', '')}
                        </div>
                    </div>
                </div>
                {f'<div style="margin-top: 6px;"><span style="background: rgba(59, 130, 246, 0.15); color: #60A5FA; border: 1px solid rgba(59, 130, 246, 0.3); font-size: 0.68rem; font-weight: 600; padding: 1px 6px; border-radius: 4px; display: inline-block;">Demo Mode</span></div>' if is_demo else ''}
            </div>
            """,
            unsafe_allow_html=True,
        )

        if st.button("🚪 Sign Out", use_container_width=True, type="secondary"):
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

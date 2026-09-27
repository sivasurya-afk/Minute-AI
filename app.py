"""
Minute AI - Main Application Entrypoint.
Stitch Design System: Executive Precision (Warm Light Minimalist, Full Top-Navigation, No Left Sidebar).
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
    initial_sidebar_state="collapsed",
)

# Inject Stitch Executive Precision CSS
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');
    
    /* Global Typography */
    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
        color: #111827;
        background-color: #F8F9FB !important;
    }
    
    h1, h2, h3, h4, h5, h6 {
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        letter-spacing: -0.02em !important;
        color: #111827 !important;
    }

    /* Completely hide Streamlit sidebar and its toggle button */
    [data-testid="stSidebar"],
    [data-testid="collapsedControl"] {
        display: none !important;
    }

    /* Main container full-width architectural layout */
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 3.5rem !important;
        max-width: 1460px !important;
    }

    /* Custom subtle scrollbars */
    ::-webkit-scrollbar {
        width: 6px;
        height: 6px;
    }
    ::-webkit-scrollbar-track {
        background: #F1F3F5;
    }
    ::-webkit-scrollbar-thumb {
        background: #CBD5E1;
        border-radius: 4px;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: #94A3B8;
    }

    /* Top Sticky Navigation Bar */
    .top-navbar {
        background: #FFFFFF;
        border: 1px solid #E5E7EB;
        border-radius: 14px;
        padding: 10px 18px;
        margin-bottom: 1.5rem;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04), 0 1px 2px rgba(0, 0, 0, 0.02);
        display: flex;
        align-items: center;
        justify-content: space-between;
    }

    /* Level 1 Content Cards */
    .stitch-card {
        background: #FFFFFF;
        border: 1px solid #E5E7EB;
        border-radius: 12px;
        padding: 1.4rem;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04), 0 1px 2px rgba(0, 0, 0, 0.02);
        transition: border-color 0.15s ease, box-shadow 0.15s ease;
    }
    .stitch-card:hover {
        border-color: #D1D5DB;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.02);
    }

    /* Primary and Secondary Buttons */
    .stButton > button {
        border-radius: 8px !important;
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        font-weight: 600 !important;
        font-size: 0.85rem !important;
        padding: 0.45rem 1rem !important;
        transition: all 0.15s ease !important;
    }
    .stButton > button[kind="primary"] {
        background-color: #4F46E5 !important;
        color: #FFFFFF !important;
        border: 1px solid #4338CA !important;
        box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05) !important;
    }
    .stButton > button[kind="primary"]:hover {
        background-color: #4338CA !important;
        box-shadow: 0 3px 8px rgba(79, 70, 229, 0.25) !important;
    }
    .stButton > button[kind="secondary"] {
        background-color: #FFFFFF !important;
        color: #111827 !important;
        border: 1px solid #E5E7EB !important;
        box-shadow: 0 1px 2px rgba(0, 0, 0, 0.03) !important;
    }
    .stButton > button[kind="secondary"]:hover {
        background-color: #F9FAFB !important;
        border-color: #D1D5DB !important;
    }

    /* Metric Cards Override */
    [data-testid="stMetric"] {
        background: #FFFFFF !important;
        border: 1px solid #E5E7EB !important;
        border-radius: 12px !important;
        padding: 1.1rem 1.25rem !important;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.03) !important;
    }
    [data-testid="stMetricValue"] {
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        font-size: 2.1rem !important;
        font-weight: 700 !important;
        color: #111827 !important;
        letter-spacing: -0.03em !important;
    }
    [data-testid="stMetricLabel"] {
        font-size: 0.76rem !important;
        font-weight: 600 !important;
        color: #6B7280 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.05em !important;
    }

    /* Form Controls */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea,
    .stSelectbox > div > div {
        background-color: #FFFFFF !important;
        border: 1px solid #E5E7EB !important;
        border-radius: 8px !important;
        color: #111827 !important;
        box-shadow: 0 1px 2px rgba(0,0,0,0.02) !important;
    }
    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {
        border-color: #4F46E5 !important;
        box-shadow: 0 0 0 3px rgba(79, 70, 229, 0.15) !important;
    }

    /* Tabs Styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 6px !important;
        background: #F1F3F5 !important;
        padding: 4px !important;
        border-radius: 10px !important;
        border: 1px solid #E5E7EB !important;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 6px !important;
        padding: 6px 14px !important;
        color: #4B5563 !important;
        font-weight: 600 !important;
        font-size: 0.83rem !important;
        border: none !important;
        background: transparent !important;
    }
    .stTabs [aria-selected="true"] {
        background: #FFFFFF !important;
        color: #111827 !important;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08) !important;
    }

    /* Expanders */
    [data-testid="stExpander"] {
        background: #FFFFFF !important;
        border: 1px solid #E5E7EB !important;
        border-radius: 10px !important;
        box-shadow: 0 1px 2px rgba(0, 0, 0, 0.02) !important;
    }

    /* Monospace Code */
    code {
        font-family: 'JetBrains Mono', monospace !important;
        font-size: 0.8rem !important;
        background: #EEF2F6 !important;
        color: #334155 !important;
        padding: 2px 5px !important;
        border-radius: 4px !important;
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

    # 2. TOP HORIZONTAL NAVIGATION BAR (Zero Sidebar Layout)
    if "current_nav" not in st.session_state:
        st.session_state["current_nav"] = "Dashboard"

    if "nav_selection" in st.session_state:
        st.session_state["current_nav"] = st.session_state.pop("nav_selection")

    current_nav = st.session_state["current_nav"]

    # Top Bar Header Container
    col_nav_brand, col_nav_items, col_nav_user = st.columns([2.5, 5, 2.5])

    with col_nav_brand:
        st.markdown(
            """
            <div style="display: flex; align-items: center; gap: 9px; padding: 4px 0;">
                <div style="width: 34px; height: 34px; border-radius: 8px; background: #4F46E5; display: flex; align-items: center; justify-content: center; font-size: 1.15rem; box-shadow: 0 2px 6px rgba(79, 70, 229, 0.3);">
                    ⏱️
                </div>
                <div>
                    <div style="display: flex; align-items: center; gap: 6px;">
                        <span style="font-size: 1.15rem; font-weight: 800; color: #111827; letter-spacing: -0.02em;">Minute AI</span>
                        <span style="background: #EEF2FF; color: #4338CA; border: 1px solid #C7D2FE; font-size: 0.65rem; font-weight: 700; padding: 1px 5px; border-radius: 4px; text-transform: uppercase;">Enterprise</span>
                    </div>
                    <div style="font-size: 0.72rem; color: #6B7280; font-weight: 500;">Meeting Intelligence to Jira</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col_nav_items:
        # Segmented horizontal navigation buttons
        nav_cols = st.columns(6)
        pages_def = [
            ("Dashboard", "📊 Dashboard"),
            ("Process Transcript", "📝 Process"),
            ("Action Items", "✅ Tasks"),
            ("Transcript History", "📜 History"),
            ("Jira Projects", "📁 Projects"),
            ("Settings", "⚙️ Settings"),
        ]

        for idx, (page_key, page_label) in enumerate(pages_def):
            with nav_cols[idx]:
                is_active = (current_nav == page_key)
                btn_type = "primary" if is_active else "secondary"
                if st.button(page_label, key=f"topnav_{page_key}", use_container_width=True, type=btn_type):
                    st.session_state["current_nav"] = page_key
                    st.rerun()

    with col_nav_user:
        # User profile and sign out
        user_name = user.get('full_name', 'User')
        initials = "".join([part[0].upper() for part in user_name.split()[:2]]) or "U"
        is_demo = user.get("is_demo", False)

        c_uinfo, c_usignout = st.columns([2.8, 1.2])
        with c_uinfo:
            st.markdown(
                f"""
                <div style="display: flex; align-items: center; justify-content: flex-end; gap: 8px; padding-top: 4px;">
                    <div style="text-align: right; line-height: 1.2;">
                        <div style="font-weight: 700; font-size: 0.82rem; color: #111827;">{user_name}</div>
                        <div style="font-size: 0.7rem; color: {'#2563EB' if is_demo else '#059669'}; font-weight: 600;">
                            {'⚡ Demo Mode' if is_demo else '🟢 Live Active'}
                        </div>
                    </div>
                    <div style="width: 30px; height: 30px; border-radius: 50%; background: #4F46E5; color: #FFFFFF; display: flex; align-items: center; justify-content: center; font-size: 0.75rem; font-weight: 700; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
                        {initials}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with c_usignout:
            if st.button("Logout", key="btn_logout", use_container_width=True, type="secondary"):
                logout()

    st.markdown("<hr style='margin: 0.6rem 0 1.4rem 0; border: none; border-top: 1px solid #E5E7EB;'/>", unsafe_allow_html=True)

    # 3. PAGE ROUTING
    if current_nav == "Dashboard":
        render_dashboard_page(user_id, access_token)
    elif current_nav == "Process Transcript":
        render_process_transcript_page(user_id, access_token)
    elif current_nav == "Action Items":
        render_action_items_page(user_id, access_token)
    elif current_nav == "Transcript History":
        render_transcript_history_page(user_id, access_token)
    elif current_nav == "Jira Projects":
        render_jira_projects_page(user_id, access_token)
    elif current_nav == "Settings":
        render_settings_page(user_id, access_token)


if __name__ == "__main__":
    main()

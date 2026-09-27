"""
Authentication and session management for Minute AI using Supabase Auth.
Provides login, registration, logout, and guest/demo mode support.
"""

from typing import Optional, Dict, Any, Tuple
import os
import streamlit as st
from dotenv import load_dotenv

Tuple_Result = Tuple[bool, str]

load_dotenv()

# Demo user credentials for offline / unconfigured mode
DEMO_USER = {
    "id": "00000000-0000-0000-0000-000000000001",
    "email": "demo@minute.ai",
    "full_name": "Demo User",
    "is_demo": True,
}


def get_supabase_auth_client():
    """Retrieve Supabase client for authentication."""
    url = os.getenv("SUPABASE_URL") or st.secrets.get("SUPABASE_URL", "")
    anon_key = os.getenv("SUPABASE_ANON_KEY") or st.secrets.get("SUPABASE_ANON_KEY", "")

    if not url or not anon_key or "your-project" in url or "your_supabase" in anon_key:
        return None

    try:
        from supabase import create_client
        return create_client(url, anon_key)
    except Exception:
        return None


def is_authenticated() -> bool:
    """Check if a user is currently logged in."""
    return st.session_state.get("user") is not None


def get_current_user() -> Optional[Dict[str, Any]]:
    """Return currently authenticated user dictionary or None."""
    return st.session_state.get("user")


def get_current_user_id() -> str:
    """Return user UUID or empty string."""
    user = get_current_user()
    return user.get("id", "") if user else ""


def login_user(email: str, password: str) -> Tuple_Result:
    """Authenticate existing user via Supabase Auth."""
    client = get_supabase_auth_client()
    if not client:
        return False, "Supabase connection is not configured. Use Demo Mode or configure .env."

    try:
        res = client.auth.sign_in_with_password({"email": email, "password": password})
        if res.user:
            user_data = {
                "id": str(res.user.id),
                "email": res.user.email,
                "full_name": (res.user.user_metadata or {}).get("full_name", res.user.email.split("@")[0]),
                "access_token": res.session.access_token if res.session else None,
                "is_demo": False,
            }
            st.session_state["user"] = user_data
            return True, "Login successful!"
        return False, "Invalid email or password."
    except Exception as e:
        err_msg = str(e)
        if "invalid_credentials" in err_msg.lower():
            return False, "Invalid email or password."
        return False, f"Authentication error: {err_msg}"


def register_user(email: str, password: str, full_name: str) -> Tuple_Result:
    """Register new user account in Supabase."""
    client = get_supabase_auth_client()
    if not client:
        return False, "Supabase connection is not configured. Use Demo Mode or configure .env."

    if len(password) < 6:
        return False, "Password must be at least 6 characters."

    try:
        res = client.auth.sign_up({
            "email": email,
            "password": password,
            "options": {
                "data": {"full_name": full_name.strip()}
            }
        })
        if res.user:
            # If email confirmation is enabled on Supabase, notify user
            if res.session:
                user_data = {
                    "id": str(res.user.id),
                    "email": res.user.email,
                    "full_name": full_name.strip(),
                    "access_token": res.session.access_token,
                    "is_demo": False,
                }
                st.session_state["user"] = user_data
                return True, "Registration successful! You are now logged in."
            else:
                return True, "Registration initiated! Please check your email to confirm your account."
        return False, "Unable to create account. Please try again."
    except Exception as e:
        return False, f"Registration error: {str(e)}"


def login_demo_mode():
    """Sign in using the offline demo user session."""
    st.session_state["user"] = DEMO_USER
    st.session_state["is_demo"] = True


def logout():
    """Clear session state and sign out."""
    client = get_supabase_auth_client()
    if client and not st.session_state.get("user", {}).get("is_demo"):
        try:
            client.auth.sign_out()
        except Exception:
            pass
    st.session_state["user"] = None
    st.session_state["is_demo"] = False
    st.rerun()



def render_auth_page():
    """Render a clean authentication container with login, signup, and demo mode."""
    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        st.markdown(
            """
            <div style="text-align: center; margin-bottom: 2rem; margin-top: 1rem;">
                <div style="width: 56px; height: 56px; border-radius: 14px; background: linear-gradient(135deg, #6366F1, #8B5CF6); display: inline-flex; align-items: center; justify-content: center; font-size: 1.8rem; box-shadow: 0 0 25px rgba(99, 102, 241, 0.4); margin-bottom: 12px;">
                    ⏱️
                </div>
                <h1 style="margin: 0; font-size: 2.2rem; font-weight: 800; color: #F8FAFC; letter-spacing: -0.03em;">Minute AI</h1>
                <p style="color: #94A3B8; font-size: 0.95rem; margin-top: 6px;">
                    AI-Powered Meeting Transcript to Jira Action Item Dashboard
                </p>
                <div style="display: inline-flex; gap: 8px; margin-top: 4px;">
                    <span style="background: rgba(99, 102, 241, 0.12); color: #A5B4FC; font-size: 0.72rem; padding: 2px 8px; border-radius: 4px; font-weight: 600;">Groq Whisper V3</span>
                    <span style="background: rgba(16, 185, 129, 0.12); color: #34D399; font-size: 0.72rem; padding: 2px 8px; border-radius: 4px; font-weight: 600;">Qwen 2.5 AI</span>
                    <span style="background: rgba(56, 189, 248, 0.12); color: #7DD3FC; font-size: 0.72rem; padding: 2px 8px; border-radius: 4px; font-weight: 600;">Supabase RLS</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        has_supabase = get_supabase_auth_client() is not None

        if not has_supabase:
            st.markdown(
                """
                <div style="background: rgba(99, 102, 241, 0.08); border: 1px solid rgba(99, 102, 241, 0.25); border-radius: 10px; padding: 12px 14px; margin-bottom: 16px;">
                    <div style="font-weight: 700; color: #A5B4FC; font-size: 0.85rem; margin-bottom: 2px;">⚡ Instant Demo & Evaluation Ready</div>
                    <div style="font-size: 0.78rem; color: #94A3B8; line-height: 1.4;">
                        Supabase credentials can be connected anytime. You can explore all features right now with <b>Demo Mode</b>.
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        tab_demo, tab_login, tab_register = st.tabs(["🚀 Instant Demo Mode", "🔑 Sign In", "✨ Create Account"])

        with tab_demo:
            st.markdown(
                """
                <div style="padding: 10px 0;">
                    <p style="font-size: 0.88rem; color: #CBD5E1; line-height: 1.5;">
                        Test Minute AI immediately with pre-loaded mock data and live Groq AI extraction:
                    </p>
                    <ul style="font-size: 0.82rem; color: #94A3B8; line-height: 1.6;">
                        <li>Pre-loaded with 3 Jira projects (Frontend, Core API, DevOps)</li>
                        <li>Sample meetings with verified action items and priorities</li>
                        <li>Full access to Plotly charts, multi-format transcript upload, and exports</li>
                    </ul>
                </div>
                """,
                unsafe_allow_html=True,
            )
            if st.button("Launch Minute AI as Demo User →", use_container_width=True, type="primary"):
                login_demo_mode()
                st.rerun()

        with tab_login:
            with st.form("login_form", clear_on_submit=False):
                email = st.text_input("Email", placeholder="you@company.com", key="login_email")
                password = st.text_input("Password", type="password", placeholder="••••••••", key="login_password")
                submit = st.form_submit_button("Sign In to Account", use_container_width=True, type="primary")

                if submit:
                    if not email or not password:
                        st.error("Please enter both email and password.")
                    else:
                        success, message = login_user(email, password)
                        if success:
                            st.success(message)
                            st.rerun()
                        else:
                            st.error(message)

        with tab_register:
            with st.form("register_form", clear_on_submit=False):
                name = st.text_input("Full Name", placeholder="Jane Doe", key="reg_name")
                reg_email = st.text_input("Work Email", placeholder="you@company.com", key="reg_email")
                reg_password = st.text_input("Password", type="password", placeholder="At least 6 characters", key="reg_password")
                submit_reg = st.form_submit_button("Create Enterprise Account", use_container_width=True, type="primary")

                if submit_reg:
                    if not name or not reg_email or not reg_password:
                        st.error("Please fill in all registration fields.")
                    else:
                        success, message = register_user(reg_email, reg_password, name)
                        if success:
                            st.success(message)
                            if st.session_state.get("user"):
                                st.rerun()
                        else:
                            st.error(message)

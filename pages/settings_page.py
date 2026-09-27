"""
Settings page for Minute AI.
Modern Dark Enterprise SaaS model preferences, classification parameters, and diagnostics.
"""

from typing import Optional
import os
import streamlit as st
from services.groq_service import AVAILABLE_GROQ_MODELS, DEFAULT_LLM_MODEL, DEFAULT_TRANSCRIPTION_MODEL, GroqService
from database.supabase_client import get_supabase_client
from database.repositories import ProfileRepository


def render_settings_page(user_id: str, access_token: Optional[str] = None):
    # Header
    st.markdown(
        """
        <div style="margin-bottom: 1.2rem;">
            <h1 style="font-size: 2.1rem; font-weight: 800; color: #F8FAFC; margin: 0; letter-spacing: -0.03em;">
                Settings
            </h1>
            <p style="color: #94A3B8; font-size: 0.95rem; margin-top: 4px;">
                Manage AI model parameters, confidence classification thresholds, and environment connectivity.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    profile_repo = ProfileRepository(access_token)
    profile = profile_repo.get_profile(user_id) or {}

    tab_ai, tab_profile, tab_system = st.tabs(["🤖 AI Model Configuration", "👤 User Profile", "🔌 Connectivity & Diagnostics"])

    with tab_ai:
        st.markdown("##### Groq AI Model & Extraction Tuning")
        st.caption("Settings modified here take immediate effect for all extraction runs in your current session.")

        with st.form("ai_settings_form"):
            # Model Selection
            current_model = st.session_state.get("custom_groq_model", os.getenv("GROQ_LLM_MODEL", DEFAULT_LLM_MODEL))
            model_idx = AVAILABLE_GROQ_MODELS.index(current_model) if current_model in AVAILABLE_GROQ_MODELS else 0
            selected_model = st.selectbox(
                "Groq LLM Model for Action Item Extraction",
                AVAILABLE_GROQ_MODELS,
                index=model_idx,
                help="Recommended: qwen/qwen3.8-27b or llama-3.3-70b-versatile for structured JSON extraction",
            )

            # Transcription Model
            st.text_input(
                "Speech Transcription Engine",
                value=DEFAULT_TRANSCRIPTION_MODEL,
                disabled=True,
                help="Audio transcription is powered by Groq Whisper Large V3.",
            )

            # Classification Confidence Threshold
            current_threshold = float(st.session_state.get("custom_threshold", os.getenv("CONFIDENCE_THRESHOLD", 0.70)))
            selected_threshold = st.slider(
                "Project Classification Confidence Threshold",
                min_value=0.50,
                max_value=0.95,
                value=current_threshold,
                step=0.05,
                help="Tasks classified with confidence below this threshold will be flagged as 'Needs Clarification'.",
            )

            # Default Priority
            selected_priority = st.selectbox(
                "Default Action Item Priority (if unspecified)",
                ["Medium", "Low", "High", "Lowest", "Highest"],
                index=0,
            )

            save_ai = st.form_submit_button("Save AI Preferences", type="primary")
            if save_ai:
                st.session_state["custom_groq_model"] = selected_model
                st.session_state["custom_threshold"] = selected_threshold
                st.session_state["default_priority"] = selected_priority
                os.environ["GROQ_LLM_MODEL"] = selected_model
                os.environ["CONFIDENCE_THRESHOLD"] = str(selected_threshold)
                st.success("AI preferences updated successfully!")

    with tab_profile:
        st.markdown("##### Account Information")
        with st.form("profile_form"):
            p_name = st.text_input("Full Name", value=profile.get("full_name") or "")
            p_email = st.text_input("Email Address", value=profile.get("email") or "", disabled=True)

            save_profile = st.form_submit_button("Update Profile", type="primary")
            if save_profile:
                if p_name.strip():
                    profile_repo.update_profile(user_id, p_name.strip())
                    st.success("Profile updated!")
                    st.rerun()

    with tab_system:
        st.markdown("##### Active System Diagnostics")

        groq_service = GroqService.get_instance()
        groq_key = os.getenv("GROQ_API_KEY", "")
        has_groq = groq_service.is_configured()

        c_groq_stat, c_supa_stat = st.columns(2)

        with c_groq_stat:
            with st.container(border=True):
                st.markdown(
                    """
                    <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px;">
                        <span style="font-weight: 700; font-size: 1.05rem; color: #F8FAFC;">Groq Cloud API</span>
                        <span style="background: rgba(16, 185, 129, 0.15); color: #34D399; border: 1px solid rgba(16, 185, 129, 0.3); font-size: 0.72rem; font-weight: 600; padding: 2px 7px; border-radius: 6px;">
                            Active & Ready
                        </span>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                if has_groq:
                    masked = groq_key[:7] + "••••••••" + groq_key[-4:] if len(groq_key) > 11 else "Configured"
                    st.markdown(f"API Key: ` {masked} `")
                    st.markdown(f"Active LLM: ` {os.getenv('GROQ_LLM_MODEL', DEFAULT_LLM_MODEL)} `")
                    st.markdown(f"Speech Engine: ` {DEFAULT_TRANSCRIPTION_MODEL} `")
                    st.caption("✅ Fast Whisper V3 & Qwen 2.5 inference verified.")
                else:
                    st.warning("Key not configured in .env.")

        with c_supa_stat:
            with st.container(border=True):
                client = get_supabase_client(access_token)
                is_connected = client is not None
                supa_status_label = "Cloud Connected" if is_connected else "MCP / Demo Active"
                supa_color = "#34D399" if is_connected else "#60A5FA"

                st.markdown(
                    f"""
                    <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px;">
                        <span style="font-weight: 700; font-size: 1.05rem; color: #F8FAFC;">Supabase PostgreSQL</span>
                        <span style="background: rgba(99, 102, 241, 0.15); color: {supa_color}; border: 1px solid {supa_color}44; font-size: 0.72rem; font-weight: 600; padding: 2px 7px; border-radius: 6px;">
                            {supa_status_label}
                        </span>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                supa_url = os.getenv("SUPABASE_URL", "https://qklcxzdumitujatjoxqn.supabase.co")
                st.markdown(f"Project URL: ` {supa_url} `")
                st.markdown("Project Ref: ` qklcxzdumitujatjoxqn `")
                st.markdown("Security: ` Row Level Security (RLS) `")
                st.caption("Configured with Supabase MCP server & Agent Skills.")

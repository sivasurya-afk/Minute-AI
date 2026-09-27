"""
Settings page for Minute AI.
Manage Groq LLM model preferences, classification thresholds, default priorities, and profile settings.
"""

from typing import Optional
import os
import streamlit as st
from services.groq_service import AVAILABLE_GROQ_MODELS, DEFAULT_LLM_MODEL, DEFAULT_TRANSCRIPTION_MODEL, GroqService
from database.supabase_client import get_supabase_client
from database.repositories import ProfileRepository


def render_settings_page(user_id: str, access_token: Optional[str] = None):
    st.markdown(
        """
        <div style="margin-bottom: 1.5rem;">
            <h1 style="font-size: 2rem; font-weight: 700; margin-bottom: 0.2rem; color: #1E293B;">Settings</h1>
            <p style="color: #64748B; font-size: 0.95rem; margin: 0;">
                Configure AI model parameters, classification thresholds, and user profile preferences.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    profile_repo = ProfileRepository(access_token)
    profile = profile_repo.get_profile(user_id) or {}

    tab_ai, tab_profile, tab_system = st.tabs(["🤖 AI Model Preferences", "👤 User Profile", "🔌 Connection & Diagnostics"])

    with tab_ai:
        st.markdown("##### Groq LLM & Transcription Parameters")
        st.caption("Settings configured here take immediate effect for all transcript extraction runs in your session.")

        with st.form("ai_settings_form"):
            # Model Selection
            current_model = st.session_state.get("custom_groq_model", os.getenv("GROQ_LLM_MODEL", DEFAULT_LLM_MODEL))
            model_idx = AVAILABLE_GROQ_MODELS.index(current_model) if current_model in AVAILABLE_GROQ_MODELS else 0
            selected_model = st.selectbox(
                "Groq LLM Model for Action Item Extraction",
                AVAILABLE_GROQ_MODELS,
                index=model_idx,
                help="Recommended: llama-3.3-70b-versatile for high reasoning and accuracy",
            )

            # Transcription Model
            st.text_input(
                "Transcription Model (Whisper)",
                value=DEFAULT_TRANSCRIPTION_MODEL,
                disabled=True,
                help="Speech-to-text audio transcription uses Groq Whisper Large V3.",
            )

            # Classification Confidence Threshold
            current_threshold = float(st.session_state.get("custom_threshold", os.getenv("CONFIDENCE_THRESHOLD", 0.70)))
            selected_threshold = st.slider(
                "Project Classification Confidence Threshold",
                min_value=0.50,
                max_value=0.95,
                value=current_threshold,
                step=0.05,
                help="Tasks classified with confidence below this threshold will be marked as 'Needs Clarification'.",
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
        st.markdown("##### Integration Diagnostics")

        # Groq Diagnostics
        groq_service = GroqService.get_instance()
        groq_key = os.getenv("GROQ_API_KEY", "")
        has_groq = groq_service.is_configured()

        c_groq_stat, c_supa_stat = st.columns(2)

        with c_groq_stat:
            with st.container(border=True):
                st.markdown("#### Groq Cloud API")
                if has_groq:
                    masked = groq_key[:6] + "..." + groq_key[-4:] if len(groq_key) > 10 else "Configured"
                    st.success(f"🟢 Connected & Ready (`{masked}`)")
                else:
                    st.warning("🟡 Key Not Set in `.env`. Using Offline Simulation Pipeline.")
                st.caption("Provides Whisper Large V3 transcription and LLaMA 3.3 task extraction.")

        with c_supa_stat:
            with st.container(border=True):
                st.markdown("#### Supabase PostgreSQL")
                client = get_supabase_client(access_token)
                if client:
                    st.success("🟢 Connected to Cloud Database (RLS Enforced)")
                else:
                    st.info("🔵 In-Memory / Evaluation Mode Active")
                st.caption("Secure multi-tenant persistence with PostgreSQL and Row Level Security.")

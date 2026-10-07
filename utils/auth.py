"""
Authentication and session management for Minute AI using Supabase Auth.
Provides login, registration, and guest/demo mode support.
"""

from typing import Optional, Dict, Any, Tuple
import os
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
    url = os.getenv("SUPABASE_URL", "")
    anon_key = os.getenv("SUPABASE_ANON_KEY", "")

    if not url or not anon_key or "your-project" in url or "your_supabase" in anon_key:
        return None

    try:
        from supabase import create_client
        return create_client(url, anon_key)
    except Exception:
        return None


def login_user(email: str, password: str) -> Tuple_Result:
    """Authenticate existing user via Supabase Auth."""
    client = get_supabase_auth_client()
    if not client:
        return False, "Supabase connection is not configured. Use Demo Mode or configure .env."

    try:
        res = client.auth.sign_in_with_password({"email": email, "password": password})
        if res.user:
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
            if res.session:
                return True, "Registration successful! You are now logged in."
            else:
                return True, "Registration initiated! Please check your email to confirm your account."
        return False, "Unable to create account. Please try again."
    except Exception as e:
        return False, f"Registration error: {str(e)}"

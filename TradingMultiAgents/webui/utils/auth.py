"""
Simple authentication system for WebUI
"""

import os
import hashlib
import hmac
import secrets
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import streamlit as st

class AuthManager:
    """Simple authentication manager for WebUI"""
    
    def __init__(self):
        # In production, these should come from secure storage
        self.users = self._load_users()
        self.session_timeout = timedelta(hours=8)
        
    def _load_users(self) -> Dict[str, Dict[str, Any]]:
        """Load users from environment or use defaults"""
        # In production, load from database or secure config
        default_users = {
            "admin": {
                "password_hash": self._hash_password("admin123"),  # Change in production!
                "role": "admin"
            },
            "user": {
                "password_hash": self._hash_password("user123"),  # Change in production!
                "role": "user"
            }
        }
        
        # Allow overriding via environment
        if os.getenv("WEBUI_ADMIN_PASSWORD"):
            default_users["admin"]["password_hash"] = self._hash_password(
                os.getenv("WEBUI_ADMIN_PASSWORD")
            )
            
        return default_users
    
    def _hash_password(self, password: str) -> str:
        """Hash password using SHA256"""
        # In production, use bcrypt or similar
        salt = os.getenv("WEBUI_PASSWORD_SALT", "default_salt_change_me")
        return hashlib.sha256(f"{password}{salt}".encode()).hexdigest()
    
    def authenticate(self, username: str, password: str) -> bool:
        """Authenticate user"""
        if username not in self.users:
            return False
            
        expected_hash = self.users[username]["password_hash"]
        provided_hash = self._hash_password(password)
        
        # Use constant-time comparison to prevent timing attacks
        return hmac.compare_digest(expected_hash, provided_hash)
    
    def create_session(self, username: str) -> str:
        """Create session for authenticated user"""
        session_id = secrets.token_urlsafe(32)
        
        # Store session info
        if "sessions" not in st.session_state:
            st.session_state.sessions = {}
            
        st.session_state.sessions[session_id] = {
            "username": username,
            "created_at": datetime.now(),
            "last_activity": datetime.now(),
            "role": self.users[username]["role"]
        }
        
        return session_id
    
    def validate_session(self, session_id: Optional[str]) -> Optional[Dict[str, Any]]:
        """Validate session and return session info if valid"""
        if not session_id:
            return None
            
        if "sessions" not in st.session_state:
            return None
            
        session = st.session_state.sessions.get(session_id)
        if not session:
            return None
            
        # Check timeout
        if datetime.now() - session["last_activity"] > self.session_timeout:
            # Session expired
            del st.session_state.sessions[session_id]
            return None
            
        # Update last activity
        session["last_activity"] = datetime.now()
        return session
    
    def logout(self, session_id: str):
        """Logout user by removing session"""
        if "sessions" in st.session_state and session_id in st.session_state.sessions:
            del st.session_state.sessions[session_id]
    
    def get_user_role(self, username: str) -> Optional[str]:
        """Get user role"""
        user = self.users.get(username)
        return user["role"] if user else None
    
    def is_admin(self, session_info: Dict[str, Any]) -> bool:
        """Check if user is admin"""
        return session_info.get("role") == "admin"


def require_auth(func):
    """Decorator to require authentication for a function"""
    def wrapper(*args, **kwargs):
        if "auth_session_id" not in st.session_state:
            st.error("Please login to access this feature")
            st.stop()
            
        auth_manager = AuthManager()
        session_info = auth_manager.validate_session(st.session_state.auth_session_id)
        
        if not session_info:
            st.error("Session expired. Please login again.")
            del st.session_state.auth_session_id
            st.stop()
            
        # Add session info to kwargs
        kwargs["session_info"] = session_info
        return func(*args, **kwargs)
        
    return wrapper


def require_admin(func):
    """Decorator to require admin role"""
    def wrapper(*args, **kwargs):
        if "auth_session_id" not in st.session_state:
            st.error("Please login to access this feature")
            st.stop()
            
        auth_manager = AuthManager()
        session_info = auth_manager.validate_session(st.session_state.auth_session_id)
        
        if not session_info:
            st.error("Session expired. Please login again.")
            del st.session_state.auth_session_id
            st.stop()
            
        if not auth_manager.is_admin(session_info):
            st.error("Admin access required")
            st.stop()
            
        # Add session info to kwargs
        kwargs["session_info"] = session_info
        return func(*args, **kwargs)
        
    return wrapper
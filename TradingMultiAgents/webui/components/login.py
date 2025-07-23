"""
Login component for WebUI
"""

import streamlit as st
from typing import Optional
from ..utils.auth import AuthManager


def show_login_page() -> Optional[str]:
    """Show login page and return session ID if successful"""
    st.title("🔐 Trading Agents WebUI - Login")
    
    with st.container():
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            with st.form("login_form"):
                st.markdown("### Please login to continue")
                
                username = st.text_input("Username", key="login_username")
                password = st.text_input("Password", type="password", key="login_password")
                
                col_btn1, col_btn2 = st.columns(2)
                with col_btn1:
                    submit = st.form_submit_button("Login", use_container_width=True, type="primary")
                
                if submit:
                    if not username or not password:
                        st.error("Please enter both username and password")
                        return None
                        
                    auth_manager = AuthManager()
                    
                    if auth_manager.authenticate(username, password):
                        session_id = auth_manager.create_session(username)
                        st.success("Login successful!")
                        return session_id
                    else:
                        st.error("Invalid username or password")
                        return None
            
            # Information box
            with st.expander("ℹ️ Login Information"):
                st.info("""
                **Demo Credentials:**
                - Username: `user`, Password: `user123`
                - Username: `admin`, Password: `admin123`
                
                **Note:** In production, please change default passwords and use secure authentication.
                """)
    
    return None


def show_logout_button():
    """Show logout button in sidebar"""
    if st.sidebar.button("🚪 Logout", key="logout_button"):
        auth_manager = AuthManager()
        if "auth_session_id" in st.session_state:
            auth_manager.logout(st.session_state.auth_session_id)
            del st.session_state.auth_session_id
        st.rerun()
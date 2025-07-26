"""
フル幅を使用するログインページの例
"""

import streamlit as st
from typing import Optional
from ..utils.auth import AuthManager


def show_login_page_fullwidth() -> Optional[str]:
    """赤枠部分も含めて画面全体を使用するログインページ"""
    
    # ページ全体の幅を使用
    st.set_page_config(layout="wide")
    
    # カスタムCSS - 赤枠部分も使用
    st.markdown("""
    <style>
    /* メインコンテナの幅制限を解除 */
    .main .block-container {
        max-width: none !important;
        padding-left: 2rem !important;
        padding-right: 2rem !important;
    }
    
    /* サイドバーを一時的に非表示（ログイン時のみ） */
    [data-testid="stSidebar"] {
        display: none;
    }
    
    /* コンテンツを画面全体に広げる */
    .element-container {
        width: 100% !important;
    }
    
    /* ログインフォームの背景 */
    .login-container {
        background: #f0f2f6;
        min-height: 100vh;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # オプション1: 単一列で全幅使用
    st.title("🔐 Trading Agents WebUI - Login")
    st.markdown("---")
    
    # フォームを中央に配置しつつ、背景は全幅
    with st.container():
        # 3列レイアウトだが、より広く使用
        col1, col2, col3 = st.columns([1, 4, 1])  # 中央を80%に
        
        with col2:
            with st.form("login_form"):
                st.markdown("### Please login to continue")
                
                # 2列でフォームフィールドを配置
                col_user, col_pass = st.columns(2)
                
                with col_user:
                    username = st.text_input("Username", key="login_username")
                
                with col_pass:
                    password = st.text_input("Password", type="password", key="login_password")
                
                # ボタンも2列で配置
                col_btn1, col_btn2 = st.columns(2)
                with col_btn1:
                    submit = st.form_submit_button("Login", use_container_width=True, type="primary")
                with col_btn2:
                    cancel = st.form_submit_button("Cancel", use_container_width=True)
                
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
    
    # 画面下部に情報を全幅で表示
    st.markdown("---")
    
    # 3列で情報を配置
    info_col1, info_col2, info_col3 = st.columns(3)
    
    with info_col1:
        st.markdown("### 🚀 Features")
        st.markdown("""
        - Multi-agent trading system
        - Real-time market analysis
        - Advanced backtesting
        """)
    
    with info_col2:
        st.markdown("### 📊 Demo Accounts")
        st.info("""
        **User**: user / user123  
        **Admin**: admin / admin123
        """)
    
    with info_col3:
        st.markdown("### 📞 Support")
        st.markdown("""
        - Documentation: [Link](#)
        - Contact: support@example.com
        """)
    
    return None


def show_login_page_sidebar_option() -> Optional[str]:
    """サイドバーを活用したログインページ"""
    
    # サイドバーにログインフォームを配置
    with st.sidebar:
        st.markdown("## 🔐 Login")
        
        with st.form("sidebar_login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submit = st.form_submit_button("Login", use_container_width=True)
            
            if submit:
                # ログイン処理...
                pass
    
    # メインエリアは情報表示に使用
    st.title("Welcome to Trading Agents WebUI")
    st.markdown("""
    ## A Multi-Agent Financial Analysis Platform
    
    Please login using the sidebar to access the system.
    """)
    
    # 画面全体を使って特徴を表示
    st.markdown("---")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Active Users", "1,234", "+12%")
    
    with col2:
        st.metric("Total Trades", "45,678", "+23%")
    
    with col3:
        st.metric("Success Rate", "67.8%", "+2.3%")
    
    with col4:
        st.metric("Uptime", "99.9%", "0%")
    
    return None
"""
改善されたログインコンポーネント - 表示面積を最大化
"""

import streamlit as st
from typing import Optional
from ..utils.auth import AuthManager


def show_login_page() -> Optional[str]:
    """Show login page with improved layout"""
    # ページ全体を使用するレイアウト
    st.markdown("""
    <style>
    /* ログインページ専用のスタイル */
    .main > div {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 100%;
    }
    
    /* フォームのスタイリング */
    .stForm {
        background-color: white;
        padding: 2rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    /* タイトルの中央寄せ */
    h1 {
        text-align: center;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # タイトル
    st.title("🔐 Trading Agents WebUI")
    st.markdown("<h3 style='text-align: center;'>ログインして続行</h3>", unsafe_allow_html=True)
    
    # スペーサー
    st.markdown("<br>", unsafe_allow_html=True)
    
    # より広いレイアウトオプション1: 画面幅の60%を使用
    col1, col2, col3 = st.columns([1, 3, 1])
    
    with col2:
        with st.form("login_form", clear_on_submit=False):
            # フォームヘッダー
            st.markdown("### アカウント情報を入力")
            
            # 入力フィールド
            username = st.text_input(
                "ユーザー名",
                placeholder="ユーザー名を入力",
                key="login_username"
            )
            
            password = st.text_input(
                "パスワード", 
                type="password",
                placeholder="パスワードを入力",
                key="login_password"
            )
            
            # Remember me オプション（オプション）
            col_check, col_space = st.columns([1, 2])
            with col_check:
                remember = st.checkbox("ログイン状態を保持", value=True)
            
            # ログインボタン
            st.markdown("<br>", unsafe_allow_html=True)
            submit = st.form_submit_button(
                "ログイン", 
                use_container_width=True, 
                type="primary"
            )
            
            if submit:
                if not username or not password:
                    st.error("ユーザー名とパスワードを入力してください")
                    return None
                    
                auth_manager = AuthManager()
                
                if auth_manager.authenticate(username, password):
                    session_id = auth_manager.create_session(username)
                    st.success("ログイン成功！")
                    st.balloons()  # 成功時のアニメーション
                    return session_id
                else:
                    st.error("ユーザー名またはパスワードが正しくありません")
                    return None
        
        # ログイン情報（より見やすく）
        st.markdown("<br>", unsafe_allow_html=True)
        
        # タブでログイン情報を整理
        tab1, tab2 = st.tabs(["デモアカウント", "ヘルプ"])
        
        with tab1:
            col_demo1, col_demo2 = st.columns(2)
            with col_demo1:
                st.info("""
                **一般ユーザー**
                - ユーザー名: `user`
                - パスワード: `user123`
                """)
            with col_demo2:
                st.info("""
                **管理者**
                - ユーザー名: `admin`
                - パスワード: `admin123`
                """)
        
        with tab2:
            st.markdown("""
            **ログインできない場合:**
            1. ユーザー名とパスワードを確認してください
            2. 大文字・小文字を区別します
            3. 管理者に問い合わせてください
            
            **セキュリティ:**
            - 本番環境ではデフォルトパスワードを変更してください
            - HTTPSを使用することを推奨します
            """)
    
    # フッター情報
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown(
        "<p style='text-align: center; color: #666;'>© 2025 TradingAgents - Multi-Agent Financial Analysis Platform</p>",
        unsafe_allow_html=True
    )
    
    return None


def show_login_page_fullwidth() -> Optional[str]:
    """フルワイド版のログインページ（オプション）"""
    # 画面全体を使用
    with st.container():
        # 背景とスタイリング
        st.markdown("""
        <style>
        .login-container {
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 80vh;
        }
        
        .login-box {
            background: white;
            padding: 3rem;
            border-radius: 15px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            width: 100%;
            max-width: 500px;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # センタリングされたログインボックス
        st.markdown('<div class="login-container">', unsafe_allow_html=True)
        
        # ここにログインフォームを配置
        # ... (上記と同様の実装)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    return None
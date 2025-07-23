"""
TradingAgents WebUI - Streamlitメインアプリケーション
"""

import streamlit as st
import sys
import os
from pathlib import Path
import asyncio
import logging
from dotenv import load_dotenv
import time
import uuid

# .envファイルを読み込み
load_dotenv()

# ログ設定を最初に
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# プロジェクトルートを追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(Path(__file__).parent))

from webui.utils.state import SessionState, UIHelpers
from webui.utils.mobile_responsive import mobile_page_config, apply_mobile_optimizations
from webui.utils.auth import AuthManager
from webui.components.login import show_login_page, show_logout_button
from webui.components.dashboard import Dashboard
from webui.components.settings import SettingsPage
from webui.components.execution import ExecutionPage
from webui.components.results import ResultsPage
from webui.components.logs import LogsPage
# Lazy import for backtest to avoid architecture issues
BacktestPage = None
Backtest2Page = None

try:
    from webui.components.backtest import BacktestPage
except ImportError as e:
    logger.error(f"バックテスト機能のインポートに失敗しました: {e}")
    import traceback
    logger.error(traceback.format_exc())

try:
    from webui.components.backtest2 import Backtest2Page
except ImportError as e:
    logger.error(f"バックテスト2機能のインポートに失敗しました: {e}")
    import traceback
    logger.error(traceback.format_exc())
from webui.backend.cli_wrapper import CLIWrapper

class WebUIApp:
    """WebUIメインアプリケーション"""
    
    def __init__(self):
        self.cli_wrapper = CLIWrapper()
        self.setup_page_config()
        SessionState.init_session_state()
        SessionState.load_user_preferences()
        
        # 進捗コールバック設定
        self.cli_wrapper.add_progress_callback(SessionState.add_progress)
    
    def setup_page_config(self):
        """Streamlitページ設定"""
        mobile_page_config(
            page_title="TradingAgents WebUI",
            page_icon="📈",
            layout="wide",
            initial_sidebar_state="auto"
        )
        
        # カスタムCSS
        # Apply custom styles without unsafe HTML
        st.markdown("""
        <style>
        /* Custom CSS for TradingAgents WebUI */
        .stApp { background-color: #f8f9fa; }
        .stButton > button { width: 100%; }
        .stProgress > div > div { background-color: #007bff; }
        </style>
        """, unsafe_allow_html=True)
    
    def render_header(self):
        """ヘッダー表示"""
        col1, col2, col3 = st.columns([1, 3, 1])
        with col2:
            st.title("📈 TradingAgents WebUI")
            st.caption("マルチエージェント金融分析プラットフォーム")
    
    def render_sidebar(self):
        """サイドバー表示"""
        with st.sidebar:
            st.markdown("### 📈 TradingAgents")
            
            # User info and logout
            if "current_user" in st.session_state:
                st.markdown(f"👤 **User:** {st.session_state.current_user}")
                st.markdown(f"🔑 **Role:** {st.session_state.user_role}")
                show_logout_button()
            
            st.markdown("---")
            
            # ナビゲーション
            st.markdown("### 🧭 ナビゲーション")
            
            current_page = SessionState.get("current_page")
            
            if st.button("🏠 ダッシュボード", use_container_width=True, 
                        type="primary" if current_page == "dashboard" else "secondary", key="nav_dashboard"):
                SessionState.navigate_to("dashboard")
                st.rerun()
            
            if st.button("⚙️ 分析設定", use_container_width=True,
                        type="primary" if current_page == "settings" else "secondary", key="nav_settings"):
                SessionState.navigate_to("settings")
                st.rerun()
            
            if st.button("▶️ 分析実行", use_container_width=True,
                        type="primary" if current_page == "execution" else "secondary", key="nav_execution"):
                SessionState.navigate_to("execution")
                st.rerun()
            
            if st.button("📊 結果表示", use_container_width=True,
                        type="primary" if current_page == "results" else "secondary", key="nav_results"):
                SessionState.navigate_to("results")
                st.rerun()
            
            if st.button("🔍 実行ログ", use_container_width=True,
                        type="primary" if current_page == "logs" else "secondary", key="nav_logs"):
                SessionState.navigate_to("logs")
                st.rerun()
            
            if st.button("📊 バックテスト", use_container_width=True,
                        type="primary" if current_page == "backtest" else "secondary", key="nav_backtest"):
                SessionState.navigate_to("backtest")
                st.rerun()
            
            if st.button("🧪 バックテスト2", use_container_width=True,
                        type="primary" if current_page == "backtest2" else "secondary", key="nav_backtest2"):
                SessionState.navigate_to("backtest2")
                st.rerun()
            
            st.markdown("---")
            
            # 現在の設定表示
            st.markdown("### 📋 現在の設定")
            with st.container():
                st.info(f"""
                **ティッカー:** {SessionState.get('selected_ticker')}  
                **日付:** {SessionState.get('selected_date')}  
                **深度:** {UIHelpers.format_research_depth(SessionState.get('research_depth'))}  
                **LLM:** {SessionState.get('llm_provider')}
                """)
            
            # 分析状況
            if SessionState.get("analysis_running"):
                st.markdown("### 🔄 分析実行中")
                progress_list = SessionState.get("analysis_progress", [])
                if progress_list:
                    latest = progress_list[-1]
                    st.write(f"**{latest.get('agent', '')}**: {latest.get('message', '')}")
                    st.progress(latest.get('progress', 0.0))
            
            st.markdown("---")
            
            # クイックアクション
            st.markdown("### ⚡ クイックアクション")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🔍 SPY分析", use_container_width=True, key="quick_spy"):
                    SessionState.update({
                        "selected_ticker": "SPY",
                        "current_page": "settings"
                    })
                    st.rerun()
            
            with col2:
                if st.button("📈 JP225分析", use_container_width=True, key="quick_jp225"):
                    SessionState.update({
                        "selected_ticker": "JP225",
                        "current_page": "settings"
                    })
                    st.rerun()
            
            # 環境変数チェック（管理者のみ）
            if st.session_state.get("user_role") == "admin":
                st.markdown("---")
                st.markdown("### 🔐 環境設定")
                
                required_vars = ["FINNHUB_API_KEY", "OPENAI_API_KEY"]
                all_set = True
                
                for var in required_vars:
                    if os.getenv(var):
                        st.success(f"✅ {var} is configured")
                    else:
                        st.error(f"❌ {var} is missing")
                        all_set = False
                
                if not all_set:
                    st.warning("⚠️ 必要な環境変数が設定されていません")
                    with st.expander("設定方法"):
                        st.code("""
export FINNHUB_API_KEY=your_key_here
export OPENAI_API_KEY=your_key_here
""")
    
    def render_main_content(self):
        """メインコンテンツ表示"""
        current_page = SessionState.get("current_page")
        
        if current_page == "dashboard":
            dashboard = Dashboard(self.cli_wrapper)
            dashboard.render()
        
        elif current_page == "settings":
            settings = SettingsPage(self.cli_wrapper)
            settings.render()
        
        elif current_page == "execution":
            execution = ExecutionPage(self.cli_wrapper)
            execution.render()
        
        elif current_page == "results":
            results = ResultsPage(self.cli_wrapper)
            results.render()
        
        elif current_page == "logs":
            logs = LogsPage()
            logs.render()
        
        elif current_page == "backtest":
            if BacktestPage is not None:
                backtest = BacktestPage(SessionState)
                backtest.render()
            else:
                st.error("バックテスト機能は現在利用できません。代わりにバックテスト2をご利用ください。")
                if st.button("バックテスト2に移動"):
                    SessionState.navigate_to("backtest2")
                    st.rerun()
        
        elif current_page == "backtest2":
            if Backtest2Page:
                try:
                    backtest2 = Backtest2Page(SessionState)
                    backtest2.render()
                except Exception as e:
                    logger.error(f"バックテスト2ページのレンダリングエラー: {e}")
                    import traceback
                    logger.error(traceback.format_exc())
                    st.error(f"バックテスト2機能でエラーが発生しました: {str(e)}")
                    st.error("詳細はログをご確認ください。")
            else:
                st.error("バックテスト2機能は現在利用できません。")
                st.info("インポートエラーの詳細はログをご確認ください。")
        
        else:
            st.error(f"Unknown page: {current_page}")
    
    def check_pending_notifications(self):
        """保留中の通知をチェック"""
        if "notification_handler" not in st.session_state:
            from webui.components.notification_handler import NotificationHandler
            st.session_state.notification_handler = NotificationHandler()
        
        # ユーザーIDの初期化
        if "user_id" not in st.session_state:
            st.session_state.user_id = str(uuid.uuid4())
        
        # 定期的に通知をチェック（5秒ごと）
        if time.time() - st.session_state.get("last_notification_check", 0) > 5:
            st.session_state.notification_handler.check_and_send_notifications(
                st.session_state.user_id
            )
            st.session_state.last_notification_check = time.time()
    
    def run(self):
        """アプリケーション実行"""
        try:
            # Check authentication
            if "auth_session_id" not in st.session_state:
                # Show login page
                session_id = show_login_page()
                if session_id:
                    st.session_state.auth_session_id = session_id
                    st.rerun()
                return
            
            # Validate session
            auth_manager = AuthManager()
            session_info = auth_manager.validate_session(st.session_state.auth_session_id)
            
            if not session_info:
                # Session expired
                del st.session_state.auth_session_id
                st.rerun()
                return
            
            # Store current user info
            st.session_state.current_user = session_info["username"]
            st.session_state.user_role = session_info["role"]
            
            # 通知チェック
            self.check_pending_notifications()
            
            self.render_header()
            self.render_sidebar()
            self.render_main_content()
            
        except Exception as e:
            logger.error(f"Application error: {e}")
            st.error(f"アプリケーションエラー: {e}")
            
            with st.expander("エラー詳細"):
                st.exception(e)

def main():
    """メイン関数"""
    try:
        app = WebUIApp()
        app.run()
    except Exception as e:
        st.error(f"アプリケーション初期化エラー: {e}")
        logger.error(f"App initialization error: {e}")

if __name__ == "__main__":
    main()
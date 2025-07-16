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

# .envファイルを読み込み
load_dotenv()

# プロジェクトルートを追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(Path(__file__).parent))

from webui.utils.state import SessionState, UIHelpers
from webui.utils.mobile_responsive import mobile_page_config, apply_mobile_optimizations
from webui.components.dashboard import Dashboard
from webui.components.settings import SettingsPage
from webui.components.execution import ExecutionPage
from webui.components.results import ResultsPage
from webui.backend.cli_wrapper import CLIWrapper

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
        st.markdown("""
        <style>
        .main-header {
            background: linear-gradient(90deg, #1e3c72 0%, #2a5298 100%);
            color: white;
            padding: 1rem;
            border-radius: 0.5rem;
            margin-bottom: 1rem;
            text-align: center;
        }
        .metric-card {
            background: #f8f9fa;
            padding: 1rem;
            border-radius: 0.5rem;
            border: 1px solid #dee2e6;
        }
        .status-running {
            color: #007bff;
        }
        .status-completed {
            color: #28a745;
        }
        .status-error {
            color: #dc3545;
        }
        .sidebar-section {
            margin-bottom: 1rem;
            padding: 0.5rem;
            border-left: 3px solid #007bff;
            background: #f8f9fa;
        }
        </style>
        """, unsafe_allow_html=True)
    
    def render_header(self):
        """ヘッダー表示"""
        st.markdown("""
        <div class="main-header">
            <h1>📈 TradingAgents WebUI</h1>
            <p>マルチエージェント金融分析プラットフォーム</p>
        </div>
        """, unsafe_allow_html=True)
    
    def render_sidebar(self):
        """サイドバー表示"""
        with st.sidebar:
            st.markdown("### 📈 TradingAgents")
            
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
            
            st.markdown("---")
            
            # 現在の設定表示
            st.markdown("### 📋 現在の設定")
            with st.container():
                st.markdown(f"""
                <div class="sidebar-section">
                <strong>ティッカー:</strong> {SessionState.get('selected_ticker')}<br>
                <strong>日付:</strong> {SessionState.get('selected_date')}<br>
                <strong>深度:</strong> {UIHelpers.format_research_depth(SessionState.get('research_depth'))}<br>
                <strong>LLM:</strong> {SessionState.get('llm_provider')}
                </div>
                """, unsafe_allow_html=True)
            
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
            
            # 環境変数チェック
            st.markdown("---")
            st.markdown("### 🔐 環境設定")
            
            required_vars = ["FINNHUB_API_KEY", "OPENAI_API_KEY"]
            all_set = True
            
            for var in required_vars:
                if os.getenv(var):
                    st.success(f"✅ {var}")
                else:
                    st.error(f"❌ {var}")
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
        
        else:
            st.error(f"Unknown page: {current_page}")
    
    def run(self):
        """アプリケーション実行"""
        try:
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
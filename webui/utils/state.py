"""
Streamlit状態管理ユーティリティ
"""

import streamlit as st
from typing import Any, Dict, List, Optional
from datetime import datetime, date
import json
from pathlib import Path

from webui.backend.cli_wrapper import AnalysisConfig, AnalysisProgress
from cli.models import AnalystType

class SessionState:
    """Streamlitセッション状態管理"""
    
    @staticmethod
    def init_session_state():
        """セッション状態の初期化"""
        defaults = {
            # ナビゲーション
            "current_page": "dashboard",
            "prev_page": None,
            
            # 分析設定
            "analysis_config": None,
            "selected_analysts": [AnalystType.MARKET, AnalystType.NEWS],
            "research_depth": 3,
            "llm_provider": "openai",
            "shallow_thinker": "gpt-4o-mini",
            "deep_thinker": "o3-2025-04-16",
            
            # 分析実行状態
            "analysis_running": False,
            "analysis_progress": [],
            "analysis_results": None,
            
            # 履歴・表示
            "selected_ticker": "SPY",
            "selected_date": str(date.today()),
            "analysis_history": [],
            "current_results": None,
            
            # UI状態
            "show_advanced_settings": False,
            "auto_refresh": True,
            "progress_container": None,
            
            # ユーザー設定
            "user_preferences": {
                "default_analysts": [AnalystType.MARKET.value, AnalystType.NEWS.value],
                "default_depth": 3,
                "default_provider": "openai",
                "theme": "light"
            }
        }
        
        for key, value in defaults.items():
            if key not in st.session_state:
                st.session_state[key] = value
    
    @staticmethod
    def get(key: str, default: Any = None) -> Any:
        """セッション状態の値を取得"""
        return st.session_state.get(key, default)
    
    @staticmethod
    def set(key: str, value: Any):
        """セッション状態の値を設定"""
        st.session_state[key] = value
    
    @staticmethod
    def update(updates: Dict[str, Any]):
        """複数の値を一括更新"""
        for key, value in updates.items():
            st.session_state[key] = value
    
    @staticmethod
    def navigate_to(page: str):
        """ページ遷移"""
        SessionState.set("prev_page", SessionState.get("current_page"))
        SessionState.set("current_page", page)
    
    @staticmethod
    def add_progress(progress: AnalysisProgress):
        """分析進捗を追加"""
        progress_list = SessionState.get("analysis_progress", [])
        progress_list.append({
            "stage": progress.stage,
            "agent": progress.agent,
            "status": progress.status,
            "progress": progress.progress,
            "message": progress.message,
            "timestamp": progress.timestamp.isoformat()
        })
        SessionState.set("analysis_progress", progress_list)
    
    @staticmethod
    def clear_progress():
        """分析進捗をクリア"""
        SessionState.set("analysis_progress", [])
    
    @staticmethod
    def save_user_preferences():
        """ユーザー設定を保存"""
        prefs_file = Path.home() / ".tradingagents_webui_prefs.json"
        try:
            with open(prefs_file, 'w') as f:
                json.dump(SessionState.get("user_preferences"), f, indent=2)
        except Exception as e:
            st.error(f"設定保存エラー: {e}")
    
    @staticmethod
    def load_user_preferences():
        """ユーザー設定を読み込み"""
        prefs_file = Path.home() / ".tradingagents_webui_prefs.json"
        if prefs_file.exists():
            try:
                with open(prefs_file, 'r') as f:
                    prefs = json.load(f)
                    SessionState.set("user_preferences", prefs)
                    
                    # 設定値をセッション状態に反映
                    if "default_analysts" in prefs:
                        analysts = [AnalystType(a) for a in prefs["default_analysts"]]
                        SessionState.set("selected_analysts", analysts)
                    
                    if "default_depth" in prefs:
                        SessionState.set("research_depth", prefs["default_depth"])
                    
                    if "default_provider" in prefs:
                        SessionState.set("llm_provider", prefs["default_provider"])
                        
            except Exception as e:
                st.warning(f"設定読み込みエラー: {e}")

class UIHelpers:
    """UI関連のヘルパー関数"""
    
    @staticmethod
    def format_analyst_name(analyst_type: AnalystType) -> str:
        """アナリスト名を表示用にフォーマット"""
        name_map = {
            AnalystType.MARKET: "📈 Market Analyst",
            AnalystType.SOCIAL: "💬 Social Analyst",
            AnalystType.NEWS: "📰 News Analyst",
            AnalystType.FUNDAMENTALS: "📊 Fundamentals Analyst"
        }
        return name_map.get(analyst_type, analyst_type.value)
    
    @staticmethod
    def format_progress_status(status: str) -> str:
        """進捗ステータスを表示用にフォーマット"""
        status_map = {
            "waiting": "⏳ 待機中",
            "running": "🔄 実行中",
            "completed": "✅ 完了",
            "error": "❌ エラー"
        }
        return status_map.get(status, status)
    
    @staticmethod
    def format_research_depth(depth: int) -> str:
        """研究深度を表示用にフォーマット"""
        depth_map = {
            1: "⚡ Shallow (1ラウンド)",
            2: "📝 Light (2ラウンド)",
            3: "🔍 Medium (3ラウンド)",
            4: "🔬 Deep (4ラウンド)",
            5: "🎯 Comprehensive (5ラウンド)"
        }
        return depth_map.get(depth, f"カスタム ({depth}ラウンド)")
    
    @staticmethod
    def get_provider_models(provider: str) -> List[str]:
        """プロバイダーに対応するモデル一覧を取得"""
        model_map = {
            "openai": ["gpt-4o-mini", "gpt-4o", "o1-mini", "o4-mini", "o3-2025-04-16"],
            "anthropic": ["claude-3-haiku-20240307", "claude-3-sonnet-20240229", "claude-3-5-sonnet-20241022"],
            "google": ["gemini-1.5-flash", "gemini-1.5-pro"],
            "openrouter": ["meta-llama/llama-3.1-8b-instruct", "anthropic/claude-3.5-sonnet"],
            "ollama": ["llama3.1", "mistral", "codellama"]
        }
        return model_map.get(provider, [])
    
    @staticmethod
    def create_analysis_config() -> AnalysisConfig:
        """セッション状態から分析設定を作成"""
        return AnalysisConfig(
            ticker=SessionState.get("selected_ticker"),
            analysis_date=SessionState.get("selected_date"),
            analysts=SessionState.get("selected_analysts"),
            research_depth=SessionState.get("research_depth"),
            llm_provider=SessionState.get("llm_provider"),
            backend_url=f"https://api.{SessionState.get('llm_provider')}.com/v1",
            shallow_thinker=SessionState.get("shallow_thinker"),
            deep_thinker=SessionState.get("deep_thinker")
        )
    
    @staticmethod
    def show_progress_bar(progress_list: List[Dict], container=None):
        """進捗バーを表示"""
        if not progress_list:
            return
        
        target = container if container else st
        
        # 最新の進捗状況
        latest_progress = progress_list[-1] if progress_list else None
        
        if latest_progress:
            progress_value = latest_progress.get("progress", 0.0)
            status = latest_progress.get("status", "")
            message = latest_progress.get("message", "")
            
            # プログレスバー表示
            target.progress(progress_value, text=f"{UIHelpers.format_progress_status(status)}: {message}")
            
            # 詳細ログ（最新5件）
            with target.expander("詳細ログ", expanded=False):
                for p in progress_list[-5:]:
                    timestamp = p.get("timestamp", "")
                    agent = p.get("agent", "")
                    msg = p.get("message", "")
                    st.text(f"[{timestamp[:19]}] {agent}: {msg}")
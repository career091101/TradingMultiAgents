"""
設定画面コンポーネント
"""

import streamlit as st
from datetime import datetime, date, timedelta
from typing import List
import os

import sys
from pathlib import Path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from cli.models import AnalystType
from webui.utils.state import SessionState, UIHelpers

class SettingsPage:
    """分析設定画面"""
    
    def __init__(self, cli_wrapper):
        self.cli_wrapper = cli_wrapper
    
    def render(self):
        """設定画面をレンダリング"""
        st.title("⚙️ 分析設定")
        st.markdown("分析パラメータを設定して、マルチエージェント分析を実行します。")
        
        # 基本設定セクション
        self._render_basic_settings()
        
        st.markdown("---")
        
        # アナリスト選択セクション
        self._render_analyst_selection()
        
        st.markdown("---")
        
        # LLM設定セクション
        self._render_llm_settings()
        
        st.markdown("---")
        
        # 詳細設定セクション
        self._render_advanced_settings()
        
        st.markdown("---")
        
        # アクションボタン
        self._render_action_buttons()
    
    def _render_basic_settings(self):
        """基本設定セクション"""
        st.subheader("📊 基本設定")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # ティッカー選択
            ticker = st.text_input(
                "ティッカーシンボル",
                value=SessionState.get("selected_ticker", "SPY"),
                placeholder="例: SPY, AAPL, TSLA",
                help="分析対象の株式ティッカーシンボルを入力してください"
            )
            SessionState.set("selected_ticker", ticker.upper())
            
            # よく使用されるティッカーのクイック選択
            st.markdown("**クイック選択:**")
            quick_tickers = ["SPY", "QQQ", "AAPL", "MSFT", "GOOGL", "TSLA", "JP225"]
            
            ticker_cols = st.columns(len(quick_tickers))
            for i, qt in enumerate(quick_tickers):
                with ticker_cols[i]:
                    if st.button(qt, key=f"quick_ticker_{qt}", use_container_width=True):
                        SessionState.set("selected_ticker", qt)
                        st.rerun()
        
        with col2:
            # 分析日設定
            today = date.today()
            min_date = today - timedelta(days=365)
            
            analysis_date = st.date_input(
                "分析基準日",
                value=datetime.strptime(SessionState.get("selected_date", str(today)), "%Y-%m-%d").date(),
                min_value=min_date,
                max_value=today,
                help="分析を実行する基準日を選択してください"
            )
            SessionState.set("selected_date", str(analysis_date))
            
            # 日付プリセット
            st.markdown("**日付プリセット:**")
            date_presets = {
                "今日": today,
                "昨日": today - timedelta(days=1),
                "1週間前": today - timedelta(days=7),
                "1ヶ月前": today - timedelta(days=30)
            }
            
            preset_cols = st.columns(len(date_presets))
            for i, (label, preset_date) in enumerate(date_presets.items()):
                with preset_cols[i]:
                    if st.button(label, key=f"date_preset_{i}", use_container_width=True):
                        SessionState.set("selected_date", str(preset_date))
                        st.rerun()
    
    def _render_analyst_selection(self):
        """アナリスト選択セクション"""
        st.subheader("👥 アナリストチーム選択")
        
        st.markdown("分析に参加させるアナリストを選択してください。複数選択可能です。")
        
        # 現在選択されているアナリスト
        current_analysts = SessionState.get("selected_analysts", [AnalystType.MARKET, AnalystType.NEWS])
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Market Analyst
            market_selected = st.checkbox(
                UIHelpers.format_analyst_name(AnalystType.MARKET),
                value=AnalystType.MARKET in current_analysts,
                help="テクニカル指標分析 (MACD, RSI, ボリンジャーバンド等)"
            )
            
            # Social Analyst
            social_selected = st.checkbox(
                UIHelpers.format_analyst_name(AnalystType.SOCIAL),
                value=AnalystType.SOCIAL in current_analysts,
                help="ソーシャルメディア・Redditセンチメント分析"
            )
        
        with col2:
            # News Analyst
            news_selected = st.checkbox(
                UIHelpers.format_analyst_name(AnalystType.NEWS),
                value=AnalystType.NEWS in current_analysts,
                help="ニュース分析・マクロ経済指標"
            )
            
            # Fundamentals Analyst
            fundamentals_selected = st.checkbox(
                UIHelpers.format_analyst_name(AnalystType.FUNDAMENTALS),
                value=AnalystType.FUNDAMENTALS in current_analysts,
                help="財務諸表・企業業績・バリュエーション分析"
            )
        
        # 選択されたアナリストを更新
        selected_analysts = []
        if market_selected:
            selected_analysts.append(AnalystType.MARKET)
        if social_selected:
            selected_analysts.append(AnalystType.SOCIAL)
        if news_selected:
            selected_analysts.append(AnalystType.NEWS)
        if fundamentals_selected:
            selected_analysts.append(AnalystType.FUNDAMENTALS)
        
        SessionState.set("selected_analysts", selected_analysts)
        
        # プリセット選択
        st.markdown("**アナリストプリセット:**")
        preset_col1, preset_col2, preset_col3 = st.columns(3)
        
        with preset_col1:
            if st.button("📈 テクニカル重視", key="settings_technical_preset", use_container_width=True):
                SessionState.set("selected_analysts", [AnalystType.MARKET, AnalystType.NEWS])
                st.rerun()
        
        with preset_col2:
            if st.button("📊 ファンダメンタル重視", key="settings_fundamental_preset", use_container_width=True):
                SessionState.set("selected_analysts", [AnalystType.FUNDAMENTALS, AnalystType.NEWS])
                st.rerun()
        
        with preset_col3:
            if st.button("🌐 総合分析", key="settings_comprehensive_preset", use_container_width=True):
                SessionState.set("selected_analysts", [AnalystType.MARKET, AnalystType.SOCIAL, AnalystType.NEWS, AnalystType.FUNDAMENTALS])
                st.rerun()
        
        # 警告メッセージ
        if not selected_analysts:
            st.warning("⚠️ 少なくとも1つのアナリストを選択してください")
    
    def _render_llm_settings(self):
        """LLM設定セクション"""
        st.subheader("🤖 LLM設定")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # LLMプロバイダー選択
            providers = ["openai", "anthropic", "google", "openrouter", "ollama"]
            current_provider = SessionState.get("llm_provider", "openai")
            
            provider = st.selectbox(
                "LLMプロバイダー",
                providers,
                index=providers.index(current_provider) if current_provider in providers else 0,
                help="使用するLLMプロバイダーを選択してください"
            )
            SessionState.set("llm_provider", provider)
            
            # 軽量モデル選択
            available_models = UIHelpers.get_provider_models(provider)
            current_shallow = SessionState.get("shallow_thinker", "gpt-4o-mini")
            
            if current_shallow not in available_models and available_models:
                current_shallow = available_models[0]
            
            shallow_model = st.selectbox(
                "軽量思考モデル",
                available_models,
                index=available_models.index(current_shallow) if current_shallow in available_models else 0,
                help="高頻度タスク用の軽量モデル"
            )
            SessionState.set("shallow_thinker", shallow_model)
        
        with col2:
            # 研究深度設定
            depth = st.select_slider(
                "研究深度",
                options=[1, 2, 3, 4, 5],
                value=SessionState.get("research_depth", 3),
                format_func=lambda x: UIHelpers.format_research_depth(x),
                help="分析の詳細度を設定します。深度が高いほど詳細な分析を行いますが、時間がかかります。"
            )
            SessionState.set("research_depth", depth)
            
            # 高性能モデル選択
            current_deep = SessionState.get("deep_thinker", "o4-mini")
            
            if current_deep not in available_models and available_models:
                current_deep = available_models[-1]  # 通常、最後が最も高性能
            
            deep_model = st.selectbox(
                "高性能思考モデル",
                available_models,
                index=available_models.index(current_deep) if current_deep in available_models else -1,
                help="深い分析・議論用の高性能モデル"
            )
            SessionState.set("deep_thinker", deep_model)
        
        # 推奨設定の表示
        st.info("""
        💡 **推奨設定:**
        - **軽量モデル**: 高頻度のタスク (ニュース要約、テクニカル計算) に使用
        - **高性能モデル**: 深い財務分析とエージェント間議論に使用
        - **研究深度**: 初回は3 (Medium) からお試しください
        """)
    
    def _render_advanced_settings(self):
        """詳細設定セクション"""
        show_advanced = st.checkbox("🔧 詳細設定を表示", value=SessionState.get("show_advanced_settings", False))
        SessionState.set("show_advanced_settings", show_advanced)
        
        if show_advanced:
            col1, col2 = st.columns(2)
            
            with col1:
                # バックエンドURL設定
                backend_url = st.text_input(
                    "バックエンドURL",
                    value=f"https://api.{SessionState.get('llm_provider', 'openai')}.com/v1",
                    help="LLM APIのエンドポイントURL"
                )
                
                # タイムアウト設定
                timeout = st.number_input(
                    "タイムアウト (秒)",
                    min_value=60,
                    max_value=3600,
                    value=1800,
                    help="分析の最大実行時間"
                )
            
            with col2:
                # 結果保存設定
                save_results = st.checkbox(
                    "結果を自動保存",
                    value=True,
                    help="分析結果をローカルに自動保存"
                )
                
                # デバッグモード
                debug_mode = st.checkbox(
                    "デバッグモード",
                    value=False,
                    help="詳細なログ出力を有効化"
                )
    
    def _render_action_buttons(self):
        """アクションボタンセクション"""
        st.subheader("🚀 アクション")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.button("💾 設定を保存", key="settings_save", use_container_width=True):
                self._save_settings()
                st.success("✅ 設定を保存しました")
                st.balloons()
        
        with col2:
            if st.button("🔄 設定をリセット", key="settings_reset", use_container_width=True):
                self._reset_settings()
                st.success("✅ 設定をリセットしました")
                st.rerun()
        
        with col3:
            if st.button("🔍 設定を検証", key="settings_validate", use_container_width=True):
                self._validate_settings()
        
        with col4:
            # 分析開始ボタン（設定が有効な場合のみ）
            selected_analysts = SessionState.get("selected_analysts", [])
            can_start = len(selected_analysts) > 0 and self._check_environment()
            
            if st.button("▶️ 分析開始", 
                        key="settings_start_analysis",
                        use_container_width=True, 
                        type="primary",
                        disabled=not can_start):
                SessionState.navigate_to("execution")
                st.rerun()
        
        # 設定サマリー表示
        st.markdown("---")
        self._render_settings_summary()
    
    def _save_settings(self):
        """設定を保存"""
        prefs = SessionState.get("user_preferences", {})
        prefs.update({
            "default_analysts": [a.value for a in SessionState.get("selected_analysts", [])],
            "default_depth": SessionState.get("research_depth", 3),
            "default_provider": SessionState.get("llm_provider", "openai"),
            "shallow_model": SessionState.get("shallow_thinker", "gpt-4o-mini"),
            "deep_model": SessionState.get("deep_thinker", "o4-mini")
        })
        SessionState.set("user_preferences", prefs)
        SessionState.save_user_preferences()
    
    def _reset_settings(self):
        """設定をリセット"""
        SessionState.update({
            "selected_ticker": "SPY",
            "selected_date": str(date.today()),
            "selected_analysts": [AnalystType.MARKET, AnalystType.NEWS],
            "research_depth": 3,
            "llm_provider": "openai",
            "shallow_thinker": "gpt-4o-mini",
            "deep_thinker": "o4-mini",
            "show_advanced_settings": False
        })
    
    def _validate_settings(self):
        """設定を検証"""
        issues = []
        
        # ティッカー検証
        ticker = SessionState.get("selected_ticker", "")
        if not ticker or len(ticker) < 1:
            issues.append("ティッカーシンボルが無効です")
        
        # アナリスト選択検証
        analysts = SessionState.get("selected_analysts", [])
        if not analysts:
            issues.append("アナリストが選択されていません")
        
        # 環境変数検証
        if not self._check_environment():
            issues.append("必要な環境変数が設定されていません")
        
        if issues:
            for issue in issues:
                st.error(f"❌ {issue}")
        else:
            st.success("✅ 設定に問題ありません")
    
    def _check_environment(self) -> bool:
        """環境変数をチェック"""
        required_vars = ["FINNHUB_API_KEY", "OPENAI_API_KEY"]
        return all(os.getenv(var) for var in required_vars)
    
    def _render_settings_summary(self):
        """設定サマリー表示"""
        st.subheader("📋 現在の設定")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"""
            **基本設定:**
            - ティッカー: `{SessionState.get('selected_ticker', 'N/A')}`
            - 分析日: `{SessionState.get('selected_date', 'N/A')}`
            - 研究深度: `{UIHelpers.format_research_depth(SessionState.get('research_depth', 3))}`
            """)
        
        with col2:
            analysts = SessionState.get("selected_analysts", [])
            analyst_names = [UIHelpers.format_analyst_name(a) for a in analysts]
            
            st.markdown(f"""
            **LLM設定:**
            - プロバイダー: `{SessionState.get('llm_provider', 'openai')}`
            - 軽量モデル: `{SessionState.get('shallow_thinker', 'gpt-4o-mini')}`
            - 高性能モデル: `{SessionState.get('deep_thinker', 'o4-mini')}`
            """)
        
        if analyst_names:
            st.markdown(f"**選択済みアナリスト:** {', '.join(analyst_names)}")
        else:
            st.warning("⚠️ アナリストが選択されていません")
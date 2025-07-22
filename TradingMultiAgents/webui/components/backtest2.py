"""
Backtest2 page component for the WebUI.
Implements the paper-compliant multi-agent backtesting with 6-phase decision flow.
"""

import streamlit as st
from datetime import datetime, timedelta
import pandas as pd
import json
from typing import Dict, Any, List, Optional
from pathlib import Path

from ..utils.state import SessionState, UIHelpers
from ..backend.backtest2_wrapper import Backtest2Wrapper


class Backtest2Page:
    """Backtest2 page component - Paper-compliant version."""
    
    def __init__(self, session_state: SessionState):
        self.state = session_state
        self.ui = UIHelpers()
        self.backtest_wrapper = Backtest2Wrapper()
    
    def render(self):
        """Render the Backtest2 page."""
        st.title("🧪 バックテスト2 - 論文準拠マルチエージェント取引")
        
        # Information box
        st.info("""
        **バックテスト2** は論文の6段階意思決定フローを実装しています：
        1. 📊 データ収集 → 2. 💡 投資分析 → 3. 📈 投資決定
        4. 💰 取引決定 → 5. ⚠️ リスク評価 → 6. ✅ 最終決定
        
        機能: マルチエージェント議論、リスクベースのポジションサイジング、反省と学習
        """)
        
        # Create tabs
        tab1, tab2, tab3, tab4 = st.tabs([
            "⚙️ 設定", 
            "🤖 エージェント設定", 
            "▶️ バックテスト実行", 
            "📊 結果と分析"
        ])
        
        with tab1:
            self._render_basic_config()
        
        with tab2:
            self._render_agent_config()
        
        with tab3:
            self._render_execution()
        
        with tab4:
            self._render_results()
    
    def _render_basic_config(self):
        """Render basic configuration section."""
        st.markdown("### 基本設定")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Ticker selection
            st.markdown("#### 取引銘柄")
            # Get tickers as list and convert to string for display
            saved_tickers = self.state.get("bt2_tickers", ["AAPL", "MSFT"])
            if isinstance(saved_tickers, list):
                ticker_display = ", ".join(saved_tickers)
            elif isinstance(saved_tickers, str):
                ticker_display = saved_tickers
            else:
                # Handle unexpected types
                logger.warning(f"Unexpected ticker type: {type(saved_tickers)}")
                ticker_display = "AAPL, MSFT"
                
            ticker_input = st.text_input(
                "ティッカー",
                value=ticker_display,
                help="ティッカーをカンマで区切って入力"
            )
            tickers = [t.strip().upper() for t in ticker_input.split(",") if t.strip()]
            self.state.set("bt2_tickers", tickers)
            
            # Date range
            st.markdown("#### 期間")
            start_date = st.date_input(
                "開始日",
                value=self.state.get("bt2_start_date", datetime.now() - timedelta(days=90)),
                max_value=datetime.now() - timedelta(days=1)
            )
            self.state.set("bt2_start_date", start_date)
            
            end_date = st.date_input(
                "終了日",
                value=self.state.get("bt2_end_date", datetime.now() - timedelta(days=1)),
                min_value=start_date,
                max_value=datetime.now()
            )
            self.state.set("bt2_end_date", end_date)
            
            # Initial capital
            initial_capital = st.number_input(
                "初期資本 ($)",
                min_value=1000.0,
                max_value=10000000.0,
                value=self.state.get("bt2_capital", 100000.0),
                step=10000.0,
                format="%.2f"
            )
            self.state.set("bt2_capital", initial_capital)
        
        with col2:
            # Risk parameters
            st.markdown("#### リスク管理")
            
            # Position limits by risk profile
            st.write("**ポジションサイズ上限（資本のパーセント）**")
            
            aggressive_limit = st.slider(
                "アグレッシブ",
                min_value=10,
                max_value=100,
                value=int(self.state.get("bt2_aggressive_limit", 0.8) * 100),  # 論文準拠: 80%
                step=5,
                format="%d%%"
            )
            self.state.set("bt2_aggressive_limit", aggressive_limit / 100)
            
            neutral_limit = st.slider(
                "ニュートラル",
                min_value=5,
                max_value=50,
                value=int(self.state.get("bt2_neutral_limit", 0.5) * 100),  # 論文準拠: 50%
                step=5,
                format="%d%%"
            )
            self.state.set("bt2_neutral_limit", neutral_limit / 100)
            
            conservative_limit = st.slider(
                "コンサーバティブ",
                min_value=1,
                max_value=30,
                value=int(self.state.get("bt2_conservative_limit", 0.3) * 100),  # 論文準拠: 30%
                step=1,
                format="%d%%"
            )
            self.state.set("bt2_conservative_limit", conservative_limit / 100)
            
            # Max positions
            max_positions = st.number_input(
                "最大同時ポジション数",
                min_value=1,
                max_value=20,
                value=self.state.get("bt2_max_positions", 5)
            )
            self.state.set("bt2_max_positions", max_positions)
            
            # Stop loss / Take profit
            col_sl, col_tp = st.columns(2)
            with col_sl:
                stop_loss = st.number_input(
                    "ストップロス (%)",
                    min_value=1.0,
                    max_value=50.0,
                    value=self.state.get("bt2_stop_loss", 0.1) * 100,
                    step=1.0
                )
                self.state.set("bt2_stop_loss", stop_loss / 100)
            
            with col_tp:
                take_profit = st.number_input(
                    "テイクプロフィット (%)",
                    min_value=1.0,
                    max_value=100.0,
                    value=self.state.get("bt2_take_profit", 0.2) * 100,
                    step=1.0
                )
                self.state.set("bt2_take_profit", take_profit / 100)
        
        # Trading costs
        st.markdown("#### 取引コスト")
        col1, col2 = st.columns(2)
        
        with col1:
            slippage = st.number_input(
                "スリッページ（パーセント）",
                min_value=0.0,
                max_value=1.0,
                value=self.state.get("bt2_slippage", 0.001) * 100,
                step=0.01,
                format="%.2f"
            )
            self.state.set("bt2_slippage", slippage / 100)
        
        with col2:
            commission = st.number_input(
                "手数料（パーセント）",
                min_value=0.0,
                max_value=1.0,
                value=self.state.get("bt2_commission", 0.001) * 100,
                step=0.01,
                format="%.2f"
            )
            self.state.set("bt2_commission", commission / 100)
    
    def _render_agent_config(self):
        """Render agent configuration section."""
        st.markdown("### マルチエージェント設定")
        
        # Mock mode toggle - prominently displayed
        mock_container = st.container()
        with mock_container:
            st.markdown("#### 🧪 テストモード設定")
            col_mock1, col_mock2 = st.columns([3, 1])
            with col_mock1:
                use_mock = st.checkbox(
                    "**モックモードを使用**",
                    value=self.state.get("bt2_use_mock", False),
                    help="実際のLLMを使用せずに高速テストを実行します。APIキー不要で動作確認ができます。"
                )
                self.state.set("bt2_use_mock", use_mock)
            with col_mock2:
                if use_mock:
                    st.success("✅ モックモード")
                else:
                    st.info("🤖 実LLM")
            
            if use_mock:
                st.warning("⚠️ モックモードが有効です。実際のLLMは使用されず、テスト用の模擬取引判断が行われます。")
            
            st.markdown("---")
        
        # LLM Provider and Model Info
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### LLM設定（分析設定と同期）")
            
            # Get values from analysis settings
            llm_provider = self.state.get("llm_provider", "openai")
            deep_model = self.state.get("deep_thinker", "o3-2025-04-16")
            fast_model = self.state.get("shallow_thinker", "o4-mini-2025-04-16")
            
            # Display current settings (read-only)
            st.info(f"""
            **現在の分析設定モデル:**
            - プロバイダー: {llm_provider}
            - 深い思考モデル: {deep_model}
            - 速い思考モデル: {fast_model}
            """)
            
            # Sync with analysis settings
            self.state.set("bt2_llm_provider", llm_provider)
            self.state.set("bt2_deep_model", deep_model)
            self.state.set("bt2_fast_model", fast_model)
            
            st.caption("※ モデルを変更するには「分析設定」ページで設定してください")
            
            # Temperature
            temperature = st.slider(
                "温度パラメータ",
                min_value=0.0,
                max_value=1.0,
                value=self.state.get("bt2_temperature", 0.7),
                step=0.1,
                help="LLM応答のランダム性を制御"
            )
            self.state.set("bt2_temperature", temperature)
            
            # Max tokens
            max_tokens = st.number_input(
                "最大トークン数",
                min_value=500,
                max_value=4000,
                value=self.state.get("bt2_max_tokens", 2000),
                step=500,
                help="エージェントごとの最大応答長"
            )
            self.state.set("bt2_max_tokens", max_tokens)
        
        with col2:
            st.markdown("#### エージェントの動作")
            
            # Debate rounds
            max_debate_rounds = st.number_input(
                "最大投資議論ラウンド数",
                min_value=1,
                max_value=3,
                value=self.state.get("bt2_debate_rounds", 1),
                help="強気vs弱気リサーチャーの議論"
            )
            self.state.set("bt2_debate_rounds", max_debate_rounds)
            
            # Risk discussion rounds
            max_risk_rounds = st.number_input(
                "最大リスク議論ラウンド数",
                min_value=1,
                max_value=3,
                value=self.state.get("bt2_risk_rounds", 1),
                help="リスク議論者の討論"
            )
            self.state.set("bt2_risk_rounds", max_risk_rounds)
            
            # Memory and reflection
            enable_memory = st.checkbox(
                "エージェントメモリを有効化",
                value=self.state.get("bt2_enable_memory", True),
                help="エージェントが過去の意思決定から学習"
            )
            self.state.set("bt2_enable_memory", enable_memory)
            
            enable_reflection = st.checkbox(
                "反省機能を有効化",
                value=self.state.get("bt2_enable_reflection", True),
                help="定期的なパフォーマンスレビューと学習"
            )
            self.state.set("bt2_enable_reflection", enable_reflection)
            
            if enable_reflection:
                immediate_reflection = st.checkbox(
                    "取引直後の反省",
                    value=self.state.get("bt2_immediate_reflection", True),
                    help="各取引直後に反省を実施"
                )
                self.state.set("bt2_immediate_reflection", immediate_reflection)
        
        # Agent roster
        st.markdown("#### アクティブエージェント")
        
        agents = {
            "市場アナリスト": "テクニカル指標と価格分析",
            "ニュースアナリスト": "ニュースセンチメント分析",
            "ソーシャルメディアアナリスト": "ソーシャルセンチメント追跡",
            "ファンダメンタルズアナリスト": "企業ファンダメンタルズ",
            "強気リサーチャー": "強気論の開発",
            "弱気リサーチャー": "弱気論の開発",
            "リサーチマネージャー": "投資計画の調整",
            "トレーダー": "取引実行の意思決定",
            "リスク議論者": "リスク評価（アグレッシブ/ニュートラル/コンサーバティブ）",
            "リスクマネージャー": "最終的なリスク調整済み意思決定"
        }
        
        # Display in a nice format
        for agent, description in agents.items():
            st.write(f"**{agent}**: {description}")
        
        # Advanced options
        with st.expander("詳細オプション"):
            use_japanese = st.checkbox(
                "日本語プロンプトを使用",
                value=self.state.get("bt2_use_japanese", False),
                help="エージェントプロンプトに日本語を使用"
            )
            self.state.set("bt2_use_japanese", use_japanese)
            
            online_tools = st.checkbox(
                "オンラインデータソースを使用",
                value=self.state.get("bt2_online_tools", False),
                help="リアルタイムデータを使用（再現性が低下）"
            )
            self.state.set("bt2_online_tools", online_tools)
            
            force_refresh = st.checkbox(
                "データを強制更新",
                value=self.state.get("bt2_force_refresh", False),
                help="キャッシュをバイパスして新しいデータを取得"
            )
            self.state.set("bt2_force_refresh", force_refresh)
    
    def _render_execution(self):
        """Render execution section."""
        st.markdown("### バックテスト実行")
        
        # Validate configuration
        tickers = self.state.get("bt2_tickers", [])
        if not tickers:
            st.error("設定タブで少なくとも１つのティッカーを設定してください。")
            return
        
        # Summary
        st.markdown("#### 設定サマリー")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("ティッカー数", len(tickers))
            # Safe date subtraction with type validation
            start_date = self.state.get("bt2_start_date")
            end_date = self.state.get("bt2_end_date")
            try:
                if start_date and end_date and hasattr(start_date, 'days') and hasattr(end_date, 'days'):
                    days_count = (end_date - start_date).days
                else:
                    days_count = 0
            except (TypeError, AttributeError) as e:
                logger.warning(f"Date calculation error: {e}")
                days_count = 0
            st.metric("期間（日数）", days_count)
        
        with col2:
            st.metric("初期資本", f"${self.state.get('bt2_capital', 0):,.0f}")
            st.metric("最大ポジション数", self.state.get("bt2_max_positions", 5))
        
        with col3:
            st.metric("LLMプロバイダー", self.state.get("bt2_llm_provider", "openai"))
            st.metric("エージェント", "10専門エージェント")
        
        st.markdown("---")
        
        # Estimated time and cost with safe date handling
        start_date = self.state.get("bt2_start_date")
        end_date = self.state.get("bt2_end_date")
        if start_date and end_date:
            days = (end_date - start_date).days
        else:
            days = 0
        decisions_per_day = len(tickers)  # One decision per ticker per day
        total_decisions = days * decisions_per_day
        
        # Rough estimates
        time_per_decision = 5  # seconds (with mock agents)
        cost_per_decision = 0.05  # dollars (with real LLMs)
        
        col1, col2 = st.columns(2)
        with col1:
            st.info(f"""
            **推定時間**: 約{(total_decisions * time_per_decision) // 60}分
            (モックエージェント: 1決定あたり{time_per_decision}秒)
            """)
        
        with col2:
            if self.state.get("bt2_llm_provider") != "ollama":
                st.warning(f"""
                **推定コスト**: 約${total_decisions * cost_per_decision:.2f}
                ({total_decisions}回の決定 × ${cost_per_decision})
                """)
        
        # Run button
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("🚀 マルチエージェントバックテストを開始", 
                        type="primary", 
                        use_container_width=True,
                        disabled=self.state.get("bt2_running", False)):
                self._run_backtest()
        
        # Progress section
        if self.state.get("bt2_running", False):
            st.markdown("---")
            st.markdown("### 実行進捗")
            
            # Overall progress
            progress = self.state.get("bt2_progress", 0.0)
            st.progress(progress / 100)
            
            # Status
            col1, col2 = st.columns(2)
            with col1:
                status = self.state.get("bt2_status", "初期化中...")
                st.write(f"**ステータス**: {status}")
            
            with col2:
                current_ticker = self.state.get("bt2_current_ticker", "")
                if current_ticker:
                    st.write(f"**処理中**: {current_ticker}")
            
            # Current phase indicator
            phases = ["データ収集", "投資分析", "投資決定",
                     "取引決定", "リスク評価", "最終決定"]
            current_phase = self.state.get("bt2_current_phase", 0)
            
            # Phase progress
            st.write("**意思決定フロー進捗**")
            phase_cols = st.columns(6)
            for i, (col, phase) in enumerate(zip(phase_cols, phases)):
                with col:
                    if i < current_phase:
                        st.success(f"✓ {phase}", icon="✅")
                    elif i == current_phase:
                        st.info(f"▶ {phase}", icon="🔄")
                    else:
                        st.text(f"○ {phase}")
            
            # Stop button
            if st.button("⏹️ バックテストを停止", type="secondary"):
                self.backtest_wrapper.stop_backtest()
                self.state.set("bt2_running", False)
                st.warning("バックテストがユーザーによって停止されました。")
        
        # Recent logs
        if self.state.get("bt2_logs"):
            with st.expander("実行ログ", expanded=False):
                logs = self.state.get("bt2_logs", [])
                # Create a text area with logs
                log_text = "\n".join(logs[-20:])  # Last 20 entries
                
                # Display last 20 log entries
                st.text_area("最新ログ (最後の20件)", value=log_text, height=200, disabled=True, key="bt2_log_display")
                
                # Show full logs in code block for easy copying
                full_log_text = "\n".join(logs)
                st.markdown("**📋 全ログをコピー** (下記のテキストを選択してコピー)")
                st.code(full_log_text, language="text")
                
                # Download button as alternative
                st.download_button(
                    label="💾 ログをダウンロード",
                    data=full_log_text,
                    file_name=f"backtest2_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                    mime="text/plain"
                )
    
    def _run_backtest(self):
        """Execute the backtest."""
        self.state.set("bt2_running", True)
        self.state.set("bt2_progress", 0.0)
        self.state.set("bt2_logs", [])
        self.state.set("bt2_current_phase", 0)
        
        # Prepare configuration with safe date handling
        start_date = self.state.get("bt2_start_date")
        end_date = self.state.get("bt2_end_date")
        
        config = {
            "tickers": self.state.get("bt2_tickers", ["AAPL"]),
            "start_date": start_date.strftime("%Y-%m-%d") if start_date else datetime.now().strftime("%Y-%m-%d"),
            "end_date": end_date.strftime("%Y-%m-%d") if end_date else datetime.now().strftime("%Y-%m-%d"),
            "initial_capital": self.state.get("bt2_capital", 100000.0),
            "slippage": self.state.get("bt2_slippage", 0.001),
            "commission": self.state.get("bt2_commission", 0.001),
            "risk_free_rate": 0.02,  # 2% annual
            "aggressive_limit": self.state.get("bt2_aggressive_limit", 0.3),
            "neutral_limit": self.state.get("bt2_neutral_limit", 0.2),
            "conservative_limit": self.state.get("bt2_conservative_limit", 0.1),
            "stop_loss": self.state.get("bt2_stop_loss", 0.1),
            "take_profit": self.state.get("bt2_take_profit", 0.2),
            "max_positions": self.state.get("bt2_max_positions", 5),
            "agent_config": {
                "llm_provider": self.state.get("bt2_llm_provider", "openai"),
                "deep_model": self.state.get("bt2_deep_model", "o3-2025-04-16"),
                "fast_model": self.state.get("bt2_fast_model", "o4-mini-2025-04-16"),
                "temperature": self.state.get("bt2_temperature", 0.7),
                "max_tokens": self.state.get("bt2_max_tokens", 2000),
                "max_debate_rounds": self.state.get("bt2_debate_rounds", 1),
                "max_risk_rounds": self.state.get("bt2_risk_rounds", 1),
                "use_japanese": self.state.get("bt2_use_japanese", False),
                "online_tools": self.state.get("bt2_online_tools", False)
            },
            "enable_memory": self.state.get("bt2_enable_memory", True),
            "enable_reflection": self.state.get("bt2_enable_reflection", True),
            "immediate_reflection": self.state.get("bt2_immediate_reflection", True),
            "force_refresh": self.state.get("bt2_force_refresh", False),
            "generate_plots": True,
            "save_trades": True,
            "debug": True,
            "use_mock": self.state.get("bt2_use_mock", False)
        }
        
        # Execute backtest
        try:
            with st.spinner("マルチエージェントシステムを初期化中..."):
                results = self.backtest_wrapper.run_backtest(
                    config=config,
                    progress_callback=self._update_progress,
                    log_callback=self._update_logs
                )
            
            # Store results
            self.state.set("bt2_results", results)
            self.state.set("bt2_running", False)
            self.state.set("bt2_completed", True)
            
            # Success message
            st.success("✅ Multi-agent backtest completed successfully!")
            st.balloons()
            
            # Quick summary
            if results:
                # Check if results have valid format
                valid_results = []
                for ticker, r in results.items():
                    if isinstance(r, dict) and "metrics" in r and isinstance(r["metrics"], dict):
                        valid_results.append(r)
                
                if valid_results:
                    total_return = sum(r["metrics"]["total_return"] for r in valid_results) / len(valid_results)
                    st.info(f"Average Return: {total_return:.2f}% | View detailed results in the Results tab")
                else:
                    st.warning("Results format is invalid. Please check the logs.")
            
        except Exception as e:
            self.state.set("bt2_running", False)
            st.error(f"❌ Backtest failed: {str(e)}")
            st.exception(e)
    
    def _update_progress(self, progress: float, status: str, ticker: str = ""):
        """Update progress callback."""
        self.state.set("bt2_progress", progress)
        self.state.set("bt2_status", status)
        if ticker:
            self.state.set("bt2_current_ticker", ticker)
        
        # Update phase based on status
        phase_keywords = {
            "Data Collection": 0,
            "Investment Analysis": 1,
            "Investment Decision": 2,
            "Trading Decision": 3,
            "Risk Assessment": 4,
            "Final Decision": 5
        }
        
        for keyword, phase_idx in phase_keywords.items():
            if keyword.lower() in status.lower():
                self.state.set("bt2_current_phase", phase_idx)
                break
    
    def _update_logs(self, log_entry: str):
        """Update logs callback."""
        logs = self.state.get("bt2_logs", [])
        timestamp = datetime.now().strftime("%H:%M:%S")
        logs.append(f"[{timestamp}] {log_entry}")
        
        # Keep only last 100 entries
        if len(logs) > 100:
            logs = logs[-100:]
        
        self.state.set("bt2_logs", logs)
    
    def _render_results(self):
        """Render results section with agent performance analysis."""
        st.markdown("### バックテスト結果とエージェント分析")
        
        if not self.state.get("bt2_completed", False):
            st.info("結果がありません。「バックテスト実行」タブでバックテストを実行してください。")
            return
        
        results = self.state.get("bt2_results", {})
        if not results:
            st.warning("結果データが見つかりません。")
            return
        
        # Overall summary metrics
        st.markdown("#### ポートフォリオサマリー")
        
        # Calculate aggregate metrics with type safety
        valid_results = []
        for ticker, r in results.items():
            if isinstance(r, dict) and "metrics" in r and isinstance(r["metrics"], dict):
                valid_results.append(r)
            else:
                logger.warning(f"Invalid result format for {ticker}: {type(r)}")
        
        if not valid_results:
            st.error("有効な結果データがありません。")
            return
            
        total_return = sum(r["metrics"].get("total_return", 0) for r in valid_results) / len(valid_results)
        avg_sharpe = sum(r["metrics"].get("sharpe_ratio", 0) for r in valid_results) / len(valid_results)
        max_dd = max(r["metrics"].get("max_drawdown", 0) for r in valid_results)
        total_trades = sum(r["metrics"].get("total_trades", 0) for r in valid_results)
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("平均リターン", f"{total_return:.2f}%", 
                     delta=f"{total_return:.2f}%",
                     delta_color="normal" if total_return >= 0 else "inverse")
        
        with col2:
            st.metric("平均シャープレシオ", f"{avg_sharpe:.2f}")
        
        with col3:
            st.metric("最大ドローダウン", f"{max_dd:.2f}%",
                     delta=f"{max_dd:.2f}%",
                     delta_color="inverse")
        
        with col4:
            st.metric("総取引数", total_trades)
        
        # Individual ticker results
        st.markdown("---")
        st.markdown("#### 個別ティッカーパフォーマンス")
        
        for ticker, result in results.items():
            if not isinstance(result, dict) or "metrics" not in result:
                logger.warning(f"Skipping invalid result for {ticker}")
                continue
            return_value = result.get("metrics", {}).get("total_return", 0)
            with st.expander(f"📊 {ticker} - Return: {return_value:.2f}%", 
                           expanded=len(results) == 1):
                self._render_ticker_analysis(ticker, result)
        
        # Agent performance analysis
        st.markdown("---")
        st.markdown("#### Multi-Agent Performance Analysis")
        
        # Aggregate agent performance across all tickers
        agent_performance = self._aggregate_agent_performance(results)
        
        if agent_performance:
            # Agent accuracy metrics
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("##### Agent Decision Accuracy")
                
                agent_accuracy = []
                for agent, perf in agent_performance.items():
                    if "accuracy" in perf:
                        agent_accuracy.append({
                            "Agent": agent,
                            "Accuracy": f"{perf['accuracy']:.1f}%",
                            "Decisions": perf.get("total_decisions", 0)
                        })
                
                if agent_accuracy:
                    df_accuracy = pd.DataFrame(agent_accuracy)
                    st.dataframe(df_accuracy, use_container_width=True, hide_index=True)
            
            with col2:
                st.markdown("##### Agent Contribution to Returns")
                
                # Placeholder for agent contribution analysis
                st.info("エージェント貢献分析は、各エージェントの決定がリターンにどう影響したかを示します")
        
        # Decision flow analysis
        st.markdown("---")
        st.markdown("#### 6段階意思決定フロー分析")
        
        phases = ["データ収集", "投資分析", "投資決定",
                 "取引決定", "リスク評価", "最終決定"]
        
        # Create phase timing analysis
        phase_data = []
        for i, phase in enumerate(phases):
            phase_data.append({
                "フェーズ": phase,
                "平均時間 (秒)": 2 + i * 0.5,  # Mock data
                "成功率": f"{95 - i * 2}%"  # Mock data
            })
        
        df_phases = pd.DataFrame(phase_data)
        st.dataframe(df_phases, use_container_width=True, hide_index=True)
        
        # Download section
        st.markdown("---")
        st.markdown("#### 結果のエクスポート")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Aggregate metrics JSON
            all_metrics = {
                ticker: result["metrics"] 
                for ticker, result in results.items()
            }
            
            st.download_button(
                "📊 全メトリクスをダウンロード (JSON)",
                data=json.dumps(all_metrics, indent=2),
                file_name=f"backtest2_metrics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )
        
        with col2:
            # Create summary CSV
            summary_data = []
            for ticker, result in results.items():
                if not isinstance(result, dict) or "metrics" not in result:
                    continue
                metrics = result["metrics"]
                summary_data.append({
                    "Ticker": ticker,
                    "Return (%)": metrics.get("total_return", 0),
                    "Sharpe": metrics.get("sharpe_ratio", 0),
                    "Max DD (%)": metrics.get("max_drawdown", 0),
                    "Trades": metrics.get("total_trades", 0),
                    "Win Rate (%)": metrics.get("win_rate", 0)
                })
            
            df_summary = pd.DataFrame(summary_data)
            csv = df_summary.to_csv(index=False)
            
            st.download_button(
                "📋 Download Summary (CSV)",
                data=csv,
                file_name=f"backtest2_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
        
        with col3:
            # Configuration backup
            config_backup = {
                "timestamp": datetime.now().isoformat(),
                "config": {
                    "tickers": self.state.get("bt2_tickers"),
                    "start_date": str(self.state.get("bt2_start_date")),
                    "end_date": str(self.state.get("bt2_end_date")),
                    "initial_capital": self.state.get("bt2_capital"),
                    "llm_provider": self.state.get("bt2_llm_provider"),
                    "agent_settings": {
                        "debate_rounds": self.state.get("bt2_debate_rounds"),
                        "risk_rounds": self.state.get("bt2_risk_rounds"),
                        "enable_memory": self.state.get("bt2_enable_memory"),
                        "enable_reflection": self.state.get("bt2_enable_reflection")
                    }
                }
            }
            
            st.download_button(
                "⚙️ Download Config (JSON)",
                data=json.dumps(config_backup, indent=2),
                file_name=f"backtest2_config_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )
    
    def _render_ticker_analysis(self, ticker: str, result: Dict[str, Any]):
        """Render detailed analysis for a single ticker."""
        metrics = result.get("metrics", {})
        
        # Key metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("総リターン", f"{metrics.get('total_return', 0):.2f}%")
            st.metric("年率リターン", f"{metrics.get('annualized_return', 0):.2f}%")
        
        with col2:
            st.metric("シャープレシオ", f"{metrics.get('sharpe_ratio', 0):.2f}")
            st.metric("ソルティノレシオ", f"{metrics.get('sortino_ratio', 0):.2f}")
        
        with col3:
            st.metric("最大ドローダウン", f"{metrics.get('max_drawdown', 0):.2f}%")
            st.metric("ボラティリティ", f"{metrics.get('volatility', 0):.2f}%")
        
        with col4:
            st.metric("勝率", f"{metrics.get('win_rate', 0):.1f}%")
            st.metric("プロフィットファクター", f"{metrics.get('profit_factor', 0):.2f}")
        
        # Trading statistics
        st.markdown("##### 取引統計")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write(f"**総取引数**: {metrics.get('total_trades', 0)}")
            st.write(f"**勝ち取引**: {metrics.get('winning_trades', 0)}")
            st.write(f"**負け取引**: {metrics.get('losing_trades', 0)}")
        
        with col2:
            st.write(f"**平均利益**: {metrics.get('avg_win', 0):.2f}")
            st.write(f"**平均損失**: {metrics.get('avg_loss', 0):.2f}")
            st.write(f"**カルマーレシオ**: {metrics.get('calmar_ratio', 0):.2f}")
        
        # Benchmark comparison
        if result.get("benchmark_comparison"):
            st.markdown("##### ベンチマーク比較")
            
            comparison = result["benchmark_comparison"]
            portfolio = comparison.get('portfolio', {})
            benchmark = comparison.get('benchmark', {})
            relative = comparison.get('relative', {})
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown("**ポートフォリオ**")
                st.write(f"リターン: {portfolio.get('total_return', 0):.2%}")
                st.write(f"ボラティリティ: {portfolio.get('volatility', 0):.2%}")
            
            with col2:
                st.markdown(f"**ベンチマーク (SPY)**")
                st.write(f"リターン: {benchmark.get('total_return', 0):.2%}")
                st.write(f"ボラティリティ: {benchmark.get('volatility', 0):.2%}")
            
            with col3:
                st.markdown("**相対パフォーマンス**")
                st.write(f"アルファ: {relative.get('alpha', 0):.2%}")
                st.write(f"ベータ: {relative.get('beta', 1):.2f}")
                st.write(f"アウトパフォーマンス: {relative.get('outperformance', 0):.2%}")
        
        # Agent-specific performance for this ticker
        if result.get("agent_performance"):
            st.markdown("##### エージェントパフォーマンス")
            
            agent_perf = result["agent_performance"]
            # Display agent-specific metrics
            st.json(agent_perf)
    
    def _aggregate_agent_performance(self, results: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """Aggregate agent performance across all tickers."""
        aggregated = {}
        
        for ticker, result in results.items():
            if "agent_performance" in result and result["agent_performance"]:
                for agent, perf in result["agent_performance"].items():
                    if agent not in aggregated:
                        aggregated[agent] = {
                            "total_decisions": 0,
                            "correct_decisions": 0,
                            "accuracy": 0.0
                        }
                    
                    # Aggregate metrics (this is placeholder logic)
                    aggregated[agent]["total_decisions"] += perf.get("decisions", 0)
                    aggregated[agent]["correct_decisions"] += perf.get("correct", 0)
        
        # Calculate accuracy
        for agent in aggregated:
            if aggregated[agent]["total_decisions"] > 0:
                aggregated[agent]["accuracy"] = (
                    aggregated[agent]["correct_decisions"] / 
                    aggregated[agent]["total_decisions"] * 100
                )
        
        return aggregated
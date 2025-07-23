"""
リアルタイム実行画面コンポーネント
"""

import streamlit as st
import asyncio
import threading
import time
from datetime import datetime
from typing import Dict, List, Any
import os
import logging

import sys
from pathlib import Path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from webui.utils.state import SessionState, UIHelpers
from webui.backend.cli_wrapper import AnalysisConfig, AnalysisProgress

# ログ設定
logger = logging.getLogger(__name__)

class ExecutionPage:
    """分析実行画面"""
    
    def __init__(self, cli_wrapper):
        self.cli_wrapper = cli_wrapper
    
    def render(self):
        """実行画面をレンダリング"""
        st.title("▶️ 分析実行")
        
        # 現在の設定確認
        if not self._validate_config():
            return
        
        # 実行状態に応じて画面を切り替え
        is_running = SessionState.get("analysis_running", False)
        
        if not is_running:
            self._render_pre_execution()
        else:
            self._render_during_execution()
    
    def _validate_config(self) -> bool:
        """設定の妥当性をチェック"""
        issues = []
        
        # 基本設定チェック
        ticker = SessionState.get("selected_ticker", "")
        if not ticker:
            issues.append("ティッカーシンボルが設定されていません")
        
        date = SessionState.get("selected_date", "")
        if not date:
            issues.append("分析日が設定されていません")
        
        analysts = SessionState.get("selected_analysts", [])
        if not analysts:
            issues.append("アナリストが選択されていません")
        
        # 環境変数チェック
        required_vars = ["FINNHUB_API_KEY", "OPENAI_API_KEY"]
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        if missing_vars:
            issues.append(f"環境変数が不足: {', '.join(missing_vars)}")
        
        if issues:
            st.error("🚫 分析を開始できません")
            for issue in issues:
                st.error(f"• {issue}")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("⚙️ 設定画面へ", type="primary", use_container_width=True, 
                           key="exec_to_settings", help="設定画面に移動"):
                    SessionState.navigate_to("settings")
                    st.rerun()
            
            with col2:
                if st.button("🏠 ダッシュボードへ", use_container_width=True, 
                           key="exec_to_dashboard", help="ダッシュボードに移動"):
                    SessionState.navigate_to("dashboard")
                    st.rerun()
            
            return False
        
        return True
    
    def _render_pre_execution(self):
        """実行前画面"""
        st.markdown("分析設定を確認して実行を開始してください。")
        
        # 設定確認セクション
        self._render_config_summary()
        
        st.markdown("---")
        
        # 実行ボタンセクション
        self._render_execution_controls()
        
        st.markdown("---")
        
        # 注意事項
        self._render_execution_notes()
    
    def _render_during_execution(self):
        """実行中画面"""
        st.markdown("🔄 **分析実行中...** お待ちください")
        
        # 実行制御
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            st.markdown(f"**実行中**: {SessionState.get('selected_ticker')} ({SessionState.get('selected_date')})")
        
        with col2:
            if st.button("⏹️ 停止", type="secondary", use_container_width=True, 
                       key="exec_stop_analysis", help="分析を強制停止"):
                self._stop_analysis()
        
        with col3:
            if st.button("🔄 更新", use_container_width=True, 
                       key="exec_refresh", help="画面を更新"):
                st.rerun()
        
        st.markdown("---")
        
        # 進捗表示
        self._render_progress_display()
        
        st.markdown("---")
        
        # リアルタイムログ
        self._render_live_log()
        
        # 自動更新（10秒間隔）
        auto_refresh = st.checkbox("自動更新", value=SessionState.get("auto_refresh", False), 
                                 key="auto_refresh_toggle", help="10秒間隔で自動更新")
        SessionState.set("auto_refresh", auto_refresh)
        
        if auto_refresh:
            # 最終更新時刻を取得
            last_update = SessionState.get("last_update_time", 0)
            current_time = time.time()
            
            # 10秒経過したら更新
            if current_time - last_update >= 10:
                SessionState.set("last_update_time", current_time)
                st.rerun()
    
    def _render_config_summary(self):
        """設定サマリー表示"""
        st.subheader("📋 実行設定確認")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 📊 基本設定")
            st.markdown(f"""
            - **ティッカー**: `{SessionState.get('selected_ticker')}`
            - **分析日**: `{SessionState.get('selected_date')}`
            - **研究深度**: `{UIHelpers.format_research_depth(SessionState.get('research_depth'))}`
            """)
            
            st.markdown("### 🤖 LLM設定")
            st.markdown(f"""
            - **プロバイダー**: `{SessionState.get('llm_provider')}`
            - **軽量モデル**: `{SessionState.get('shallow_thinker')}`
            - **高性能モデル**: `{SessionState.get('deep_thinker')}`
            """)
        
        with col2:
            st.markdown("### 👥 選択アナリスト")
            analysts = SessionState.get("selected_analysts", [])
            
            if analysts:
                for analyst in analysts:
                    st.markdown(f"- {UIHelpers.format_analyst_name(analyst)}")
            else:
                st.warning("アナリストが選択されていません")
            
            # その他の有効チーム
            st.markdown("### 🎯 有効チーム")
            if SessionState.get("enable_research_team", False):
                st.markdown("- 🔬 研究チーム")
            if SessionState.get("enable_risk_team", False):
                st.markdown("- ⚖️ リスク管理チーム")
            if SessionState.get("enable_trader", False):
                st.markdown("- 📈 トレーダー")
            if SessionState.get("enable_portfolio_manager", False):
                st.markdown("- 🎯 ポートフォリオマネージャー")
            
            st.markdown("### ⏱️ 予想実行時間")
            depth = SessionState.get('research_depth', 3)
            analyst_count = len(analysts)
            estimated_time = self._estimate_execution_time(depth, analyst_count)
            
            st.info(f"約 **{estimated_time}分** (目安)")
            st.caption("実際の時間は市場状況やAPIレスポンス時間により変動します")
    
    def _render_execution_controls(self):
        """実行制御ボタン"""
        st.subheader("🚀 実行制御")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("▶️ 分析開始", 
                        type="primary", 
                        use_container_width=True, 
                        key="exec_start_analysis",
                        help="現在の設定で分析を開始"):
                self._start_analysis()
        
        with col2:
            if st.button("⚙️ 設定変更", 
                        use_container_width=True, 
                        key="exec_change_settings",
                        help="分析設定を変更"):
                SessionState.navigate_to("settings")
                st.rerun()
        
        with col3:
            if st.button("🏠 ダッシュボード", 
                        use_container_width=True, 
                        key="exec_to_home",
                        help="ダッシュボードに戻る"):
                SessionState.navigate_to("dashboard")
                st.rerun()
    
    def _render_execution_notes(self):
        """実行時の注意事項"""
        st.subheader("ℹ️ 実行時の注意事項")
        
        with st.expander("詳細を表示", expanded=False):
            st.markdown("""
            ### 📝 実行前の確認事項
            - **環境変数**: 必要なAPI Keyが設定されていることを確認してください
            - **ネットワーク**: 安定したインターネット接続が必要です
            - **時間**: 分析完了まで数分から数十分かかる場合があります
            
            ### 🔄 実行中の動作
            - **自動保存**: 分析結果は自動的に `results/` ディレクトリに保存されます
            - **進捗表示**: リアルタイムで各エージェントの実行状況を表示します
            - **ログ出力**: 詳細な実行ログを確認できます
            
            ### ⚠️ 注意点
            - **ブラウザタブを閉じない**: 実行中はブラウザタブを開いたままにしてください
            - **重複実行禁止**: 同じティッカー・日付の分析を同時実行はできません
            - **エラー処理**: エラーが発生した場合は自動的に停止し、ログに記録されます
            
            ### 🛑 緊急時の対処
            - **停止ボタン**: 実行中に「停止」ボタンで強制終了できます
            - **プロセス確認**: システムレベルでプロセスが残る場合は手動で終了してください
            """)
    
    def _render_progress_display(self):
        """進捗表示"""
        st.subheader("📈 実行進捗")
        
        progress_list = SessionState.get("analysis_progress", [])
        
        if not progress_list:
            st.info("実行状況の情報を取得中...")
            return
        
        # 最新の進捗情報
        latest_progress = progress_list[-1] if progress_list else None
        
        if latest_progress:
            # メイン進捗バー
            progress_value = latest_progress.get("progress", 0.0)
            status = latest_progress.get("status", "")
            message = latest_progress.get("message", "")
            
            st.progress(progress_value, text=f"{UIHelpers.format_progress_status(status)}: {message}")
            
            # エージェント別状況
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("### 🤖 エージェント状況")
                
                # 各エージェントのステータスを表示
                expected_agents = []
                
                # アナリストチーム
                analysts = SessionState.get("selected_analysts", [])
                if analysts:
                    analyst_map = {
                        "market": "Market Analyst",
                        "social": "Social Analyst",
                        "news": "News Analyst",
                        "fundamentals": "Fundamentals Analyst"
                    }
                    for analyst in analysts:
                        if analyst.value in analyst_map:
                            expected_agents.append(analyst_map[analyst.value])
                
                # 研究チーム
                if SessionState.get("enable_research_team", False):
                    if SessionState.get("enable_bull_researcher", False):
                        expected_agents.append("Bull Researcher")
                    if SessionState.get("enable_bear_researcher", False):
                        expected_agents.append("Bear Researcher")
                    if SessionState.get("enable_research_manager", False):
                        expected_agents.append("Research Manager")
                
                # リスク管理チーム
                if SessionState.get("enable_risk_team", False):
                    if SessionState.get("enable_aggressive_analyst", False):
                        expected_agents.append("Aggressive Analyst")
                    if SessionState.get("enable_conservative_analyst", False):
                        expected_agents.append("Conservative Analyst")
                    if SessionState.get("enable_neutral_analyst", False):
                        expected_agents.append("Neutral Analyst")
                
                # トレーダーとポートフォリオマネージャー
                if SessionState.get("enable_trader", False):
                    expected_agents.append("Trader")
                if SessionState.get("enable_portfolio_manager", False):
                    expected_agents.append("Portfolio Manager")
                
                for agent in expected_agents:
                    # この エージェントの最新状況を取得
                    agent_progress = None
                    for p in reversed(progress_list):
                        if agent.lower().replace(" ", "") in p.get("agent", "").lower().replace(" ", ""):
                            agent_progress = p
                            break
                    
                    if agent_progress:
                        status_icon = {
                            "waiting": "⏳",
                            "running": "🔄", 
                            "completed": "✅",
                            "error": "❌"
                        }.get(agent_progress.get("status", "waiting"), "⏳")
                        
                        st.markdown(f"{status_icon} **{agent}**: {agent_progress.get('message', '待機中')}")
                    else:
                        st.markdown(f"⏳ **{agent}**: 待機中")
            
            with col2:
                st.markdown("### 📊 実行統計")
                
                # 実行統計情報
                total_messages = len(progress_list)
                completed_count = len([p for p in progress_list if p.get("status") == "completed"])
                error_count = len([p for p in progress_list if p.get("status") == "error"])
                
                st.markdown(f"""
                - **総メッセージ数**: {total_messages}
                - **完了タスク**: {completed_count}
                - **エラー数**: {error_count}
                - **開始時刻**: {progress_list[0].get('timestamp', 'N/A')[:19] if progress_list else 'N/A'}
                """)
                
                # 経過時間計算
                if progress_list:
                    start_time = datetime.fromisoformat(progress_list[0].get('timestamp', ''))
                    elapsed = datetime.now() - start_time
                    st.markdown(f"- **経過時間**: {elapsed.seconds // 60}分{elapsed.seconds % 60}秒")
    
    def _render_live_log(self):
        """リアルタイムログ表示"""
        st.subheader("📝 実行ログ")
        
        progress_list = SessionState.get("analysis_progress", [])
        
        if not progress_list:
            st.info("ログ情報がまだありません")
            return
        
        # ログ表示オプション
        col1, col2, col3 = st.columns(3)
        
        with col1:
            show_count = st.selectbox(
                "表示件数",
                [10, 20, 50, 100],
                index=1,
                key="log_show_count"
            )
        
        with col2:
            filter_status = st.selectbox(
                "ステータスフィルター",
                ["全て", "running", "completed", "error"],
                key="log_filter_status"
            )
        
        with col3:
            if st.button("🔄 ログ更新", use_container_width=True, key="exec_refresh_log"):
                st.rerun()
        
        # ログフィルタリング
        filtered_logs = progress_list
        if filter_status != "全て":
            filtered_logs = [p for p in progress_list if p.get("status") == filter_status]
        
        # 最新N件を表示
        recent_logs = filtered_logs[-show_count:]
        
        # ログ表示（CLIライクな表示）
        log_container = st.container()
        with log_container:
            # ログを時系列順で表示（最新が下）
            for i, log_entry in enumerate(recent_logs):
                timestamp = log_entry.get("timestamp", "")[:19]
                agent = log_entry.get("agent", "")
                status = log_entry.get("status", "")
                message = log_entry.get("message", "")
                stage = log_entry.get("stage", "")
                
                # CLIログの形式に合わせて表示
                if stage == "tools":
                    # ツール呼び出しログ
                    st.code(f"🔧 [{timestamp}] {message}", language="text")
                elif agent in ["Market Analyst", "Social Analyst", "News Analyst", "Fundamentals Analyst"]:
                    # アナリストログ  
                    if status == "running":
                        st.info(f"📊 [{timestamp}] {agent}: {message}")
                    elif status == "completed":
                        st.success(f"✅ [{timestamp}] {agent}: {message}")
                elif agent == "Research Team":
                    # リサーチチームログ
                    st.info(f"🔬 [{timestamp}] {message}")
                elif agent == "Trader":
                    # トレーダーログ
                    st.info(f"💼 [{timestamp}] {message}")
                elif agent == "Portfolio Manager":
                    # ポートフォリオマネージャーログ
                    st.info(f"🎯 [{timestamp}] {message}")
                elif status == "error":
                    # エラーログ
                    st.error(f"❌ [{timestamp}] {agent}: {message}")
                elif status == "completed":
                    # 完了ログ
                    st.success(f"✅ [{timestamp}] {agent}: {message}")
                else:
                    # 一般ログ
                    st.text(f"📝 [{timestamp}] {agent}: {message}")
                    
            # 自動スクロール（最新ログを表示）
            if recent_logs:
                st.empty()  # 最下部にスペースを作成
    
    def _start_analysis(self):
        """分析を開始"""
        try:
            # 実行状態を設定
            SessionState.set("analysis_running", True)
            SessionState.clear_progress()
            
            # 分析設定を作成
            config = UIHelpers.create_analysis_config()
            
            # バックグラウンドで分析実行
            self._run_analysis_in_background(config)
            
            st.success("✅ 分析を開始しました")
            st.rerun()
            
        except Exception as e:
            st.error(f"❌ 分析開始エラー: {e}")
            SessionState.set("analysis_running", False)
    
    def _run_analysis_in_background(self, config: AnalysisConfig):
        """バックグラウンドで分析実行"""
        def run_async():
            try:
                # asyncioイベントループを作成して実行
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                result = loop.run_until_complete(
                    self.cli_wrapper.run_analysis(config)
                )
                
                # 実行完了
                SessionState.set("analysis_running", False)
                SessionState.set("analysis_results", result)
                
                loop.close()
                
            except Exception as e:
                SessionState.set("analysis_running", False)
                SessionState.add_progress(AnalysisProgress(
                    stage="error",
                    agent="system",
                    status="error",
                    progress=0.0,
                    message=f"バックグラウンド実行エラー: {str(e)}",
                    timestamp=datetime.now()
                ))
        
        # バックグラウンドスレッドで実行
        thread = threading.Thread(target=run_async, daemon=True)
        thread.start()
    
    def _stop_analysis(self):
        """分析を停止"""
        SessionState.set("analysis_running", False)
        SessionState.add_progress(AnalysisProgress(
            stage="stopped",
            agent="user",
            status="error",
            progress=0.0,
            message="ユーザーによって停止されました",
            timestamp=datetime.now()
        ))
        st.warning("⚠️ 分析を停止しました")
        st.rerun()
    
    def _estimate_execution_time(self, depth: int, analyst_count: int) -> int:
        """実行時間を推定（分単位）"""
        # 基本時間：深度 × アナリスト数 × 2分
        base_time = depth * analyst_count * 2
        
        # 議論・まとめフェーズの時間
        discussion_time = depth * 3
        
        # 合計時間
        total_time = base_time + discussion_time
        
        return max(5, min(total_time, 60))  # 5分〜60分の範囲
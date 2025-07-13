"""
ダッシュボードコンポーネント
"""

import streamlit as st
from datetime import datetime, timedelta
from typing import List, Dict, Any

import sys
from pathlib import Path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from webui.utils.state import SessionState, UIHelpers
from cli.models import AnalystType

class Dashboard:
    """メインダッシュボード"""
    
    def __init__(self, cli_wrapper):
        self.cli_wrapper = cli_wrapper
    
    def render(self):
        """ダッシュボードをレンダリング"""
        st.title("🏠 ダッシュボード")
        st.markdown("TradingAgents WebUIの概要とクイックアクセス")
        
        # メトリクス表示
        self._render_metrics()
        
        st.markdown("---")
        
        # クイックアクション
        self._render_quick_actions()
        
        st.markdown("---")
        
        # 最近の分析履歴
        self._render_recent_history()
        
        st.markdown("---")
        
        # システム情報
        self._render_system_info()
    
    def _render_metrics(self):
        """メトリクス表示"""
        st.subheader("📊 統計情報")
        
        # 分析履歴を取得
        history = self.cli_wrapper.get_analysis_history()
        
        # メトリクス計算
        total_analyses = len(history)
        completed_analyses = len([h for h in history if h["status"] == "completed"])
        recent_analyses = len([h for h in history if 
                              datetime.now().timestamp() - h["timestamp"] < 86400 * 7])  # 過去7日
        
        success_rate = (completed_analyses / total_analyses * 100) if total_analyses > 0 else 0
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                label="🔢 総分析数",
                value=total_analyses,
                help="これまでに実行された分析の総数"
            )
        
        with col2:
            st.metric(
                label="✅ 完了分析",
                value=completed_analyses,
                delta=f"{success_rate:.1f}% 成功率",
                help="正常完了した分析数と成功率"
            )
        
        with col3:
            st.metric(
                label="📅 今週の分析",
                value=recent_analyses,
                help="過去7日間に実行された分析数"
            )
        
        with col4:
            # 現在の実行状況
            is_running = SessionState.get("analysis_running", False)
            status = "🔄 実行中" if is_running else "⏸️ 待機中"
            color = "normal" if not is_running else "inverse"
            
            st.metric(
                label="🎯 実行状況",
                value=status,
                help="現在の分析実行状況"
            )
    
    def _render_quick_actions(self):
        """クイックアクション"""
        st.subheader("⚡ クイックアクション")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 🎯 人気銘柄分析")
            
            popular_tickers = [
                {"symbol": "SPY", "name": "S&P 500 ETF", "icon": "🇺🇸"},
                {"symbol": "QQQ", "name": "NASDAQ 100 ETF", "icon": "💻"},
                {"symbol": "AAPL", "name": "Apple Inc.", "icon": "🍎"},
                {"symbol": "MSFT", "name": "Microsoft Corp.", "icon": "💻"},
                {"symbol": "JP225", "name": "日経225", "icon": "🇯🇵"}
            ]
            
            for ticker_info in popular_tickers:
                col_icon, col_content, col_button = st.columns([1, 4, 2])
                
                with col_icon:
                    st.markdown(f"## {ticker_info['icon']}")
                
                with col_content:
                    st.markdown(f"**{ticker_info['symbol']}**")
                    st.caption(ticker_info['name'])
                
                with col_button:
                    if st.button(f"分析開始", key=f"dashboard_quick_analyze_{ticker_info['symbol']}", use_container_width=True):
                        SessionState.update({
                            "selected_ticker": ticker_info['symbol'],
                            "current_page": "settings"
                        })
                        st.rerun()
        
        with col2:
            st.markdown("### 🔧 分析プリセット")
            
            presets = [
                {
                    "name": "📈 テクニカル分析",
                    "description": "テクニカル指標とニュース分析",
                    "analysts": [AnalystType.MARKET, AnalystType.NEWS],
                    "depth": 3
                },
                {
                    "name": "📊 ファンダメンタル分析",
                    "description": "財務諸表とニュース分析",
                    "analysts": [AnalystType.FUNDAMENTALS, AnalystType.NEWS],
                    "depth": 4
                },
                {
                    "name": "🌐 総合分析",
                    "description": "全アナリストによる包括的分析",
                    "analysts": [AnalystType.MARKET, AnalystType.SOCIAL, AnalystType.NEWS, AnalystType.FUNDAMENTALS],
                    "depth": 5
                },
                {
                    "name": "⚡ クイック分析",
                    "description": "高速な基本分析",
                    "analysts": [AnalystType.MARKET, AnalystType.NEWS],
                    "depth": 1
                }
            ]
            
            for preset in presets:
                with st.container():
                    col_info, col_btn = st.columns([3, 1])
                    
                    with col_info:
                        st.markdown(f"**{preset['name']}**")
                        st.caption(preset['description'])
                        st.caption(f"深度: {preset['depth']}, アナリスト: {len(preset['analysts'])}名")
                    
                    with col_btn:
                        if st.button("設定", key=f"dashboard_preset_{preset['name']}", use_container_width=True):
                            SessionState.update({
                                "selected_analysts": preset['analysts'],
                                "research_depth": preset['depth'],
                                "current_page": "settings"
                            })
                            st.rerun()
                
                st.markdown("")
    
    def _render_recent_history(self):
        """最近の分析履歴"""
        st.subheader("📈 最近の分析履歴")
        
        history = self.cli_wrapper.get_analysis_history()
        
        if not history:
            st.info("📭 まだ分析履歴がありません。分析を開始してみましょう！")
            if st.button("🚀 最初の分析を開始", key="dashboard_first_analysis", type="primary"):
                SessionState.navigate_to("settings")
                st.rerun()
            return
        
        # 最新5件を表示
        recent_history = history[:5]
        
        for i, analysis in enumerate(recent_history):
            with st.container():
                col1, col2, col3, col4, col5 = st.columns([2, 2, 2, 2, 1])
                
                with col1:
                    # ステータスアイコン
                    status_icon = "✅" if analysis["status"] == "completed" else "⏳"
                    st.markdown(f"## {status_icon}")
                    
                with col2:
                    st.markdown(f"**{analysis['ticker']}**")
                    st.caption(f"ティッカー")
                
                with col3:
                    st.markdown(f"**{analysis['date']}**")
                    st.caption("分析日")
                
                with col4:
                    timestamp = datetime.fromtimestamp(analysis['timestamp'])
                    time_ago = self._time_ago(timestamp)
                    st.markdown(f"**{time_ago}**")
                    st.caption("実行時刻")
                
                with col5:
                    if st.button("表示", key=f"dashboard_view_analysis_{i}", use_container_width=True):
                        SessionState.update({
                            "selected_ticker": analysis['ticker'],
                            "selected_date": analysis['date'],
                            "current_page": "results"
                        })
                        st.rerun()
                
                # 詳細情報
                with st.expander(f"詳細: {analysis['ticker']} ({analysis['date']})", expanded=False):
                    col_details1, col_details2 = st.columns(2)
                    
                    with col_details1:
                        st.markdown(f"""
                        - **ステータス**: {analysis['status']}
                        - **レポート数**: {analysis['report_count']}
                        - **パス**: `{analysis['path']}`
                        """)
                    
                    with col_details2:
                        if analysis['status'] == 'completed':
                            if st.button(f"📊 結果を見る", key=f"dashboard_detailed_view_{i}"):
                                SessionState.update({
                                    "selected_ticker": analysis['ticker'],
                                    "selected_date": analysis['date'],
                                    "current_page": "results"
                                })
                                st.rerun()
                        else:
                            st.caption("分析が完了していません")
                
                st.markdown("---")
        
        # 全履歴表示ボタン
        if len(history) > 5:
            if st.button(f"📜 全履歴を表示 ({len(history)}件)", key="dashboard_show_all_history", use_container_width=True):
                SessionState.navigate_to("results")
                st.rerun()
    
    def _render_system_info(self):
        """システム情報"""
        st.subheader("🔧 システム情報")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 📦 環境状態")
            
            # 環境変数チェック
            import os
            required_vars = ["FINNHUB_API_KEY", "OPENAI_API_KEY"]
            
            for var in required_vars:
                if os.getenv(var):
                    st.success(f"✅ {var} - 設定済み")
                else:
                    st.error(f"❌ {var} - 未設定")
            
            # パス情報
            st.markdown("### 📁 パス情報")
            results_path = Path(project_root) / "results"
            st.markdown(f"- **プロジェクトルート**: `{project_root}`")
            st.markdown(f"- **結果保存先**: `{results_path}`")
            st.markdown(f"- **結果ディレクトリ存在**: {'✅' if results_path.exists() else '❌'}")
        
        with col2:
            st.markdown("### ⚙️ 現在の設定")
            
            st.markdown(f"""
            - **ティッカー**: {SessionState.get('selected_ticker', 'N/A')}
            - **分析日**: {SessionState.get('selected_date', 'N/A')}
            - **研究深度**: {SessionState.get('research_depth', 'N/A')}
            - **LLMプロバイダー**: {SessionState.get('llm_provider', 'N/A')}
            """)
            
            analysts = SessionState.get('selected_analysts', [])
            if analysts:
                analyst_names = [UIHelpers.format_analyst_name(a) for a in analysts]
                st.markdown(f"- **選択アナリスト**: {', '.join(analyst_names)}")
            else:
                st.markdown("- **選択アナリスト**: 未選択")
            
            # クイック設定変更ボタン
            if st.button("⚙️ 設定を変更", key="dashboard_change_settings", use_container_width=True):
                SessionState.navigate_to("settings")
                st.rerun()
    
    def _time_ago(self, timestamp: datetime) -> str:
        """相対時間を計算"""
        now = datetime.now()
        diff = now - timestamp
        
        if diff.days > 0:
            return f"{diff.days}日前"
        elif diff.seconds > 3600:
            hours = diff.seconds // 3600
            return f"{hours}時間前"
        elif diff.seconds > 60:
            minutes = diff.seconds // 60
            return f"{minutes}分前"
        else:
            return "たった今"
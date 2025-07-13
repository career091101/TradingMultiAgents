"""
結果表示コンポーネント
"""

import streamlit as st
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path
import re

import sys
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from webui.utils.state import SessionState, UIHelpers

class ResultsPage:
    """分析結果表示画面"""
    
    def __init__(self, cli_wrapper):
        self.cli_wrapper = cli_wrapper
    
    def render(self):
        """結果画面をレンダリング"""
        st.title("📊 分析結果")
        
        # 結果選択セクション
        self._render_result_selector()
        
        st.markdown("---")
        
        # 選択された結果の表示
        selected_ticker = SessionState.get("selected_ticker")
        selected_date = SessionState.get("selected_date")
        
        if selected_ticker and selected_date:
            self._render_analysis_results(selected_ticker, selected_date)
        else:
            self._render_no_selection()
    
    def _render_result_selector(self):
        """結果選択セクション"""
        st.subheader("🔍 結果選択")
        
        # 分析履歴を取得
        history = self.cli_wrapper.get_analysis_history()
        
        if not history:
            st.info("📭 まだ分析結果がありません")
            if st.button("🚀 分析を開始", key="results_start_analysis", type="primary"):
                SessionState.navigate_to("settings")
                st.rerun()
            return
        
        col1, col2, col3 = st.columns([2, 2, 1])
        
        with col1:
            # ティッカー選択
            tickers = sorted(list(set([h["ticker"] for h in history])))
            current_ticker = SessionState.get("selected_ticker", tickers[0] if tickers else "")
            
            selected_ticker = st.selectbox(
                "ティッカー",
                tickers,
                index=tickers.index(current_ticker) if current_ticker in tickers else 0,
                key="result_ticker_select"
            )
            SessionState.set("selected_ticker", selected_ticker)
        
        with col2:
            # 日付選択
            ticker_history = [h for h in history if h["ticker"] == selected_ticker]
            dates = sorted([h["date"] for h in ticker_history], reverse=True)
            
            current_date = SessionState.get("selected_date", dates[0] if dates else "")
            
            selected_date = st.selectbox(
                "分析日",
                dates,
                index=dates.index(current_date) if current_date in dates else 0,
                key="result_date_select"
            )
            SessionState.set("selected_date", selected_date)
        
        with col3:
            st.markdown("<br>", unsafe_allow_html=True)  # スペーサー
            if st.button("🔄 更新", key="results_refresh", use_container_width=True):
                st.rerun()
        
        # 選択された分析の詳細情報
        selected_analysis = next(
            (h for h in history if h["ticker"] == selected_ticker and h["date"] == selected_date),
            None
        )
        
        if selected_analysis:
            col_info1, col_info2, col_info3, col_info4 = st.columns(4)
            
            with col_info1:
                status_color = "🟢" if selected_analysis["status"] == "completed" else "🔄"
                st.metric("ステータス", f"{status_color} {selected_analysis['status']}")
            
            with col_info2:
                st.metric("レポート数", selected_analysis["report_count"])
            
            with col_info3:
                timestamp = datetime.fromtimestamp(selected_analysis["timestamp"])
                st.metric("実行時刻", timestamp.strftime("%H:%M"))
            
            with col_info4:
                if st.button("📂 フォルダを開く", key="results_open_folder", use_container_width=True):
                    st.info(f"パス: {selected_analysis['path']}")
    
    def _render_analysis_results(self, ticker: str, date: str):
        """分析結果を表示"""
        # 結果データを取得
        results = self.cli_wrapper.get_analysis_results(ticker, date)
        
        if "error" in results:
            st.error(f"❌ {results['error']}")
            return
        
        reports = results.get("reports", {})
        
        if not reports:
            st.warning("⚠️ レポートが見つかりません")
            return
        
        # タブで結果を整理
        self._render_result_tabs(reports, results, ticker, date)
    
    def _render_result_tabs(self, reports: Dict[str, str], results: Dict[str, Any], ticker: str, date: str):
        """結果をタブ形式で表示"""
        # レポートの順序定義
        report_order = [
            ("final_trade_decision", "🎯 最終投資判断", "最終的な投資判断と推奨事項"),
            ("trader_investment_plan", "💼 トレーダー計画", "具体的な取引戦略"),
            ("investment_plan", "📈 投資計画", "リサーチチームの投資提案"),
            ("market_report", "📊 市場分析", "テクニカル指標とチャート分析"),
            ("fundamentals_report", "💰 ファンダメンタル", "財務諸表と企業分析"),
            ("news_report", "📰 ニュース分析", "最新ニュースと市場動向"),
            ("sentiment_report", "💬 センチメント", "ソーシャルメディア分析")
        ]
        
        # 利用可能なレポートのタブのみ作成
        available_tabs = []
        tab_contents = []
        
        for report_key, tab_name, description in report_order:
            if report_key in reports:
                available_tabs.append(tab_name)
                tab_contents.append((report_key, reports[report_key], description))
        
        if not available_tabs:
            st.warning("表示可能なレポートがありません")
            st.info(f"利用可能なレポートキー: {list(reports.keys())}")
            return
        
        # デバッグ情報
        st.info(f"利用可能なタブ: {available_tabs}")
        st.info(f"レポート数: {len(tab_contents)}")
        
        # サマリーダッシュボードタブを追加
        all_tab_names = ["📋 サマリー"] + available_tabs + ["📝 実行ログ"]
        
        try:
            # タブを作成
            tabs = st.tabs(all_tab_names)
            
            # サマリータブ
            with tabs[0]:
                self._render_summary_dashboard(reports, results)
            
            # 各レポートタブ
            for i, (report_key, content, description) in enumerate(tab_contents):
                with tabs[i + 1]:
                    self._render_report_content(report_key, content, description)
            
            # 実行ログタブ
            with tabs[-1]:
                self._render_execution_log(results.get("log", ""))
                
        except Exception as e:
            st.error(f"タブ表示エラー: {e}")
            # フォールバック: タブなしで順次表示
            st.subheader("📋 分析サマリー")
            self._render_summary_dashboard(reports, results)
            
            for report_key, content, description in tab_contents:
                st.markdown("---")
                # レポート名を取得
                report_name = next((name for key, name, desc in report_order if key == report_key), report_key)
                st.subheader(report_name)
                self._render_report_content(report_key, content, description)
            
            st.markdown("---")
            st.subheader("📝 実行ログ")
            self._render_execution_log(results.get("log", ""))
    
    def _render_summary_dashboard(self, reports: Dict[str, str], results: Dict[str, Any]):
        """サマリーダッシュボード"""
        st.subheader("📋 分析サマリー")
        
        # 基本情報
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("ティッカー", results["ticker"])
            st.metric("分析日", results["date"])
        
        with col2:
            st.metric("レポート数", len(reports))
            
            # 最終判断を抽出
            final_decision = self._extract_final_recommendation(reports)
            if final_decision:
                st.metric("最終判断", final_decision["action"])
        
        with col3:
            # 分析完了度
            expected_reports = 7
            completion_rate = len(reports) / expected_reports * 100
            st.metric("完了度", f"{completion_rate:.0f}%")
        
        st.markdown("---")
        
        # キーポイント抽出
        self._render_key_insights(reports)
        
        st.markdown("---")
        
        # アクション推奨事項
        if final_decision:
            self._render_action_recommendations(final_decision, reports)
    
    def _render_key_insights(self, reports: Dict[str, str]):
        """キーポイント抽出"""
        st.subheader("🔍 主要ポイント")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 📈 ポジティブ要因")
            positive_points = self._extract_positive_points(reports)
            for point in positive_points[:5]:  # 上位5つ
                st.markdown(f"• {point}")
        
        with col2:
            st.markdown("### 📉 リスク要因")
            risk_points = self._extract_risk_points(reports)
            for point in risk_points[:5]:  # 上位5つ
                st.markdown(f"• {point}")
    
    def _render_action_recommendations(self, final_decision: Dict[str, str], reports: Dict[str, str]):
        """アクション推奨事項"""
        st.subheader("🎯 推奨アクション")
        
        action = final_decision.get("action", "HOLD")
        confidence = final_decision.get("confidence", "不明")
        reasoning = final_decision.get("reasoning", "")
        
        # アクションに応じた色分け
        if action.upper() == "BUY":
            st.success(f"🟢 **{action}** (信頼度: {confidence})")
        elif action.upper() == "SELL":
            st.error(f"🔴 **{action}** (信頼度: {confidence})")
        else:
            st.info(f"🟡 **{action}** (信頼度: {confidence})")
        
        if reasoning:
            st.markdown(f"**判断理由**: {reasoning}")
        
        # 追加の推奨事項
        recommendations = self._extract_recommendations(reports)
        if recommendations:
            st.markdown("### 📋 追加推奨事項")
            for rec in recommendations:
                st.markdown(f"• {rec}")
    
    def _render_report_content(self, report_key: str, content: str, description: str):
        """個別レポート表示"""
        st.markdown(f"*{description}*")
        st.markdown("---")
        
        # レポート表示オプション
        col1, col2 = st.columns([3, 1])
        
        with col1:
            pass  # メインコンテンツ用
        
        with col2:
            # 表示オプション
            show_raw = st.checkbox("Raw Markdown表示", key=f"raw_{report_key}")
            
            if st.button("📋 コピー", key=f"results_copy_{report_key}", use_container_width=True):
                st.text_area("コピー用", content, height=100, key=f"copy_area_{report_key}")
        
        # コンテンツ表示
        if show_raw:
            st.text_area("Raw Content", content, height=600, key=f"raw_content_{report_key}")
        else:
            # Markdownとして表示
            try:
                st.markdown(content)
            except Exception as e:
                st.error(f"表示エラー: {e}")
                st.text(content)
    
    def _render_execution_log(self, log_content: str):
        """実行ログ表示"""
        if not log_content:
            st.info("実行ログがありません")
            return
        
        st.subheader("📝 実行ログ")
        
        # ログ表示オプション
        col1, col2, col3 = st.columns(3)
        
        with col1:
            show_lines = st.selectbox("表示行数", [50, 100, 500, "全て"], index=1)
        
        with col2:
            filter_text = st.text_input("フィルター", placeholder="検索テキスト")
        
        with col3:
            if st.button("📋 ログをコピー", key="results_copy_log", use_container_width=True):
                st.text_area("ログコピー用", log_content, height=200)
        
        # ログ処理
        log_lines = log_content.split('\n')
        
        # フィルタリング
        if filter_text:
            log_lines = [line for line in log_lines if filter_text.lower() in line.lower()]
        
        # 行数制限
        if show_lines != "全て":
            log_lines = log_lines[-int(show_lines):]
        
        # ログ表示
        log_text = '\n'.join(log_lines)
        st.text_area("実行ログ", log_text, height=500, key="execution_log_display")
    
    def _render_no_selection(self):
        """選択なし時の表示"""
        st.info("📋 分析結果を選択してください")
        
        # 最近の分析履歴を表示
        history = self.cli_wrapper.get_analysis_history()[:5]
        
        if history:
            st.subheader("🕒 最近の分析")
            
            for analysis in history:
                col1, col2, col3, col4 = st.columns([2, 2, 2, 1])
                
                with col1:
                    st.markdown(f"**{analysis['ticker']}**")
                
                with col2:
                    st.markdown(f"**{analysis['date']}**")
                
                with col3:
                    status_icon = "✅" if analysis["status"] == "completed" else "⏳"
                    st.markdown(f"{status_icon} {analysis['status']}")
                
                with col4:
                    if st.button("表示", key=f"results_quick_view_{analysis['ticker']}_{analysis['date']}", use_container_width=True):
                        SessionState.update({
                            "selected_ticker": analysis['ticker'],
                            "selected_date": analysis['date']
                        })
                        st.rerun()
        else:
            st.markdown("まだ分析結果がありません")
            if st.button("🚀 分析を開始", key="results_start_analysis_no_selection", type="primary"):
                SessionState.navigate_to("settings")
                st.rerun()
    
    def _extract_final_recommendation(self, reports: Dict[str, str]) -> Optional[Dict[str, str]]:
        """最終推奨事項を抽出"""
        final_report = reports.get("final_trade_decision", "")
        
        if not final_report:
            return None
        
        # 簡単なパターンマッチング
        action_patterns = {
            r'BUY|買い|購入|ロング': 'BUY',
            r'SELL|売り|ショート': 'SELL',
            r'HOLD|保持|様子見': 'HOLD'
        }
        
        action = "HOLD"  # デフォルト
        for pattern, act in action_patterns.items():
            if re.search(pattern, final_report, re.IGNORECASE):
                action = act
                break
        
        return {
            "action": action,
            "confidence": "中程度",  # 実際の分析が必要
            "reasoning": final_report[:200] + "..." if len(final_report) > 200 else final_report
        }
    
    def _extract_positive_points(self, reports: Dict[str, str]) -> List[str]:
        """ポジティブ要因を抽出"""
        positive_keywords = [
            "上昇", "強気", "好調", "改善", "増加", "プラス", "良好", 
            "上向き", "回復", "成長", "利益", "positive", "bullish", "strong"
        ]
        
        points = []
        for report_content in reports.values():
            lines = report_content.split('\n')
            for line in lines:
                if any(keyword in line.lower() for keyword in positive_keywords):
                    clean_line = line.strip('- *#').strip()
                    if clean_line and len(clean_line) > 10:
                        points.append(clean_line[:100])
        
        return list(set(points))[:10]  # 重複除去して上位10個
    
    def _extract_risk_points(self, reports: Dict[str, str]) -> List[str]:
        """リスク要因を抽出"""
        risk_keywords = [
            "下落", "弱気", "悪化", "減少", "マイナス", "リスク", "懸念",
            "下向き", "低下", "損失", "negative", "bearish", "weak", "risk"
        ]
        
        points = []
        for report_content in reports.values():
            lines = report_content.split('\n')
            for line in lines:
                if any(keyword in line.lower() for keyword in risk_keywords):
                    clean_line = line.strip('- *#').strip()
                    if clean_line and len(clean_line) > 10:
                        points.append(clean_line[:100])
        
        return list(set(points))[:10]  # 重複除去して上位10個
    
    def _extract_recommendations(self, reports: Dict[str, str]) -> List[str]:
        """推奨事項を抽出"""
        rec_keywords = [
            "推奨", "提案", "検討", "おすすめ", "suggest", "recommend", "consider"
        ]
        
        recommendations = []
        for report_content in reports.values():
            lines = report_content.split('\n')
            for line in lines:
                if any(keyword in line.lower() for keyword in rec_keywords):
                    clean_line = line.strip('- *#').strip()
                    if clean_line and len(clean_line) > 10:
                        recommendations.append(clean_line[:150])
        
        return list(set(recommendations))[:5]  # 重複除去して上位5個
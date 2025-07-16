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
from webui.utils.pdf_generator import PDFReportGenerator

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
        # レポートの順序定義 - 実際に生成されるファイルに基づいて更新
        report_order = [
            # 最終判断レポート
            ("final_trade_decision", "🎯 最終投資判断", "ポートフォリオマネージャーによる最終判断とリスク管理チームの議論"),
            ("trader_investment_plan", "💼 トレーダー計画", "トレーダーによる具体的な取引戦略と執行計画"),
            
            # リサーチチームレポート
            ("investment_plan", "📈 投資計画", "研究マネージャーの総括とBull/Bear研究者の議論結果"),
            
            # アナリストレポート（基礎分析）
            ("market_report", "📊 市場分析", "マーケットアナリストによるテクニカル指標とチャート分析"),
            ("fundamentals_report", "💰 ファンダメンタル", "ファンダメンタルアナリストによる財務諸表と企業分析"),
            ("news_report", "📰 ニュース分析", "ニュースアナリストによる最新ニュースと市場動向"),
            ("sentiment_report", "💬 センチメント", "ソーシャルアナリストによるソーシャルメディア分析"),
            
            # 追加の詳細タブ（レポート内から抽出）
            ("debate_transcript", "🗣️ 議論記録", "Bull/Bear研究者間の詳細な議論内容"),
            ("risk_discussion", "⚖️ リスク議論", "リスク管理チーム（積極派/保守派/中立派）の議論"),
            ("technical_indicators", "📈 テクニカル詳細", "詳細なテクニカル指標とチャートパターン"),
            ("key_metrics", "📊 主要指標", "財務指標、リスク指標、パフォーマンス指標の要約"),
            ("action_items", "✅ アクション項目", "推奨される具体的なアクションと実行タイミング")
        ]
        
        # 既存レポートから追加の詳細情報を抽出
        extracted_reports = self._extract_detailed_reports(reports)
        
        # すべてのレポート（既存 + 抽出）を統合
        all_reports = {**reports, **extracted_reports}
        
        # 利用可能なレポートのタブのみ作成
        available_tabs = []
        tab_contents = []
        
        for report_key, tab_name, description in report_order:
            if report_key in all_reports:
                available_tabs.append(tab_name)
                tab_contents.append((report_key, all_reports[report_key], description))
        
        if not available_tabs:
            st.warning("表示可能なレポートがありません")
            st.info(f"利用可能なレポートキー: {list(reports.keys())}")
            return
        
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
        
        # PDF出力ボタン
        col_pdf = st.columns([3, 1])
        with col_pdf[1]:
            if st.button("📄 PDFで出力", key="results_export_pdf", use_container_width=True, type="primary"):
                self._export_to_pdf(reports, results)
        
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
        
        # ポイント数に応じて列の幅を調整
        positive_points = self._extract_positive_points(reports)
        risk_points = self._extract_risk_points(reports)
        max_points = max(len(positive_points), len(risk_points))
        
        # 項目数が多い場合は列幅を広げる
        if max_points > 8:
            col1, col2 = st.columns([1, 1], gap="large")
        else:
            col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 📈 ポジティブ要因")
            
            # 全件表示（最大12個まで）
            if positive_points:
                for i, point in enumerate(positive_points, 1):
                    st.markdown(f"{i}. {point}")
            else:
                st.info("ポジティブ要因が見つかりませんでした")
        
        with col2:
            st.markdown("### 📉 リスク要因")
            
            # 全件表示（最大12個まで）
            if risk_points:
                for i, point in enumerate(risk_points, 1):
                    st.markdown(f"{i}. {point}")
            else:
                st.info("リスク要因が見つかりませんでした")
    
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
            for i, rec in enumerate(recommendations, 1):
                st.markdown(f"{i}. {rec}")
    
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
        confidence = "中程度"
        
        for pattern, act in action_patterns.items():
            if re.search(pattern, final_report, re.IGNORECASE):
                action = act
                break
        
        # 信頼度の抽出
        if "強く" in final_report or "高い信頼" in final_report:
            confidence = "高"
        elif "低い" in final_report or "慎重" in final_report:
            confidence = "低"
        
        # 判断理由の抽出（重要な部分を優先）
        reasoning = final_report
        if len(final_report) > 800:
            # 「最終判断」や「結論」の部分を探す
            conclusion_keywords = ["最終判断", "結論", "総合評価", "判断理由", "推奨理由"]
            for keyword in conclusion_keywords:
                if keyword in final_report:
                    start_idx = final_report.find(keyword)
                    reasoning = final_report[start_idx:start_idx + 800]
                    break
            else:
                # キーワードが見つからない場合は最初から800文字
                reasoning = final_report[:800] + "..."
        
        return {
            "action": action,
            "confidence": confidence,
            "reasoning": reasoning
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
                        # 文の長さに応じて適切に切り詰める
                        if len(clean_line) <= 250:
                            points.append(clean_line)  # 250文字以下はそのまま
                        else:
                            # 長い文は句読点で切る
                            cutoff_point = clean_line[:250].rfind('。')
                            if cutoff_point > 200:
                                points.append(clean_line[:cutoff_point + 1])
                            else:
                                points.append(clean_line[:250] + "...")
        
        # 重複除去して、長さで並び替え（短い順）して返す
        unique_points = list(set(points))
        unique_points.sort(key=len)
        return unique_points[:12]  # 最大12個まで表示
    
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
                        # 文の長さに応じて適切に切り詰める
                        if len(clean_line) <= 250:
                            points.append(clean_line)  # 250文字以下はそのまま
                        else:
                            # 長い文は句読点で切る
                            cutoff_point = clean_line[:250].rfind('。')
                            if cutoff_point > 200:
                                points.append(clean_line[:cutoff_point + 1])
                            else:
                                points.append(clean_line[:250] + "...")
        
        # 重複除去して、長さで並び替え（短い順）して返す
        unique_points = list(set(points))
        unique_points.sort(key=len)
        return unique_points[:12]  # 最大12個まで表示
    
    def _extract_recommendations(self, reports: Dict[str, str]) -> List[str]:
        """推奨事項を抽出"""
        rec_keywords = [
            "推奨", "提案", "検討", "おすすめ", "suggest", "recommend", "consider"
        ]
        
        priority_keywords = ["緊急", "重要", "必須", "immediate", "urgent", "critical", "must"]
        action_keywords = ["実行", "行う", "する", "べき", "必要", "should", "need"]
        
        priority_recommendations = []  # 優先度の高い推奨事項
        action_recommendations = []    # 具体的なアクション
        general_recommendations = []   # 一般的な推奨事項
        
        for report_content in reports.values():
            lines = report_content.split('\n')
            for line in lines:
                if any(keyword in line.lower() for keyword in rec_keywords):
                    clean_line = line.strip('- *#').strip()
                    if clean_line and len(clean_line) > 10:
                        # 文の処理
                        if len(clean_line) <= 350:
                            processed_line = clean_line
                        else:
                            cutoff_point = clean_line[:350].rfind('。')
                            if cutoff_point > 300:
                                processed_line = clean_line[:cutoff_point + 1]
                            else:
                                processed_line = clean_line[:350] + "..."
                        
                        # 優先度による分類
                        if any(keyword in line.lower() for keyword in priority_keywords):
                            priority_recommendations.append(f"🔴 {processed_line}")
                        elif any(keyword in line.lower() for keyword in action_keywords):
                            action_recommendations.append(f"🟡 {processed_line}")
                        else:
                            general_recommendations.append(processed_line)
        
        # 重複除去して統合（優先度順）
        all_recommendations = []
        all_recommendations.extend(list(set(priority_recommendations))[:3])  # 優先度高は最大3個
        all_recommendations.extend(list(set(action_recommendations))[:3])    # アクションは最大3個
        all_recommendations.extend(list(set(general_recommendations))[:2])   # 一般は最大2個
        
        return all_recommendations[:8]  # 合計最大8個まで
    
    def _export_to_pdf(self, reports: Dict[str, str], results: Dict[str, Any]):
        """PDFエクスポート機能"""
        try:
            # PDFデータの準備
            pdf_data = self._prepare_pdf_data(reports, results)
            
            # PDF生成
            pdf_generator = PDFReportGenerator()
            pdf_bytes = pdf_generator.generate_report(pdf_data)
            
            # ダウンロードボタン
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"TradingAgents_Report_{results['ticker']}_{results['date']}_{timestamp}.pdf"
            
            st.download_button(
                label="📥 PDFをダウンロード",
                data=pdf_bytes,
                file_name=filename,
                mime="application/pdf",
                key="download_pdf_report"
            )
            
            st.success("✅ PDFレポートを生成しました")
            
        except Exception as e:
            st.error(f"❌ PDF生成エラー: {e}")
            st.exception(e)
    
    def _prepare_pdf_data(self, reports: Dict[str, str], results: Dict[str, Any]) -> Dict[str, Any]:
        """PDF用データの準備"""
        # 最終判断を抽出
        final_decision = self._extract_final_recommendation(reports)
        
        # 詳細レポートを抽出
        extracted_reports = self._extract_detailed_reports(reports)
        
        # サマリーの生成
        summary = self._generate_summary(reports, final_decision)
        
        # PDFデータ構造の作成
        pdf_data = {
            "ticker": results.get("ticker", "N/A"),
            "analysis_date": results.get("date", "N/A"),
            "research_depth": SessionState.get("research_depth", 3),
            "llm_provider": SessionState.get("llm_provider", "openai"),
            "shallow_model": SessionState.get("shallow_thinker", "gpt-4o-mini"),
            "deep_model": SessionState.get("deep_thinker", "o4-mini-2025-04-16"),
            
            # サマリー
            "summary": summary,
            
            # 最終投資判断
            "final_decision": final_decision.get("action", "HOLD") if final_decision else "N/A",
            
            # 各レポート内容
            "trader_plan": reports.get("trader_investment_plan", ""),
            "investment_plan": reports.get("investment_plan", ""),
            "market_analysis": reports.get("market_report", ""),
            "fundamental_analysis": reports.get("fundamentals_report", ""),
            "news_analysis": reports.get("news_report", ""),
            "sentiment_analysis": reports.get("sentiment_report", ""),
            
            # 追加の詳細レポート（抽出されたもの）
            "debate_transcript": extracted_reports.get("debate_transcript", ""),
            "risk_discussion": extracted_reports.get("risk_discussion", ""),
            "key_metrics": extracted_reports.get("key_metrics", ""),
            "action_items": extracted_reports.get("action_items", "")
        }
        
        return pdf_data
    
    def _generate_summary(self, reports: Dict[str, str], final_decision: Optional[Dict[str, str]]) -> str:
        """サマリーの生成"""
        summary_parts = []
        
        # 最終判断
        if final_decision:
            summary_parts.append(f"最終投資判断: {final_decision['action']}")
            if final_decision.get("confidence"):
                summary_parts.append(f"信頼度: {final_decision['confidence']}")
        
        # 主要ポジティブ要因
        positive_points = self._extract_positive_points(reports)
        if positive_points:
            summary_parts.append("\n主要ポジティブ要因:")
            # サマリーでは5個まで表示（画面表示と同じ基準）
            for i, point in enumerate(positive_points[:5], 1):
                summary_parts.append(f"{i}. {point}")
        
        # 主要リスク要因
        risk_points = self._extract_risk_points(reports)
        if risk_points:
            summary_parts.append("\n主要リスク要因:")
            # サマリーでは5個まで表示（画面表示と同じ基準）
            for i, point in enumerate(risk_points[:5], 1):
                summary_parts.append(f"{i}. {point}")
        
        return "\n".join(summary_parts)
    
    def _extract_detailed_reports(self, reports: Dict[str, str]) -> Dict[str, str]:
        """既存レポートから詳細情報を抽出して新しいレポートを生成"""
        extracted = {}
        
        # 1. Bull/Bear議論の抽出
        if "investment_plan" in reports:
            debate_content = self._extract_debate_content(reports["investment_plan"])
            if debate_content:
                extracted["debate_transcript"] = debate_content
        
        # 2. リスク管理議論の抽出
        if "final_trade_decision" in reports:
            risk_discussion = self._extract_risk_discussion(reports["final_trade_decision"])
            if risk_discussion:
                extracted["risk_discussion"] = risk_discussion
        
        # 3. テクニカル指標詳細の抽出
        if "market_report" in reports:
            technical_details = self._extract_technical_details(reports["market_report"])
            if technical_details:
                extracted["technical_indicators"] = technical_details
        
        # 4. 主要指標の集約
        key_metrics = self._aggregate_key_metrics(reports)
        if key_metrics:
            extracted["key_metrics"] = key_metrics
        
        # 5. アクション項目の抽出
        action_items = self._extract_action_items(reports)
        if action_items:
            extracted["action_items"] = action_items
        
        return extracted
    
    def _extract_debate_content(self, investment_plan: str) -> Optional[str]:
        """投資計画からBull/Bear議論を抽出"""
        lines = investment_plan.split('\n')
        debate_sections = []
        in_debate = False
        
        for i, line in enumerate(lines):
            # 議論セクションの開始を検出
            if any(keyword in line.lower() for keyword in ['bull', 'bear', '議論', 'debate', 'discussion']):
                in_debate = True
            
            if in_debate:
                # Bull研究者の発言を抽出
                if 'bull' in line.lower() and ':' in line:
                    debate_sections.append(f"\n### 🐂 Bull研究者の見解\n{line}")
                    # 次の数行も含める
                    for j in range(i+1, min(i+10, len(lines))):
                        if lines[j].strip() and not any(k in lines[j].lower() for k in ['bear', '###', '##']):
                            debate_sections.append(lines[j])
                        else:
                            break
                
                # Bear研究者の発言を抽出
                elif 'bear' in line.lower() and ':' in line:
                    debate_sections.append(f"\n### 🐻 Bear研究者の見解\n{line}")
                    # 次の数行も含める
                    for j in range(i+1, min(i+10, len(lines))):
                        if lines[j].strip() and not any(k in lines[j].lower() for k in ['bull', '###', '##']):
                            debate_sections.append(lines[j])
                        else:
                            break
        
        if debate_sections:
            return "# Bull vs Bear 研究者の議論内容\n\n" + "\n".join(debate_sections)
        return None
    
    def _extract_risk_discussion(self, final_decision: str) -> Optional[str]:
        """最終決定からリスク管理チームの議論を抽出"""
        lines = final_decision.split('\n')
        risk_sections = []
        
        risk_keywords = ['aggressive', 'conservative', 'neutral', 'リスク', 'risk management', '積極派', '保守派', '中立派']
        
        for i, line in enumerate(lines):
            if any(keyword in line.lower() for keyword in risk_keywords):
                # セクションタイトルを特定
                if 'aggressive' in line.lower() or '積極派' in line:
                    risk_sections.append(f"\n### 🚀 積極派アナリストの見解\n")
                elif 'conservative' in line.lower() or '保守派' in line:
                    risk_sections.append(f"\n### 🛡️ 保守派アナリストの見解\n")
                elif 'neutral' in line.lower() or '中立派' in line:
                    risk_sections.append(f"\n### ⚖️ 中立派アナリストの見解\n")
                
                # 内容を抽出
                for j in range(i, min(i+15, len(lines))):
                    if lines[j].strip():
                        risk_sections.append(lines[j])
                    if j > i and any(k in lines[j].lower() for k in ['###', '##', '---']):
                        break
        
        if risk_sections:
            return "# リスク管理チームの議論\n\n" + "\n".join(risk_sections)
        return None
    
    def _extract_technical_details(self, market_report: str) -> Optional[str]:
        """市場レポートから詳細なテクニカル指標を抽出"""
        lines = market_report.split('\n')
        technical_sections = []
        
        # テクニカル指標のキーワード
        tech_keywords = ['rsi', 'macd', 'bollinger', 'sma', 'ema', 'volume', 'support', 'resistance', 
                        'trend', 'pattern', 'fibonacci', 'indicator', '指標', 'チャート']
        
        for i, line in enumerate(lines):
            if any(keyword in line.lower() for keyword in tech_keywords):
                technical_sections.append(line)
                # 数値データや詳細説明を含む次の行も追加
                for j in range(i+1, min(i+5, len(lines))):
                    if lines[j].strip() and (any(char.isdigit() for char in lines[j]) or '.' in lines[j]):
                        technical_sections.append(lines[j])
        
        if technical_sections:
            return "# 詳細なテクニカル分析\n\n" + "\n".join(technical_sections)
        return None
    
    def _aggregate_key_metrics(self, reports: Dict[str, str]) -> Optional[str]:
        """全レポートから主要指標を集約"""
        metrics = []
        
        # 財務指標の抽出
        if "fundamentals_report" in reports:
            financial_metrics = self._extract_financial_metrics(reports["fundamentals_report"])
            if financial_metrics:
                metrics.append("## 📊 財務指標\n" + financial_metrics)
        
        # 市場指標の抽出
        if "market_report" in reports:
            market_metrics = self._extract_market_metrics(reports["market_report"])
            if market_metrics:
                metrics.append("\n## 📈 市場指標\n" + market_metrics)
        
        # センチメント指標の抽出
        if "sentiment_report" in reports:
            sentiment_metrics = self._extract_sentiment_metrics(reports["sentiment_report"])
            if sentiment_metrics:
                metrics.append("\n## 💬 センチメント指標\n" + sentiment_metrics)
        
        if metrics:
            return "# 主要指標サマリー\n\n" + "\n".join(metrics)
        return None
    
    def _extract_financial_metrics(self, report: str) -> str:
        """財務指標を抽出"""
        metrics = []
        keywords = ['p/e', 'eps', 'revenue', '売上', '利益', 'margin', 'ratio', 'growth']
        
        lines = report.split('\n')
        for line in lines:
            if any(keyword in line.lower() for keyword in keywords) and any(char.isdigit() for char in line):
                metrics.append(f"- {line.strip()}")
        
        return "\n".join(metrics[:10])  # 上位10個まで
    
    def _extract_market_metrics(self, report: str) -> str:
        """市場指標を抽出"""
        metrics = []
        keywords = ['price', 'volume', 'volatility', 'beta', 'correlation', '価格', '出来高']
        
        lines = report.split('\n')
        for line in lines:
            if any(keyword in line.lower() for keyword in keywords) and any(char.isdigit() for char in line):
                metrics.append(f"- {line.strip()}")
        
        return "\n".join(metrics[:10])
    
    def _extract_sentiment_metrics(self, report: str) -> str:
        """センチメント指標を抽出"""
        metrics = []
        keywords = ['sentiment', 'score', 'positive', 'negative', 'neutral', 'mention', 'trend']
        
        lines = report.split('\n')
        for line in lines:
            if any(keyword in line.lower() for keyword in keywords) and (':' in line or any(char.isdigit() for char in line)):
                metrics.append(f"- {line.strip()}")
        
        return "\n".join(metrics[:10])
    
    def _extract_action_items(self, reports: Dict[str, str]) -> Optional[str]:
        """全レポートから具体的なアクション項目を抽出"""
        action_items = []
        action_keywords = ['recommend', 'suggest', 'should', 'must', 'action', 'next step', 
                          '推奨', '提案', 'べき', '必要', 'アクション']
        
        priority_items = []  # 優先度の高いアイテム
        regular_items = []   # 通常のアイテム
        
        for report_name, content in reports.items():
            lines = content.split('\n')
            for line in lines:
                if any(keyword in line.lower() for keyword in action_keywords):
                    # 優先度の判定
                    if any(urgent in line.lower() for urgent in ['immediate', 'urgent', 'critical', '緊急', '重要']):
                        priority_items.append(f"🔴 {line.strip()}")
                    else:
                        regular_items.append(f"🔵 {line.strip()}")
        
        if priority_items or regular_items:
            result = "# 推奨アクション項目\n\n"
            
            if priority_items:
                result += "## 🚨 優先アクション\n" + "\n".join(priority_items[:5]) + "\n\n"
            
            if regular_items:
                result += "## 📋 通常アクション\n" + "\n".join(regular_items[:10])
            
            return result
        
        return None
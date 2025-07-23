"""
実行ログページコンポーネント
"""

import streamlit as st
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import asyncio
from pathlib import Path
import time
import logging

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from webui.utils.state import SessionState
from webui.utils.log_parser import LogParser, LogEntry, LogLevel, LogStatistics, JapaneseLogParser
from webui.utils.log_streamer import get_session_manager

logger = logging.getLogger(__name__)

class LogsPage:
    """実行ログページ"""
    
    def __init__(self):
        self.session_manager = get_session_manager()
        # デフォルトで日本語パーサーを使用
        self.parser = JapaneseLogParser(translate=True)
        self._init_session_state()
    
    def _init_session_state(self):
        """セッション状態の初期化"""
        if "log_filters" not in st.session_state:
            st.session_state.log_filters = {
                "levels": ["INFO", "WARNING", "ERROR", "CRITICAL"],
                "agents": [],
                "search_text": "",
                "auto_scroll": True,
                "time_range": "all"
            }
        
        if "selected_log_session" not in st.session_state:
            st.session_state.selected_log_session = None
        
        if "log_entries" not in st.session_state:
            st.session_state.log_entries = []
        
        # 言語設定を常に日本語に設定（ユーザー設定を優先）
        if "log_language" not in st.session_state:
            st.session_state.log_language = "ja"  # デフォルトは日本語
        
        # パーサーが日本語設定と一致しているか確認
        if hasattr(self, 'parser'):
            current_translate = getattr(self.parser, 'translate', False)
            should_translate = st.session_state.log_language == "ja"
            if current_translate != should_translate:
                self.parser = JapaneseLogParser(translate=should_translate)
    
    def render(self):
        """ログページをレンダリング"""
        st.title("🔍 実行ログ")
        st.markdown("分析の詳細なログを確認できます")
        
        # ログセッション選択
        self._render_session_selector()
        
        if not st.session_state.selected_log_session:
            st.info("ログセッションを選択してください")
            return
        
        # メインコンテンツ
        col1, col2 = st.columns([1, 4])
        
        with col1:
            self._render_filters()
        
        with col2:
            self._render_log_viewer()
        
        # 統計情報
        self._render_statistics()
    
    def _render_session_selector(self):
        """ログセッション選択UI"""
        sessions = self.session_manager.get_log_sessions()
        
        if not sessions:
            st.warning("ログセッションが見つかりません")
            return
        
        # セッション選択と言語設定
        col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
        
        with col1:
            # セッションリスト
            session_options = []
            session_map = {}
            
            for session in sessions:
                label = f"{session['ticker']} - {session['date']} {session['time']}"
                if session['is_active']:
                    label += " 🔴 (実行中)"
                session_options.append(label)
                session_map[label] = session['session_id']
            
            selected_label = st.selectbox(
                "ログセッション",
                session_options,
                help="表示するログセッションを選択"
            )
            
            if selected_label:
                st.session_state.selected_log_session = session_map[selected_label]
        
        with col2:
            # リフレッシュボタン
            if st.button("🔄 更新", use_container_width=True):
                st.rerun()
        
        with col3:
            # エクスポートボタン
            if st.button("📥 エクスポート", use_container_width=True):
                self._show_export_dialog()
        
        with col4:
            # 言語切り替え
            current_lang = st.session_state.get("log_language", "ja")
            language = st.selectbox(
                "言語",
                ["ja", "en"],
                format_func=lambda x: "🇯🇵 日本語" if x == "ja" else "🇺🇸 English",
                index=0 if current_lang == "ja" else 1,
                key="log_language_selector"
            )
            
            # 言語が変更された場合
            if language != current_lang:
                st.session_state.log_language = language
                # パーサーを再作成（日本語選択時は翻訳を有効化）
                self.parser = JapaneseLogParser(translate=(language == "ja"))
                # 即座に再実行して変更を反映
                st.rerun()
    
    def _render_filters(self):
        """フィルター設定UI"""
        st.subheader("フィルター")
        
        # ログレベルフィルター
        st.markdown("**ログレベル**")
        levels = ["TRACE", "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        selected_levels = []
        
        for level in levels:
            level_enum = LogLevel.from_string(level)
            icon = level_enum.get_icon()
            
            if st.checkbox(f"{icon} {level}", 
                          value=level in st.session_state.log_filters["levels"],
                          key=f"level_{level}"):
                selected_levels.append(level)
        
        st.session_state.log_filters["levels"] = selected_levels
        
        st.markdown("---")
        
        # エージェントフィルター
        st.markdown("**エージェント**")
        
        # 現在のログからエージェントリストを取得
        agents = self._get_available_agents()
        
        if st.checkbox("全て選択", value=len(st.session_state.log_filters["agents"]) == 0):
            st.session_state.log_filters["agents"] = []
        else:
            selected_agents = st.multiselect(
                "エージェント選択",
                agents,
                default=st.session_state.log_filters["agents"],
                label_visibility="collapsed"
            )
            st.session_state.log_filters["agents"] = selected_agents
        
        st.markdown("---")
        
        # 検索
        st.markdown("**検索**")
        search_text = st.text_input(
            "テキスト検索",
            value=st.session_state.log_filters["search_text"],
            placeholder="検索キーワード",
            label_visibility="collapsed"
        )
        st.session_state.log_filters["search_text"] = search_text
        
        # クイックフィルター
        st.markdown("**クイックフィルター**")
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("❌ エラーのみ", use_container_width=True):
                st.session_state.log_filters["levels"] = ["ERROR", "CRITICAL"]
                st.rerun()
        
        with col2:
            if st.button("🔧 API呼び出し", use_container_width=True):
                st.session_state.log_filters["search_text"] = "API"
                st.rerun()
        
        st.markdown("---")
        
        # オプション
        st.markdown("**オプション**")
        auto_scroll = st.checkbox(
            "自動スクロール",
            value=st.session_state.log_filters["auto_scroll"]
        )
        st.session_state.log_filters["auto_scroll"] = auto_scroll
    
    def _render_log_viewer(self):
        """ログビューアー"""
        st.subheader("ログ出力")
        
        # コントロールボタン
        col1, col2, col3 = st.columns([1, 1, 2])
        
        with col1:
            if st.button("🗑️ クリア", use_container_width=True):
                st.session_state.log_entries = []
                st.rerun()
        
        with col2:
            if st.button("⏸️ 一時停止" if st.session_state.log_filters["auto_scroll"] else "▶️ 再開", 
                        use_container_width=True):
                st.session_state.log_filters["auto_scroll"] = not st.session_state.log_filters["auto_scroll"]
                st.rerun()
        
        # ログコンテナ
        log_container = st.container()
        
        # ログエントリーを取得
        entries = self._get_filtered_logs()
        
        # ログ表示
        with log_container:
            if not entries:
                st.info("ログがありません")
            else:
                # CSSスタイル
                st.markdown("""
                <style>
                .log-entry {
                    font-family: 'Courier New', monospace;
                    font-size: 12px;
                    padding: 2px 0;
                    border-bottom: 1px solid #f0f0f0;
                }
                .log-trace { color: #6c757d; }
                .log-debug { color: #0d6efd; }
                .log-info { color: #198754; }
                .log-warning { color: #ffc107; }
                .log-error { color: #dc3545; }
                .log-critical { background: #dc3545; color: white; padding: 2px 4px; }
                .log-timestamp { color: #6c757d; }
                .log-agent { font-weight: bold; }
                .log-highlight { background: yellow; }
                </style>
                """, unsafe_allow_html=True)
                
                # 最新のログのみ表示（パフォーマンスのため）
                display_entries = entries[-1000:] if len(entries) > 1000 else entries
                
                # 各エントリーを表示
                for entry in display_entries:
                    self._render_log_entry(entry)
        
        # 自動更新
        if st.session_state.log_filters["auto_scroll"]:
            self._start_auto_refresh()
    
    def _render_log_entry(self, entry: LogEntry):
        """単一のログエントリーを表示"""
        level_class = f"log-{entry.level.value.lower()}"
        icon = entry.level.get_icon()
        
        # 検索テキストのハイライト
        message = entry.message
        search_text = st.session_state.log_filters["search_text"]
        if search_text:
            message = message.replace(search_text, f'<span class="log-highlight">{search_text}</span>')
        
        # HTML形式で表示
        html = f"""
        <div class="log-entry {level_class}">
            <span class="log-timestamp">[{entry.timestamp.strftime('%H:%M:%S.%f')[:-3]}]</span>
            <span>{icon}</span>
            <span class="log-agent">[{entry.agent}]</span>
            <span>{message}</span>
        </div>
        """
        
        st.markdown(html, unsafe_allow_html=True)
        
        # 詳細情報（展開可能）
        if entry.level in [LogLevel.ERROR, LogLevel.CRITICAL]:
            with st.expander(f"詳細 (Line {entry.line_number})"):
                st.code(entry.raw_text)
                if entry.metadata:
                    st.json(entry.metadata)
    
    def _render_statistics(self):
        """統計情報を表示"""
        entries = self._get_all_logs()
        if not entries:
            return
        
        stats = LogStatistics(entries)
        summary = stats.get_summary()
        
        st.markdown("---")
        
        # 統計メトリクス
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.metric("総ログ数", summary["total_logs"])
        
        with col2:
            st.metric("エラー", summary["error_count"], delta_color="inverse")
        
        with col3:
            st.metric("警告", summary["warning_count"], delta_color="inverse")
        
        with col4:
            st.metric("API呼び出し", summary["api_calls"])
        
        with col5:
            st.metric("実行時間", summary["execution_time"])
        
        # エラー分析
        if summary["error_count"] > 0:
            with st.expander("エラー分析"):
                error_analysis = stats.get_error_analysis()
                for error in error_analysis:
                    st.error(f"[{error['timestamp']}] {error['agent']}: {error['message']}")
    
    def _get_all_logs(self) -> List[LogEntry]:
        """全てのログを取得"""
        if not st.session_state.selected_log_session:
            return []
        
        # 常に日本語翻訳を有効にする（言語設定に関わらず）
        translate = st.session_state.get("log_language", "ja") == "ja"
        
        # デバッグログ
        logger.debug(f"Getting logs with translate={translate}, language={st.session_state.get('log_language', 'ja')}")
        
        return self.session_manager.get_session_logs(
            st.session_state.selected_log_session,
            max_lines=0,
            translate=translate
        )
    
    def _get_filtered_logs(self) -> List[LogEntry]:
        """フィルター適用済みのログを取得"""
        all_logs = self._get_all_logs()
        
        # フィルター条件
        levels = [LogLevel.from_string(l) for l in st.session_state.log_filters["levels"]]
        agents = st.session_state.log_filters["agents"] or None
        search_text = st.session_state.log_filters["search_text"] or None
        
        # フィルタリング
        filtered = []
        for entry in all_logs:
            if entry.matches_filter(levels, agents, search_text):
                filtered.append(entry)
        
        return filtered
    
    def _get_available_agents(self) -> List[str]:
        """利用可能なエージェントリストを取得"""
        all_logs = self._get_all_logs()
        agents = set()
        
        for entry in all_logs:
            agents.add(entry.agent)
        
        return sorted(list(agents))
    
    def _start_auto_refresh(self):
        """自動更新を開始"""
        # Streamlitの制約により、真のリアルタイム更新は難しい
        # 代わりに定期的な再実行を使用
        
        # 実行中のセッションの場合のみ自動更新
        sessions = self.session_manager.get_log_sessions()
        current_session = next(
            (s for s in sessions if s['session_id'] == st.session_state.selected_log_session),
            None
        )
        
        if current_session and current_session['is_active']:
            # 1秒後に再実行
            time.sleep(1)
            st.rerun()
    
    def _show_export_dialog(self):
        """エクスポートダイアログを表示"""
        with st.sidebar:
            st.subheader("📥 ログエクスポート")
            
            format_type = st.selectbox(
                "フォーマット",
                ["txt", "json", "csv"],
                help="エクスポート形式を選択"
            )
            
            if st.button("ダウンロード", type="primary"):
                data = self.session_manager.export_logs(
                    st.session_state.selected_log_session,
                    format=format_type
                )
                
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"log_export_{timestamp}.{format_type}"
                
                st.download_button(
                    label=f"📥 {filename}",
                    data=data,
                    file_name=filename,
                    mime=self._get_mime_type(format_type)
                )
    
    def _get_mime_type(self, format_type: str) -> str:
        """MIMEタイプを取得"""
        mime_types = {
            "txt": "text/plain",
            "json": "application/json",
            "csv": "text/csv"
        }
        return mime_types.get(format_type, "application/octet-stream")

# ユーティリティ関数
def render_logs_page():
    """ログページをレンダリング（エントリーポイント）"""
    page = LogsPage()
    page.render()
"""
ログパーサーユーティリティ
CLIログを解析して構造化データに変換
"""

import re
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import json
from webui.utils.log_translator import get_translator

class LogLevel(Enum):
    """ログレベル定義"""
    TRACE = "TRACE"
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"
    
    @classmethod
    def from_string(cls, level_str: str) -> 'LogLevel':
        """文字列からログレベルを取得"""
        level_map = {
            "TRACE": cls.TRACE,
            "DEBUG": cls.DEBUG,
            "INFO": cls.INFO,
            "WARNING": cls.WARNING,
            "WARN": cls.WARNING,
            "ERROR": cls.ERROR,
            "CRITICAL": cls.CRITICAL,
            "FATAL": cls.CRITICAL
        }
        return level_map.get(level_str.upper(), cls.INFO)
    
    def get_icon(self) -> str:
        """ログレベルのアイコンを取得"""
        icons = {
            self.TRACE: "🔍",
            self.DEBUG: "🐛",
            self.INFO: "ℹ️",
            self.WARNING: "⚠️",
            self.ERROR: "❌",
            self.CRITICAL: "🚨"
        }
        return icons.get(self, "📝")
    
    def get_color(self) -> str:
        """ログレベルの色を取得"""
        colors = {
            self.TRACE: "#6c757d",
            self.DEBUG: "#0d6efd",
            self.INFO: "#198754",
            self.WARNING: "#ffc107",
            self.ERROR: "#dc3545",
            self.CRITICAL: "#6f42c1"
        }
        return colors.get(self, "#000000")

@dataclass
class LogEntry:
    """ログエントリー"""
    timestamp: datetime
    level: LogLevel
    agent: str
    message: str
    raw_text: str
    line_number: int
    metadata: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        return {
            "timestamp": self.timestamp.isoformat(),
            "level": self.level.value,
            "agent": self.agent,
            "message": self.message,
            "raw_text": self.raw_text,
            "line_number": self.line_number,
            "metadata": self.metadata or {}
        }
    
    def matches_filter(self, 
                      levels: Optional[List[LogLevel]] = None,
                      agents: Optional[List[str]] = None,
                      search_text: Optional[str] = None) -> bool:
        """フィルター条件に一致するか確認"""
        # レベルフィルター
        if levels and self.level not in levels:
            return False
        
        # エージェントフィルター
        if agents and self.agent not in agents:
            return False
        
        # テキスト検索
        if search_text:
            search_lower = search_text.lower()
            if (search_lower not in self.message.lower() and 
                search_lower not in self.agent.lower() and
                search_lower not in self.raw_text.lower()):
                return False
        
        return True

class LogParser:
    """ログパーサー"""
    
    # ログフォーマットのパターン
    PATTERNS = [
        # 標準フォーマット: [2025-01-17 14:30:15] [INFO] [Agent] メッセージ
        r'^\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\]\s*\[(\w+)\]\s*\[([^\]]+)\]\s*(.+)$',
        # タイムスタンプ付き: 2025-01-17 14:30:15 - メッセージ
        r'^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\s*-\s*(.+)$',
        # エージェントのみ: [Agent] メッセージ（スクリーンショットのパターン）
        r'^\[([^\]]+)\]\s*(.+)$',
        # シンプルログ: INFO: メッセージ
        r'^(\w+):\s*(.+)$',
        # Richライブラリの進捗ログ
        r'^\s*•\s*([^:]+):\s*(.+)$',
        # エラースタックトレース
        r'^(Traceback|File|.*Error:|.*Exception:)(.*)$'
    ]
    
    # エージェント名のマッピング
    AGENT_MAPPING = {
        "market": "Market Analyst",
        "news": "News Analyst",
        "social": "Social Analyst",
        "fundamentals": "Fundamentals Analyst",
        "sentiment": "Social Analyst",
        "bull": "Bull Researcher",
        "bear": "Bear Researcher",
        "research_manager": "Research Manager",
        "aggressive": "Aggressive Analyst",
        "conservative": "Conservative Analyst",
        "neutral": "Neutral Analyst",
        "trader": "Trader",
        "portfolio": "Portfolio Manager",
        "system": "System",
        "cli": "CLI",
        "api": "API"
    }
    
    def __init__(self):
        self.compiled_patterns = [re.compile(pattern) for pattern in self.PATTERNS]
    
    def parse_line(self, line: str, line_number: int = 0) -> Optional[LogEntry]:
        """単一行をパース"""
        line = line.strip()
        if not line:
            return None
        
        # 標準フォーマットを試す
        match = self.compiled_patterns[0].match(line)
        if match:
            timestamp_str, level_str, agent, message = match.groups()
            timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
            level = LogLevel.from_string(level_str)
            agent = self._normalize_agent(agent)
            
            return LogEntry(
                timestamp=timestamp,
                level=level,
                agent=agent,
                message=message,
                raw_text=line,
                line_number=line_number
            )
        
        # タイムスタンプ付きフォーマット
        match = self.compiled_patterns[1].match(line)
        if match:
            timestamp_str, message = match.groups()
            timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
            
            # メッセージからエージェントとレベルを推測
            agent, level = self._infer_agent_and_level(message)
            
            return LogEntry(
                timestamp=timestamp,
                level=level,
                agent=agent,
                message=message,
                raw_text=line,
                line_number=line_number
            )
        
        # エージェントのみのフォーマット: [Agent] メッセージ
        match = self.compiled_patterns[2].match(line)
        if match:
            agent, message = match.groups()
            agent = self._normalize_agent(agent)
            # メッセージからレベルを推測
            _, level = self._infer_agent_and_level(message)
            
            return LogEntry(
                timestamp=datetime.now(),
                level=level,
                agent=agent,
                message=message,
                raw_text=line,
                line_number=line_number
            )
        
        # その他のパターンを試す
        return self._parse_fallback(line, line_number)
    
    def parse_file(self, file_path: str) -> List[LogEntry]:
        """ファイル全体をパース"""
        entries = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line_number, line in enumerate(f, 1):
                    entry = self.parse_line(line, line_number)
                    if entry:
                        entries.append(entry)
                    else:
                        # パースできない行も記録（デバッグ用）
                        if line.strip():
                            entries.append(LogEntry(
                                timestamp=datetime.now(),
                                level=LogLevel.TRACE,
                                agent="System",
                                message=line.strip(),
                                raw_text=line,
                                line_number=line_number
                            ))
        except Exception as e:
            # エラーをログエントリーとして追加
            entries.append(LogEntry(
                timestamp=datetime.now(),
                level=LogLevel.ERROR,
                agent="LogParser",
                message=f"ファイル読み込みエラー: {str(e)}",
                raw_text=f"Error: {str(e)}",
                line_number=0
            ))
        
        return entries
    
    def _normalize_agent(self, agent: str) -> str:
        """エージェント名を正規化"""
        agent_lower = agent.lower().strip()
        
        # マッピングから検索
        for key, value in self.AGENT_MAPPING.items():
            if key in agent_lower:
                return value
        
        # マッピングにない場合はそのまま返す
        return agent.strip()
    
    def _infer_agent_and_level(self, message: str) -> Tuple[str, LogLevel]:
        """メッセージからエージェントとレベルを推測"""
        # エラーパターン
        if any(keyword in message.lower() for keyword in ["error", "exception", "failed"]):
            return "System", LogLevel.ERROR
        
        # 警告パターン
        if any(keyword in message.lower() for keyword in ["warning", "warn"]):
            return "System", LogLevel.WARNING
        
        # エージェント特定パターン
        for agent_key, agent_name in self.AGENT_MAPPING.items():
            if agent_key in message.lower():
                return agent_name, LogLevel.INFO
        
        # デフォルト
        return "System", LogLevel.INFO
    
    def _parse_fallback(self, line: str, line_number: int) -> Optional[LogEntry]:
        """フォールバックパーサー"""
        # API呼び出しパターン
        if "API" in line or "api" in line:
            return LogEntry(
                timestamp=datetime.now(),
                level=LogLevel.DEBUG,
                agent="API",
                message=line,
                raw_text=line,
                line_number=line_number
            )
        
        # ツール呼び出しパターン
        if "Tool Call" in line:
            return LogEntry(
                timestamp=datetime.now(),
                level=LogLevel.DEBUG,
                agent="System",
                message=line,
                raw_text=line,
                line_number=line_number,
                metadata={"type": "tool_call"}
            )
        
        # 進捗表示パターン（Richライブラリ）
        if "•" in line or "─" in line or "│" in line:
            return LogEntry(
                timestamp=datetime.now(),
                level=LogLevel.INFO,
                agent="CLI",
                message=line,
                raw_text=line,
                line_number=line_number,
                metadata={"type": "progress"}
            )
        
        return None

class LogStatistics:
    """ログ統計情報"""
    
    def __init__(self, entries: List[LogEntry]):
        self.entries = entries
    
    def get_summary(self) -> Dict[str, Any]:
        """統計サマリーを取得"""
        if not self.entries:
            return {
                "total_logs": 0,
                "by_level": {},
                "by_agent": {},
                "error_count": 0,
                "warning_count": 0,
                "api_calls": 0,
                "execution_time": "00:00"
            }
        
        # レベル別集計
        by_level = {}
        for entry in self.entries:
            level = entry.level.value
            by_level[level] = by_level.get(level, 0) + 1
        
        # エージェント別集計
        by_agent = {}
        for entry in self.entries:
            agent = entry.agent
            by_agent[agent] = by_agent.get(agent, 0) + 1
        
        # API呼び出し数
        api_calls = sum(1 for entry in self.entries 
                       if entry.agent == "API" or "api" in entry.message.lower())
        
        # 実行時間計算
        if len(self.entries) >= 2:
            duration = self.entries[-1].timestamp - self.entries[0].timestamp
            minutes = int(duration.total_seconds() // 60)
            seconds = int(duration.total_seconds() % 60)
            execution_time = f"{minutes:02d}:{seconds:02d}"
        else:
            execution_time = "00:00"
        
        return {
            "total_logs": len(self.entries),
            "by_level": by_level,
            "by_agent": by_agent,
            "error_count": by_level.get("ERROR", 0),
            "warning_count": by_level.get("WARNING", 0),
            "api_calls": api_calls,
            "execution_time": execution_time
        }
    
    def get_error_analysis(self) -> List[Dict[str, Any]]:
        """エラー分析を取得"""
        errors = [entry for entry in self.entries 
                 if entry.level in [LogLevel.ERROR, LogLevel.CRITICAL]]
        
        error_analysis = []
        for error in errors:
            error_analysis.append({
                "timestamp": error.timestamp.isoformat(),
                "agent": error.agent,
                "message": error.message,
                "line_number": error.line_number
            })
        
        return error_analysis


class JapaneseLogParser(LogParser):
    """日本語対応ログパーサー"""
    
    def __init__(self, translate: bool = True):
        super().__init__()
        self.translate = translate
        self.translator = get_translator() if translate else None
    
    def parse_line(self, line: str, line_number: int = 0) -> Optional[LogEntry]:
        """行をパースして必要に応じて翻訳"""
        entry = super().parse_line(line, line_number)
        
        if entry and self.translate and self.translator:
            # すでに日本語の場合はスキップ
            if not self.translator.is_japanese(entry.message):
                # メッセージを翻訳
                translated_msg = self.translator.translate_message(entry.message)
                entry.message = translated_msg
            
            # エージェント名を翻訳
            translated_agent = self.translator.translate_agent(entry.agent)
            entry.agent = translated_agent
            
            # 生のテキストも翻訳（表示用）
            if not self.translator.is_japanese(entry.raw_text):
                entry.raw_text = self.translator.translate_message(entry.raw_text)
        
        return entry
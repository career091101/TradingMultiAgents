"""
ログストリーマー
リアルタイムでログファイルを監視し、新しいエントリーを配信
"""

import asyncio
import os
from pathlib import Path
from typing import AsyncIterator, Optional, List, Callable, Dict, Any
from datetime import datetime
import logging
import time

from webui.utils.log_parser import LogParser, LogEntry, LogLevel, JapaneseLogParser

logger = logging.getLogger(__name__)

class LogStreamer:
    """ログファイルのリアルタイムストリーミング"""
    
    def __init__(self, log_file_path: str, parser: Optional[LogParser] = None):
        self.log_file_path = Path(log_file_path)
        self.parser = parser or LogParser()
        self.position = 0
        self.is_running = False
        self.callbacks: List[Callable[[LogEntry], None]] = []
        self._file_mtime = 0
        self._buffer = []
        
    def add_callback(self, callback: Callable[[LogEntry], None]):
        """新しいログエントリーのコールバックを追加"""
        self.callbacks.append(callback)
    
    def remove_callback(self, callback: Callable[[LogEntry], None]):
        """コールバックを削除"""
        if callback in self.callbacks:
            self.callbacks.remove(callback)
    
    async def start(self):
        """ストリーミングを開始"""
        self.is_running = True
        logger.info(f"Starting log streaming for: {self.log_file_path}")
        
        # ファイルが存在するまで待機
        while self.is_running and not self.log_file_path.exists():
            await asyncio.sleep(0.5)
        
        # 初期位置を設定（既存の内容をスキップ）
        if self.log_file_path.exists():
            self.position = self.log_file_path.stat().st_size
            self._file_mtime = self.log_file_path.stat().st_mtime
        
        # ストリーミングループ
        while self.is_running:
            try:
                await self._check_and_read_new_lines()
            except Exception as e:
                logger.error(f"Error in log streaming: {e}")
            
            await asyncio.sleep(0.1)  # 100ms間隔でチェック
    
    async def stop(self):
        """ストリーミングを停止"""
        self.is_running = False
        logger.info(f"Stopped log streaming for: {self.log_file_path}")
    
    async def _check_and_read_new_lines(self):
        """新しい行をチェックして読み込み"""
        if not self.log_file_path.exists():
            return
        
        # ファイルの変更をチェック
        current_mtime = self.log_file_path.stat().st_mtime
        if current_mtime <= self._file_mtime:
            return
        
        self._file_mtime = current_mtime
        
        try:
            with open(self.log_file_path, 'r', encoding='utf-8') as f:
                # 前回の位置にシーク
                f.seek(self.position)
                
                # 新しい行を読み込み
                new_lines = f.readlines()
                
                # 現在の位置を更新
                self.position = f.tell()
                
                # 各行をパースして配信
                for line_number, line in enumerate(new_lines, self.position):
                    if entry := self.parser.parse_line(line, line_number):
                        await self._notify_callbacks(entry)
                        
        except Exception as e:
            logger.error(f"Error reading log file: {e}")
    
    async def _notify_callbacks(self, entry: LogEntry):
        """コールバックに通知"""
        for callback in self.callbacks:
            try:
                callback(entry)
            except Exception as e:
                logger.error(f"Error in log callback: {e}")
    
    async def stream_logs(self) -> AsyncIterator[LogEntry]:
        """非同期イテレーターとしてログをストリーム"""
        queue = asyncio.Queue()
        
        def enqueue(entry: LogEntry):
            queue.put_nowait(entry)
        
        self.add_callback(enqueue)
        
        try:
            # ストリーミングを開始
            stream_task = asyncio.create_task(self.start())
            
            # キューからエントリーを取得
            while self.is_running:
                try:
                    entry = await asyncio.wait_for(queue.get(), timeout=1.0)
                    yield entry
                except asyncio.TimeoutError:
                    continue
                    
        finally:
            self.remove_callback(enqueue)
            await self.stop()
            stream_task.cancel()

class LogSessionManager:
    """ログセッション管理"""
    
    def __init__(self, logs_dir: str = "logs/webui"):
        self.logs_dir = Path(logs_dir)
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        self.active_sessions: Dict[str, LogStreamer] = {}
    
    def get_log_sessions(self) -> List[Dict[str, Any]]:
        """利用可能なログセッションを取得"""
        sessions = []
        
        if not self.logs_dir.exists():
            return sessions
        
        # ログファイルを検索
        for log_file in self.logs_dir.glob("analysis_*.log"):
            # ファイル名から情報を抽出
            # analysis_TICKER_YYYYMMDD_HHMMSS.log
            parts = log_file.stem.split('_')
            if len(parts) >= 4:
                ticker = parts[1]
                date_str = parts[2]
                time_str = parts[3]
                
                # ファイル情報を取得
                stat = log_file.stat()
                
                sessions.append({
                    "session_id": log_file.stem,
                    "ticker": ticker,
                    "date": f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}",
                    "time": f"{time_str[:2]}:{time_str[2:4]}:{time_str[4:6]}",
                    "file_path": str(log_file),
                    "size": stat.st_size,
                    "modified": datetime.fromtimestamp(stat.st_mtime),
                    "is_active": self._is_file_active(log_file)
                })
        
        # 最新順にソート
        sessions.sort(key=lambda x: x['modified'], reverse=True)
        
        return sessions
    
    def _is_file_active(self, file_path: Path) -> bool:
        """ファイルがアクティブ（書き込み中）かチェック"""
        # 最終更新が5秒以内ならアクティブとみなす
        if file_path.exists():
            mtime = file_path.stat().st_mtime
            return (time.time() - mtime) < 5
        return False
    
    def start_streaming(self, session_id: str, callback: Callable[[LogEntry], None]) -> Optional[LogStreamer]:
        """ログストリーミングを開始"""
        # セッション情報を取得
        sessions = self.get_log_sessions()
        session = next((s for s in sessions if s['session_id'] == session_id), None)
        
        if not session:
            logger.error(f"Session not found: {session_id}")
            return None
        
        # 既存のストリーマーがあれば返す
        if session_id in self.active_sessions:
            streamer = self.active_sessions[session_id]
            streamer.add_callback(callback)
            return streamer
        
        # 新しいストリーマーを作成
        streamer = LogStreamer(session['file_path'])
        streamer.add_callback(callback)
        self.active_sessions[session_id] = streamer
        
        # ストリーミングを開始
        asyncio.create_task(streamer.start())
        
        return streamer
    
    def stop_streaming(self, session_id: str):
        """ログストリーミングを停止"""
        if session_id in self.active_sessions:
            streamer = self.active_sessions[session_id]
            asyncio.create_task(streamer.stop())
            del self.active_sessions[session_id]
    
    def get_session_logs(self, session_id: str, 
                        start_line: int = 0, 
                        max_lines: int = 1000,
                        translate: bool = True) -> List[LogEntry]:
        """セッションのログを取得"""
        sessions = self.get_log_sessions()
        session = next((s for s in sessions if s['session_id'] == session_id), None)
        
        if not session:
            return []
        
        # 翻訳設定に応じてパーサーを選択
        parser = JapaneseLogParser(translate=translate) if translate else LogParser()
        entries = parser.parse_file(session['file_path'])
        
        # 指定範囲のエントリーを返す
        if start_line > 0:
            entries = entries[start_line:]
        if max_lines > 0:
            entries = entries[:max_lines]
        
        return entries
    
    def search_logs(self, session_id: str, search_text: str, 
                   case_sensitive: bool = False) -> List[LogEntry]:
        """ログを検索"""
        entries = self.get_session_logs(session_id, max_lines=0)
        
        if not case_sensitive:
            search_text = search_text.lower()
        
        results = []
        for entry in entries:
            match_text = entry.raw_text if case_sensitive else entry.raw_text.lower()
            if search_text in match_text:
                results.append(entry)
        
        return results
    
    def export_logs(self, session_id: str, format: str = "txt") -> bytes:
        """ログをエクスポート"""
        entries = self.get_session_logs(session_id, max_lines=0)
        
        if format == "json":
            import json
            data = [entry.to_dict() for entry in entries]
            return json.dumps(data, indent=2, ensure_ascii=False).encode('utf-8')
        
        elif format == "csv":
            import csv
            import io
            
            output = io.StringIO()
            writer = csv.writer(output)
            
            # ヘッダー
            writer.writerow(["Timestamp", "Level", "Agent", "Message"])
            
            # データ
            for entry in entries:
                writer.writerow([
                    entry.timestamp.isoformat(),
                    entry.level.value,
                    entry.agent,
                    entry.message
                ])
            
            return output.getvalue().encode('utf-8')
        
        else:  # txt
            lines = []
            for entry in entries:
                lines.append(entry.raw_text)
            return '\n'.join(lines).encode('utf-8')

# グローバルセッションマネージャー
_session_manager = None

def get_session_manager() -> LogSessionManager:
    """グローバルセッションマネージャーを取得"""
    global _session_manager
    if _session_manager is None:
        from pathlib import Path
        project_root = Path(__file__).parent.parent.parent
        logs_dir = project_root / "logs" / "webui"
        _session_manager = LogSessionManager(str(logs_dir))
    return _session_manager
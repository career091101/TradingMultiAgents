#!/usr/bin/env python3
"""
ログパーサーのテストスクリプト
"""

import sys
from pathlib import Path

# プロジェクトルートを追加
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from webui.utils.log_parser import LogParser, LogLevel, LogStatistics
from webui.utils.log_streamer import LogSessionManager

def test_log_parser():
    """ログパーサーのテスト"""
    print("=== ログパーサーテスト ===\n")
    
    parser = LogParser()
    
    # テストログ行
    test_lines = [
        "[2025-01-17 14:30:15] [INFO] [Market Analyst] テクニカル分析を開始します",
        "[2025-01-17 14:30:16] [DEBUG] [API] FinnHub API呼び出し: /quote/AAPL",
        "[2025-01-17 14:30:17] [WARNING] [News Analyst] APIレート制限に近づいています",
        "[2025-01-17 14:30:20] [ERROR] [System] 接続エラー: タイムアウト",
        "2025-01-17 14:30:21 - 追加のログメッセージ",
        "• Market Analyst: RSI = 65.4, MACD = 0.23",
        "ERROR: ファイルが見つかりません",
    ]
    
    print("テストログ:")
    for line in test_lines:
        print(f"  {line}")
    
    print("\nパース結果:")
    entries = []
    for i, line in enumerate(test_lines, 1):
        entry = parser.parse_line(line, i)
        if entry:
            entries.append(entry)
            print(f"  Line {i}:")
            print(f"    Level: {entry.level.value} {entry.level.get_icon()}")
            print(f"    Agent: {entry.agent}")
            print(f"    Message: {entry.message}")
            print()
    
    # 統計情報
    if entries:
        stats = LogStatistics(entries)
        summary = stats.get_summary()
        
        print("統計情報:")
        print(f"  総ログ数: {summary['total_logs']}")
        print(f"  レベル別: {summary['by_level']}")
        print(f"  エージェント別: {summary['by_agent']}")
        print(f"  エラー数: {summary['error_count']}")
        print(f"  警告数: {summary['warning_count']}")

def test_log_session_manager():
    """ログセッションマネージャーのテスト"""
    print("\n\n=== ログセッションマネージャーテスト ===\n")
    
    manager = LogSessionManager()
    
    # 利用可能なセッション
    sessions = manager.get_log_sessions()
    
    print(f"利用可能なログセッション: {len(sessions)}件")
    
    for session in sessions[:5]:  # 最初の5件のみ表示
        print(f"\nセッション: {session['session_id']}")
        print(f"  ティッカー: {session['ticker']}")
        print(f"  日付: {session['date']} {session['time']}")
        print(f"  ファイルサイズ: {session['size']:,} bytes")
        print(f"  アクティブ: {'はい' if session['is_active'] else 'いいえ'}")
        
        # 最初の数行を取得
        entries = manager.get_session_logs(session['session_id'], max_lines=5)
        if entries:
            print(f"  最初の{len(entries)}行:")
            for entry in entries:
                print(f"    [{entry.timestamp.strftime('%H:%M:%S')}] {entry.level.value} - {entry.agent}: {entry.message[:50]}...")

def test_log_filtering():
    """ログフィルタリングのテスト"""
    print("\n\n=== ログフィルタリングテスト ===\n")
    
    parser = LogParser()
    
    # テストエントリー作成
    test_entries = []
    for i in range(10):
        level = [LogLevel.INFO, LogLevel.WARNING, LogLevel.ERROR][i % 3]
        agent = ["Market Analyst", "News Analyst", "API"][i % 3]
        message = f"テストメッセージ {i}: {'エラー' if level == LogLevel.ERROR else '情報'}"
        
        from datetime import datetime
        entry = parser.parse_line(
            f"[2025-01-17 14:30:{i:02d}] [{level.value}] [{agent}] {message}",
            i + 1
        )
        if entry:
            test_entries.append(entry)
    
    # フィルターテスト
    print("全エントリー数:", len(test_entries))
    
    # エラーのみ
    error_only = [e for e in test_entries if e.matches_filter(levels=[LogLevel.ERROR])]
    print(f"\nエラーのみ: {len(error_only)}件")
    
    # 特定エージェント
    market_only = [e for e in test_entries if e.matches_filter(agents=["Market Analyst"])]
    print(f"Market Analystのみ: {len(market_only)}件")
    
    # テキスト検索
    error_text = [e for e in test_entries if e.matches_filter(search_text="エラー")]
    print(f"'エラー'を含む: {len(error_text)}件")

def main():
    """メイン関数"""
    print("TradingAgents ログシステムテスト\n")
    
    test_log_parser()
    test_log_session_manager()
    test_log_filtering()
    
    print("\n\nテスト完了")

if __name__ == "__main__":
    main()
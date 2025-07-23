#!/usr/bin/env python3
"""
ログ翻訳機能のテストスクリプト
"""

import sys
from pathlib import Path

# プロジェクトルートを追加
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from webui.utils.log_translator import LogTranslator
from webui.utils.log_parser import JapaneseLogParser
from datetime import datetime

def test_translator():
    """翻訳機能のテスト"""
    print("=== ログ翻訳テスト ===\n")
    
    translator = LogTranslator()
    
    # テストメッセージ
    test_messages = [
        # API関連
        "API call to /quote/AAPL",
        "API rate limit reached",
        "API error: Connection timeout",
        
        # 分析関連
        "Starting analysis",
        "Analysis completed",
        "Analyzing technical indicators",
        "Processing market data",
        "Generating report",
        
        # エラー関連
        "Error: Invalid ticker symbol",
        "Failed to fetch data",
        "Connection timeout",
        "Could not connect to server",
        
        # ツール関連
        "Tool Call: get_stock_data",
        "Fetching financial data",
        "Calculating RSI",
        
        # システム関連
        "Initializing system",
        "Loading configuration",
        "System ready",
        
        # 固定メッセージ
        "Analyzing technical indicators",
        "Fetching news articles",
        "Bull researcher analyzing",
        "Risk assessment completed",
    ]
    
    print("英語 → 日本語 翻訳:")
    print("-" * 60)
    
    for msg in test_messages:
        translated = translator.translate_message(msg)
        print(f"原文: {msg}")
        print(f"翻訳: {translated}")
        print()

def test_agent_translation():
    """エージェント名翻訳のテスト"""
    print("\n=== エージェント名翻訳テスト ===\n")
    
    translator = LogTranslator()
    
    agents = [
        "Market Analyst",
        "News Analyst",
        "Bull Researcher",
        "Bear Researcher",
        "Portfolio Manager",
        "System",
        "API",
        "Unknown Agent"
    ]
    
    print("エージェント名翻訳:")
    print("-" * 40)
    
    for agent in agents:
        translated = translator.translate_agent(agent)
        print(f"{agent:<20} → {translated}")

def test_parser_integration():
    """パーサー統合テスト"""
    print("\n\n=== パーサー統合テスト ===\n")
    
    # 日本語翻訳ありのパーサー
    parser_ja = JapaneseLogParser(translate=True)
    
    # 日本語翻訳なしのパーサー
    parser_en = JapaneseLogParser(translate=False)
    
    # テストログ行
    test_logs = [
        "[2025-01-17 14:30:15] [INFO] [Market Analyst] Starting analysis",
        "[2025-01-17 14:30:16] [DEBUG] [API] API call to /quote/AAPL",
        "[2025-01-17 14:30:17] [WARNING] [News Analyst] API rate limit reached",
        "[2025-01-17 14:30:18] [ERROR] [System] Connection timeout",
        "[2025-01-17 14:30:19] [INFO] [Bull Researcher] Analyzing market trends",
        "[2025-01-17 14:30:20] [INFO] [Portfolio Manager] Optimizing portfolio allocation",
        # すでに日本語のログ
        "[2025-01-17 14:30:21] [INFO] [Market Analyst] テクニカル分析を開始します",
    ]
    
    print("日本語翻訳あり:")
    print("-" * 80)
    
    for i, log in enumerate(test_logs, 1):
        entry = parser_ja.parse_line(log, i)
        if entry:
            print(f"[{entry.timestamp.strftime('%H:%M:%S')}] {entry.level.get_icon()} [{entry.agent}] {entry.message}")
    
    print("\n\n日本語翻訳なし:")
    print("-" * 80)
    
    for i, log in enumerate(test_logs, 1):
        entry = parser_en.parse_line(log, i)
        if entry:
            print(f"[{entry.timestamp.strftime('%H:%M:%S')}] {entry.level.get_icon()} [{entry.agent}] {entry.message}")

def test_complex_messages():
    """複雑なメッセージの翻訳テスト"""
    print("\n\n=== 複雑なメッセージ翻訳テスト ===\n")
    
    translator = LogTranslator()
    
    complex_messages = [
        "Failed to connect to database server",
        "Processing technical indicators for AAPL",
        "Calculating moving average with period 20",
        "Fetching historical data from 2025-01-01 to 2025-01-17",
        "Error: Unable to parse JSON response from API",
        "Tool Call: get_financial_statements for ticker MSFT",
        "Analyzing sentiment from 150 news articles",
        "Generating comprehensive investment report",
    ]
    
    for msg in complex_messages:
        translated = translator.translate_message(msg)
        print(f"原文: {msg}")
        print(f"翻訳: {translated}")
        print()

def test_japanese_detection():
    """日本語検出テスト"""
    print("\n\n=== 日本語検出テスト ===\n")
    
    translator = LogTranslator()
    
    test_texts = [
        "This is English text",
        "これは日本語のテキストです",
        "Mixed text 混合テキスト",
        "API呼び出し中",
        "Starting analysis",
        "分析を開始します",
    ]
    
    for text in test_texts:
        is_japanese = translator.is_japanese(text)
        print(f"'{text}' → 日本語: {'はい' if is_japanese else 'いいえ'}")

def main():
    """メイン関数"""
    print("TradingAgents ログ翻訳テスト\n")
    
    test_translator()
    test_agent_translation()
    test_parser_integration()
    test_complex_messages()
    test_japanese_detection()
    
    print("\n\nテスト完了")

if __name__ == "__main__":
    main()
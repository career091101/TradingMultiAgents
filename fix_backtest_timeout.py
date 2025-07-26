#!/usr/bin/env python3
"""
バックテストのタイムアウト問題を解決するための修正スクリプト
"""

import json
from pathlib import Path

def create_mock_config():
    """モックモードでの実行設定を作成"""
    config = {
        "name": "test_mock_mode",
        "symbols": ["AAPL"],
        "initial_capital": 10000,
        "start_date": "2025-07-01",
        "end_date": "2025-07-14",
        "agent_config": {
            "llm_config": {
                "deep_think_model": "mock",  # モックモードを使用
                "quick_think_model": "mock",
                "temperature": 0.0,
                "timeout": 600  # タイムアウトを10分に延長
            },
            "max_debate_rounds": 1,
            "max_risk_discuss_rounds": 1,
            "use_japanese_prompts": True
        },
        "debug": True,
        "mock_mode": True
    }
    
    # 設定ファイルを保存
    config_file = Path("backtest_mock_config.json")
    with open(config_file, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)
    
    print(f"✅ モックモード設定ファイルを作成しました: {config_file}")
    print("\n📝 WebUIでの使用方法:")
    print("1. WebUIのバックテストタブを開く")
    print("2. LLM設定で以下を設定:")
    print("   - Deep Think Model: mock")
    print("   - Quick Think Model: mock")
    print("3. デバッグモードとモックモードを有効化")
    print("4. バックテストを実行")
    
    return config

def create_timeout_fix():
    """タイムアウト延長設定を作成"""
    config = {
        "name": "test_with_extended_timeout",
        "symbols": ["AAPL"],
        "initial_capital": 10000,
        "start_date": "2025-07-01",
        "end_date": "2025-07-14",
        "agent_config": {
            "llm_config": {
                "deep_think_model": "o3",
                "quick_think_model": "o4-mini",
                "temperature": 0.0,
                "timeout": 1200  # タイムアウトを20分に延長
            },
            "max_debate_rounds": 1,
            "max_risk_discuss_rounds": 1,
            "use_japanese_prompts": True
        },
        "debug": True,
        "mock_mode": False
    }
    
    # 設定ファイルを保存
    config_file = Path("backtest_extended_timeout_config.json")
    with open(config_file, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ タイムアウト延長設定ファイルを作成しました: {config_file}")
    print("\n📝 実際のLLMを使用する場合:")
    print("1. まず上記のモックモードでテスト")
    print("2. 成功したら、この設定でo3/o4-miniモデルを使用")
    print("3. タイムアウトは20分に設定済み")
    
    return config

def diagnose_issues():
    """現在の問題を診断"""
    print("🔍 バックテスト実行問題の診断結果:")
    print("\n❌ 検出された問題:")
    print("1. o3モデルのレスポンス時間が長い（40秒以上）")
    print("2. 日時フォーマットエラー（修正済み）")
    print("3. Phase 2でプロセスが停止")
    print("\n✅ 修正内容:")
    print("1. 日時パース処理を修正（ISO形式対応）")
    print("2. モックモード設定の作成")
    print("3. タイムアウト延長設定の作成")
    print("\n💡 推奨される実行手順:")
    print("1. まずモックモードで完全な実行を確認")
    print("2. 成功したら実際のLLMモデルで実行")
    print("3. 必要に応じてタイムアウトを調整")

if __name__ == "__main__":
    diagnose_issues()
    print("\n" + "="*50 + "\n")
    create_mock_config()
    create_timeout_fix()
    print("\n✨ 修正が完了しました！")
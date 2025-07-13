#!/usr/bin/env python3
"""
Streamlit Cloud用メインエントリーポイント
ファイル名: streamlit_app.py (Streamlit Cloud規約)
"""

import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# プロジェクトルートをPythonパスに追加
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# .envファイルを読み込み（ローカル開発時のみ）
load_dotenv()

# 環境変数確認（デバッグ用）
def check_environment():
    """環境変数の設定状況を確認"""
    required_vars = ["FINNHUB_API_KEY", "OPENAI_API_KEY"]
    
    print("🔍 環境変数チェック:")
    for var in required_vars:
        value = os.getenv(var)
        status = "✅ 設定済み" if value else "❌ 未設定"
        print(f"  {var}: {status}")
    
    optional_vars = ["ANTHROPIC_API_KEY", "GOOGLE_API_KEY", "REDDIT_CLIENT_ID"]
    for var in optional_vars:
        value = os.getenv(var)
        if value:
            print(f"  {var}: ✅ 設定済み")

# 環境確認実行
check_environment()

# WebUIアプリケーションを直接インポート・実行
try:
    from webui.app import main as run_webui
    
    print("🚀 TradingAgents WebUI起動中...")
    print("📱 Streamlit Cloud デプロイ対応版")
    
    # メインアプリケーション実行
    if __name__ == "__main__":
        run_webui()
        
except ImportError as e:
    print(f"❌ WebUI インポートエラー: {e}")
    print("💡 webui/app.py ファイルが存在することを確認してください")
    sys.exit(1)
except Exception as e:
    print(f"❌ 予期しないエラー: {e}")
    sys.exit(1)
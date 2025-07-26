#!/usr/bin/env python3
"""
WebUI起動スクリプト
使用法: python run_webui.py

Streamlit Cloud対応:
- streamlit_app.pyの機能も統合
- 環境変数チェック機能を拡張
"""

import subprocess
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

def check_environment():
    """環境変数の設定状況を確認"""
    print("🔍 環境変数チェック:")
    
    # 必須環境変数
    required_vars = ["FINNHUB_API_KEY", "OPENAI_API_KEY"]
    all_required_set = True
    
    for var in required_vars:
        value = os.getenv(var)
        status = "✅ 設定済み" if value else "❌ 未設定"
        print(f"  {var}: {status}")
        if not value:
            all_required_set = False
    
    # オプション環境変数
    optional_vars = ["ANTHROPIC_API_KEY", "GOOGLE_API_KEY", "REDDIT_CLIENT_ID"]
    for var in optional_vars:
        value = os.getenv(var)
        if value:
            print(f"  {var}: ✅ 設定済み")
    
    return all_required_set

def main():
    # .envファイルを読み込み
    load_dotenv()
    
    # プロジェクトルートをPythonパスに追加（Streamlit Cloud対応）
    project_root = Path(__file__).parent
    sys.path.insert(0, str(project_root))
    
    webui_path = Path(__file__).parent / "webui" / "app.py"
    
    if not webui_path.exists():
        print(f"❌ WebUIファイルが見つかりません: {webui_path}")
        sys.exit(1)
    
    print("🚀 TradingAgents WebUIを起動中...")
    print(f"📁 WebUIパス: {webui_path}")
    print("📱 Streamlit Cloud デプロイ対応版")
    
    # 環境変数確認
    all_required_set = check_environment()
    
    if not all_required_set:
        print("\n⚠️ 必要な環境変数が設定されていません")
        print("詳細は.env.exampleファイルを参照してください")
    
    print("\n🌐 ブラウザで http://localhost:8501 を開いてください")
    print("🔚 終了するには Ctrl+C を押してください")
    
    try:
        # Streamlit Cloud対応: デプロイ環境では sys.executable を使用
        cmd = [sys.executable, "-m", "streamlit", "run", str(webui_path)]
        subprocess.run(cmd, cwd=str(Path(__file__).parent))
    except KeyboardInterrupt:
        print("\n👋 WebUIを終了します")
    except Exception as e:
        print(f"❌ WebUI起動エラー: {e}")
        sys.exit(1)

# Streamlit Cloud互換性のためのエイリアス
# streamlit_app.pyの代わりにこのファイルも使用可能
if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
WebUI起動スクリプト
使用法: python run_webui.py
"""

import subprocess
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

def main():
    # .envファイルを読み込み
    load_dotenv()
    
    webui_path = Path(__file__).parent / "webui" / "app.py"
    
    if not webui_path.exists():
        print(f"❌ WebUIファイルが見つかりません: {webui_path}")
        sys.exit(1)
    
    print("🚀 TradingAgents WebUIを起動中...")
    print(f"📁 WebUIパス: {webui_path}")
    
    # 環境変数確認
    finnhub_key = os.getenv("FINNHUB_API_KEY")
    openai_key = os.getenv("OPENAI_API_KEY")
    
    print(f"🔑 FINNHUB_API_KEY: {'✅ 設定済み' if finnhub_key else '❌ 未設定'}")
    print(f"🔑 OPENAI_API_KEY: {'✅ 設定済み' if openai_key else '❌ 未設定'}")
    
    print("🌐 ブラウザで http://localhost:8501 を開いてください")
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

if __name__ == "__main__":
    main()
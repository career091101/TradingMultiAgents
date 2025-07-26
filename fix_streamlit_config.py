#!/usr/bin/env python3
"""
Fix Streamlit configuration issues
"""

import os
import shutil

def fix_streamlit_config():
    print("=== Streamlit設定の修正 ===\n")
    
    # Backup old config
    config_path = ".streamlit/config.toml"
    if os.path.exists(config_path):
        shutil.copy(config_path, f"{config_path}.backup")
        print(f"✓ 既存の設定をバックアップしました: {config_path}.backup")
    
    # Create new minimal config
    new_config = """[theme]
base = "light"

[server]
enableCORS = true
enableXsrfProtection = true
"""
    
    os.makedirs(".streamlit", exist_ok=True)
    with open(config_path, 'w') as f:
        f.write(new_config)
    
    print(f"✓ 新しい設定ファイルを作成しました: {config_path}")
    
    # Kill any existing streamlit processes
    os.system("pkill -f streamlit 2>/dev/null || true")
    print("✓ 既存のStreamlitプロセスを終了しました")
    
    print("\n次のステップ:")
    print("1. streamlit run run_webui.py")
    print("2. ブラウザで http://localhost:8501 にアクセス")

if __name__ == "__main__":
    fix_streamlit_config()
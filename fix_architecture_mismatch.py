#!/usr/bin/env python3
"""
Fix Python architecture mismatch issue
"""

import os
import subprocess
import sys

def fix_architecture_mismatch():
    print("=== Pythonアーキテクチャ不一致の修正 ===\n")
    
    # Check current Python info
    print("現在のPython環境:")
    print(f"Python: {sys.executable}")
    print(f"Version: {sys.version}")
    
    # Kill all streamlit processes
    subprocess.run(["pkill", "-f", "streamlit"], capture_output=True)
    print("✓ Streamlitプロセスを終了しました")
    
    # Reinstall pydantic with correct architecture
    print("\npydantic_coreを再インストールしています...")
    
    # Force reinstall pydantic and pydantic-core
    result = subprocess.run([
        sys.executable, "-m", "pip", "install", "--force-reinstall", 
        "--no-cache-dir", "pydantic", "pydantic-core"
    ], capture_output=True, text=True)
    
    if result.returncode == 0:
        print("✓ pydanticの再インストールが完了しました")
    else:
        print("✗ インストールエラー:")
        print(result.stderr)
        return False
    
    # Verify installation
    try:
        import pydantic
        print(f"\n✓ pydantic {pydantic.VERSION} が正常にインポートできました")
        return True
    except ImportError as e:
        print(f"\n✗ pydanticのインポートに失敗: {e}")
        return False

if __name__ == "__main__":
    success = fix_architecture_mismatch()
    
    if success:
        print("\n次のステップ:")
        print("1. streamlit run run_webui.py")
        print("2. ブラウザで http://localhost:8501 にアクセス")
    else:
        print("\n追加の対処法:")
        print("1. pip uninstall pydantic pydantic-core -y")
        print("2. pip install pydantic pydantic-core")
        print("3. または、ARM64版のPythonに切り替える")
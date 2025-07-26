import platform
import sys
import os

print("=== WebUI ARM64 デバッグ情報 ===")
print(f"Python実行ファイル: {sys.executable}")
print(f"Pythonバージョン: {sys.version}")
print(f"プラットフォーム: {platform.platform()}")
print(f"マシンタイプ: {platform.machine()}")
print(f"プロセッサ: {platform.processor()}")
print(f"アーキテクチャ: {platform.architecture()}")
print(f"環境変数 ARCHFLAGS: {os.environ.get('ARCHFLAGS', 'Not set')}")

# NumPyのアーキテクチャ確認
try:
    import numpy as np
    print(f"\nNumPy バージョン: {np.__version__}")
    print(f"NumPy パス: {np.__file__}")
except ImportError:
    print("\nNumPy not installed")

# Streamlitの確認
try:
    import streamlit as st
    print(f"\nStreamlit バージョン: {st.__version__}")
    print(f"Streamlit パス: {st.__file__}")
except ImportError:
    print("\nStreamlit not installed")

print("\n✅ このスクリプトがARM64で実行されている場合、")
print("   'マシンタイプ: arm64' と表示されます")

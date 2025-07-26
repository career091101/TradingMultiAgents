#!/usr/bin/env python3
"""
Root cause fix for architecture mismatch
"""

import os
import subprocess
import sys
import platform

def diagnose_system():
    """Diagnose the current system architecture"""
    print("=== システム診断 ===\n")
    
    print(f"Machine architecture: {platform.machine()}")
    print(f"Processor: {platform.processor()}")
    print(f"Python version: {sys.version}")
    print(f"Python executable: {sys.executable}")
    
    # Check if running under Rosetta
    result = subprocess.run(['sysctl', '-n', 'sysctl.proc_translated'], 
                          capture_output=True, text=True)
    is_rosetta = result.stdout.strip() == '1'
    print(f"Running under Rosetta: {is_rosetta}")
    
    return is_rosetta

def create_native_environment():
    """Create a native ARM64 Python environment"""
    print("\n=== ネイティブARM64環境の作成 ===\n")
    
    # Check if we have native Python
    native_python = "/opt/homebrew/bin/python3"
    if os.path.exists(native_python):
        print(f"✓ Native Python found: {native_python}")
        
        # Check its architecture
        result = subprocess.run(['file', native_python], 
                              capture_output=True, text=True)
        print(f"Architecture: {result.stdout.strip()}")
        
        return native_python
    else:
        print("✗ Native Python not found")
        print("\nHomebrew for ARM64をインストールしてください:")
        print("1. /bin/bash -c \"$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\"")
        print("2. brew install python@3.12")
        return None

def create_venv_with_native_python(native_python):
    """Create virtual environment with native Python"""
    print("\n=== 仮想環境の作成 ===\n")
    
    venv_path = "venv_arm64"
    
    # Remove old venv if exists
    if os.path.exists(venv_path):
        import shutil
        shutil.rmtree(venv_path)
        print(f"✓ 既存の環境を削除: {venv_path}")
    
    # Create new venv
    subprocess.run([native_python, '-m', 'venv', venv_path], check=True)
    print(f"✓ 新しい仮想環境を作成: {venv_path}")
    
    # Get pip path
    pip_path = os.path.join(venv_path, 'bin', 'pip')
    
    # Install requirements
    print("\n依存関係をインストール中...")
    requirements = [
        'streamlit',
        'pydantic',
        'pandas',
        'numpy',
        'yfinance',
        'langchain',
        'langchain-openai',
        'asyncio',
        'aiohttp',
        'python-dateutil',
        'pytz',
        'plotly',
        'matplotlib',
        'seaborn',
        'pytest',
        'pytest-asyncio'
    ]
    
    for req in requirements:
        print(f"Installing {req}...")
        subprocess.run([pip_path, 'install', req], 
                      capture_output=True, check=True)
    
    print("\n✓ すべての依存関係をインストールしました")
    
    return venv_path

def create_launcher_script(venv_path):
    """Create launcher script for the native environment"""
    launcher_content = f'''#!/bin/bash
# Native ARM64 WebUI launcher

echo "=== Native ARM64 WebUI Launcher ==="

# Activate virtual environment
source {venv_path}/bin/activate

# Set environment variables
export PYTHONPATH="/Users/y-sato/TradingAgents2:$PYTHONPATH"

# Check Python architecture
echo "Python: $(which python)"
echo "Architecture: $(file $(which python))"

# Kill any existing streamlit
pkill -f streamlit 2>/dev/null || true

# Start streamlit
echo -e "\\nStarting WebUI..."
python -m streamlit run run_webui.py --server.port 8501

deactivate
'''
    
    launcher_path = "run_webui_native.sh"
    with open(launcher_path, 'w') as f:
        f.write(launcher_content)
    
    os.chmod(launcher_path, 0o755)
    print(f"\n✓ ランチャースクリプトを作成: {launcher_path}")
    
    return launcher_path

def main():
    """Main function"""
    print("=== Pythonアーキテクチャ問題の根本解決 ===\n")
    
    # Diagnose system
    is_rosetta = diagnose_system()
    
    if is_rosetta:
        print("\n⚠️  警告: 現在Rosetta経由でx86_64として実行されています")
    
    # Find or suggest native Python
    native_python = create_native_environment()
    
    if native_python:
        # Create virtual environment
        venv_path = create_venv_with_native_python(native_python)
        
        # Create launcher
        launcher = create_launcher_script(venv_path)
        
        print("\n=== 完了 ===")
        print(f"\n実行方法: ./{launcher}")
        print("\nまたは手動で:")
        print(f"1. source {venv_path}/bin/activate")
        print("2. python -m streamlit run run_webui.py")
    else:
        print("\n次のステップ:")
        print("1. Native ARM64 Pythonをインストール")
        print("2. このスクリプトを再実行")

if __name__ == "__main__":
    main()
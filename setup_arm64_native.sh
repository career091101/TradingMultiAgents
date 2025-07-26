#!/bin/bash
# M1 Mac用 ARM64ネイティブ環境セットアップスクリプト

echo "🍎 M1 Mac ARM64ネイティブ環境セットアップ"
echo "=========================================="

# 色付き出力用の関数
print_success() { echo -e "\033[0;32m✅ $1\033[0m"; }
print_error() { echo -e "\033[0;31m❌ $1\033[0m"; }
print_info() { echo -e "\033[0;34m📍 $1\033[0m"; }
print_warning() { echo -e "\033[0;33m⚠️  $1\033[0m"; }

# アーキテクチャ確認
print_info "現在のアーキテクチャを確認中..."
ARCH=$(uname -m)
if [ "$ARCH" != "arm64" ]; then
    print_error "このスクリプトはARM64環境でのみ動作します"
    print_info "現在のアーキテクチャ: $ARCH"
    exit 1
fi
print_success "ARM64環境で実行中"

# Rosetta 2チェック
if sysctl -n sysctl.proc_translated 2>/dev/null | grep -q 1; then
    print_error "Rosetta 2経由で実行されています"
    print_info "ターミナルをネイティブモードで開き直してください"
    exit 1
fi

# 古いx86_64環境のクリーンアップ
if [ -d ".venv" ]; then
    print_warning "既存の.venv環境を削除します"
    rm -rf .venv
fi

# ARM64環境の作成
print_info "ARM64ネイティブPython環境を作成中..."

# Homebrewの確認
if [ -x "/opt/homebrew/bin/python3" ]; then
    PYTHON_BIN="/opt/homebrew/bin/python3"
    print_success "Homebrew Python (ARM64)を使用: $PYTHON_BIN"
elif [ -x "/usr/bin/python3" ]; then
    PYTHON_BIN="/usr/bin/python3"
    print_warning "システムPythonを使用: $PYTHON_BIN"
else
    print_error "Python3が見つかりません"
    exit 1
fi

# Python実行ファイルのアーキテクチャ確認
PYTHON_ARCH=$(file $PYTHON_BIN | grep -o 'arm64\|x86_64' | head -1)
if [ "$PYTHON_ARCH" != "arm64" ]; then
    print_error "PythonがARM64ではありません: $PYTHON_ARCH"
    print_info "Homebrewでarm64版Pythonをインストールしてください:"
    print_info "  /opt/homebrew/bin/brew install python@3.12"
    exit 1
fi

# venv作成
$PYTHON_BIN -m venv .venv_arm64
print_success "ARM64 venv作成完了"

# 環境のアクティベート
source .venv_arm64/bin/activate

# pipのアップグレード
print_info "pipをアップグレード中..."
pip install --upgrade pip

# 基本パッケージのインストール
print_info "基本パッケージをインストール中..."
pip install wheel setuptools

# プロジェクトのインストール
print_info "プロジェクトをインストール中..."
pip install -e .

# 追加の必要なパッケージ
print_info "追加パッケージをインストール中..."
pip install streamlit reportlab aiohttp

# インストール確認
print_info "インストールされたパッケージのアーキテクチャを確認中..."
python -c "
import platform
import numpy as np
import pandas as pd
print(f'Python: {platform.machine()}')
print(f'NumPy: {np.__version__}')
print(f'Pandas: {pd.__version__}')
"

# 環境変数の設定
print_info "環境変数を設定中..."
export ARCHFLAGS="-arch arm64"

# 完了メッセージ
echo ""
print_success "ARM64ネイティブ環境のセットアップが完了しました！"
echo ""
echo "📝 使用方法:"
echo "1. 環境をアクティベート:"
echo "   source .venv_arm64/bin/activate"
echo ""
echo "2. WebUIを起動:"
echo "   python TradingMultiAgents/run_webui.py"
echo ""
echo "3. 環境確認:"
echo "   python -c \"import platform; print(f'Architecture: {platform.machine()}')\""
echo ""
print_warning "注意: 常にARM64環境（.venv_arm64）を使用してください"
print_warning "x86_64モードでの実行は避けてください"
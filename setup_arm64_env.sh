#!/bin/bash
# Setup native ARM64 environment

echo "=== ARM64ネイティブ環境のセットアップ ==="

# Use native Python
NATIVE_PYTHON="/opt/homebrew/bin/python3.12"
VENV_PATH="venv_arm64"

# Remove old venv if exists
if [ -d "$VENV_PATH" ]; then
    echo "既存の仮想環境を削除中..."
    rm -rf "$VENV_PATH"
fi

# Create new venv
echo "新しい仮想環境を作成中..."
$NATIVE_PYTHON -m venv $VENV_PATH

# Activate venv
source $VENV_PATH/bin/activate

# Verify architecture
echo -e "\nPython情報:"
which python
file $(which python)
python --version

# Install dependencies
echo -e "\n依存関係をインストール中..."

# Core dependencies
pip install --upgrade pip
pip install streamlit pydantic pandas numpy yfinance

# LangChain and AI dependencies
pip install langchain langchain-openai openai

# Async and networking
pip install aiohttp asyncio nest-asyncio

# Data processing
pip install python-dateutil pytz

# Visualization
pip install plotly matplotlib seaborn

# Testing
pip install pytest pytest-asyncio

# Additional dependencies from requirements if exists
if [ -f "requirements.txt" ]; then
    echo -e "\nrequirements.txtから追加インストール..."
    pip install -r requirements.txt
fi

echo -e "\n=== セットアップ完了 ==="
echo "仮想環境をアクティベート: source $VENV_PATH/bin/activate"
echo "WebUIを起動: python -m streamlit run run_webui.py"
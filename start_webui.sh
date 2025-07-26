#!/bin/bash
# WebUI起動スクリプト

# スクリプトのディレクトリを取得
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# TradingMultiAgentsディレクトリに移動
cd "$SCRIPT_DIR/TradingMultiAgents"

# 仮想環境をアクティベート
source "$SCRIPT_DIR/.venv/bin/activate"

# 環境を確認
echo "Python: $(which python)"
echo "Python version: $(python --version)"
echo "Current directory: $(pwd)"

# plotlyの存在確認
echo "Checking plotly installation..."
python -c "import plotly; print(f'Plotly version: {plotly.__version__}')" || {
    echo "ERROR: plotly not found. Installing..."
    pip install plotly
}

# WebUIを起動
echo "Starting WebUI..."
python run_webui.py
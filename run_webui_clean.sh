#!/bin/bash
# Clean WebUI startup script

echo "=== WebUI クリーン起動スクリプト ==="

# Kill any existing streamlit processes
pkill -f streamlit 2>/dev/null || true
echo "✓ 既存のStreamlitプロセスを終了"

# Use the conda Python explicitly
PYTHON_PATH="/usr/local/Caskroom/miniconda/base/bin/python"

# Check Python version
echo -e "\nPython環境:"
$PYTHON_PATH --version

# Check if pydantic works
echo -e "\nPydantic確認:"
$PYTHON_PATH -c "import pydantic; print(f'pydantic {pydantic.VERSION} OK')" 2>&1

# Set environment variables
export PYTHONPATH="/Users/y-sato/TradingAgents2:$PYTHONPATH"

# Start streamlit with explicit Python
echo -e "\nWebUI起動中..."
$PYTHON_PATH -m streamlit run run_webui.py --server.port 8501

echo "終了しました"
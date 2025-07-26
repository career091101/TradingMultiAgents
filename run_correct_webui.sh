#!/bin/bash
# Run the correct WebUI with backtest2 functionality

echo "=== 正しいWebUI（バックテスト2付き）を起動 ==="

# Kill any existing Streamlit processes
pkill -f streamlit 2>/dev/null || true
echo "✓ 既存のStreamlitプロセスを終了"

# Activate ARM64 virtual environment
source venv_arm64/bin/activate

# Verify Python environment
echo -e "\nPython環境確認:"
which python
python --version

# Set environment variables
export PYTHONPATH="/Users/y-sato/TradingAgents2:/Users/y-sato/TradingAgents2/TradingMultiAgents:$PYTHONPATH"

# Check if required modules are available
echo -e "\nモジュール確認:"
python -c "import pydantic; print(f'✓ pydantic {pydantic.VERSION}')" 2>&1
python -c "import streamlit; print('✓ streamlit')" 2>&1

# Navigate to correct WebUI directory
cd TradingMultiAgents

# Check if backtest2 components exist
echo -e "\nバックテスト2コンポーネント確認:"
if [ -f "webui/components/backtest2.py" ]; then
    echo "✓ backtest2.py found"
else
    echo "✗ backtest2.py not found"
fi

if [ -f "webui/backend/backtest2_wrapper.py" ]; then
    echo "✓ backtest2_wrapper.py found"
else
    echo "✗ backtest2_wrapper.py not found"
fi

# Start the correct WebUI
echo -e "\n正しいWebUIを起動中..."
echo "URL: http://localhost:8501"
echo "終了: Ctrl+C"
echo "=================="

python -m streamlit run webui/app.py --server.port 8501

cd ..
deactivate
#!/bin/bash
# Safe restart with memory cleanup and proper environment

echo "=== Cleaning up system resources ==="
# Kill any existing Python/Streamlit processes
pkill -9 -f python
pkill -9 -f streamlit
sleep 2

echo "=== Clearing Python cache ==="
find /Users/y-sato/TradingAgents2 -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
find /Users/y-sato/TradingAgents2 -name "*.pyc" -delete 2>/dev/null || true

echo "=== Setting up environment ==="
cd /Users/y-sato/TradingAgents2
source venv_arm64/bin/activate

# Load environment variables from .env file
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
    echo "✓ API keys loaded from .env file"
else
    echo "❌ Error: .env file not found"
    echo "Please create a .env file with your API keys"
    exit 1
fi

# Force Python to not use any cached modules
export PYTHONDONTWRITEBYTECODE=1
export PYTHONUNBUFFERED=1

echo "=== Starting WebUI in safe mode ==="
cd TradingMultiAgents

# Run with limited memory and debug output
ulimit -m 4194304  # Limit to 4GB memory
streamlit run webui/app.py \
    --server.maxUploadSize 50 \
    --server.maxMessageSize 50 \
    --logger.level info \
    2>&1 | tee ../webui_safe_mode.log
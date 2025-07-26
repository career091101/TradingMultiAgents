#!/bin/bash
# Clean start of WebUI without memory limits

echo "=== Starting clean WebUI session ==="
echo "Timestamp: $(date)"

# Change to project directory
cd /Users/y-sato/TradingAgents2

# Activate virtual environment
echo "=== Activating ARM64 virtual environment ==="
source venv_arm64/bin/activate

# Set environment variables
export OPENAI_API_KEY="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"
export PYTHONDONTWRITEBYTECODE=1
export PYTHONUNBUFFERED=1

# Change to TradingMultiAgents directory
cd TradingMultiAgents

# Start Streamlit with basic settings
echo "=== Starting Streamlit WebUI ==="
streamlit run webui/app.py \
    --server.port 8501 \
    --server.headless true \
    --logger.level info \
    2>&1 | tee ../webui_clean_start.log
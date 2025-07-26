#!/bin/bash
# Force kill and restart WebUI with debug logging

echo "=== Forcefully stopping all Streamlit processes ==="
pkill -9 -f streamlit
sleep 2

echo "=== Cleaning up temporary files ==="
rm -f /Users/y-sato/TradingAgents2/streamlit_debug.log
rm -f /Users/y-sato/TradingAgents2/.streamlit/cache/*

echo "=== Setting up environment ==="
source venv_arm64/bin/activate
export OPENAI_API_KEY="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"

# Set debug logging
export STREAMLIT_LOG_LEVEL=debug
export PYTHONUNBUFFERED=1

echo "=== Starting WebUI with enhanced debugging ==="
cd TradingMultiAgents

# Run with explicit debug output
python -u -m streamlit run webui/app.py \
    --server.port 8501 \
    --logger.level debug \
    --server.enableCORS false \
    --server.enableXsrfProtection false \
    2>&1 | tee ../webui_debug_output.log
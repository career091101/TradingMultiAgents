#!/bin/bash
# Run WebUI with x86_64 architecture

echo "🚀 Starting WebUI with x86_64 architecture..."

# Ensure we're using x86_64 Python
export ARCHFLAGS="-arch x86_64"
export CFLAGS="-arch x86_64"
export LDFLAGS="-arch x86_64"

# Navigate to the correct directory
cd /Users/y-sato/TradingAgents2/TradingMultiAgents

# Run Streamlit with x86_64 architecture
arch -x86_64 python -m streamlit run webui/app.py
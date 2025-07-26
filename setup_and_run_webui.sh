#!/bin/bash
# Setup environment variables and run WebUI

echo "Setting up API keys..."

# Export API keys
export OPENAI_API_KEY="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"
export FINNHUB_API_KEY="d1p1c79r01qi9vk226a0d1p1c79r01qi9vk226ag"

echo "API keys set successfully!"
echo ""
echo "Starting WebUI..."
echo "Access the WebUI at: http://localhost:8501"
echo ""
echo "Recommended settings:"
echo "- Date range: 2024-01-01 to 2024-12-31"
echo "- Tickers: AAPL, MSFT"
echo "- Initial capital: 100000"
echo "- LLM Provider: OpenAI"
echo "- Deep model: gpt-4-turbo-preview"
echo "- Fast model: gpt-3.5-turbo"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Navigate to the correct directory and run WebUI
cd /Users/y-sato/TradingAgents2/TradingMultiAgents
python run_webui.py
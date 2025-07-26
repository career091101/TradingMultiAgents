#!/bin/bash
# Run WebUI with o3/o4 models

echo "=== TradingAgents WebUI with o3/o4 Models ==="
echo ""

# Load environment variables from .env file
if [ -f ../.env ]; then
    export $(cat ../.env | grep -v '^#' | xargs)
    echo "✓ API keys loaded from .env file"
else
    echo "❌ Error: .env file not found"
    echo "Please create a .env file with your API keys"
    exit 1
fi

echo "✓ API keys configured"
echo ""
echo "=== WebUI Settings for o3/o4 Models ==="
echo ""
echo "Provider: OpenAI"
echo "Deep Model: o3-2025-04-16"
echo "Fast Model: o4-mini-2025-04-16"
echo "Temperature: 1.0 (Required for o3/o4)"
echo ""
echo "=== Recommended Configuration ==="
echo ""
echo "1. Date Range: 2024-01-01 to 2024-12-31"
echo "2. Tickers: AAPL, MSFT"
echo "3. Initial Capital: 100,000"
echo "4. Debate Rounds: 1"
echo "5. Risk Rounds: 1"
echo ""
echo "=== Known Issues ==="
echo ""
echo "- JSONシリアライズエラーが表示されますが、バックテストは継続されます"
echo "- エラーにより全ての決定がHOLDになる可能性があります"
echo "- その場合はモックモード（mock/mock）を使用してください"
echo ""
echo "WebUI URL: http://localhost:8501"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Navigate to WebUI directory
cd /Users/y-sato/TradingAgents2/TradingMultiAgents

# Run WebUI
python run_webui.py
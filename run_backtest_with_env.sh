#!/bin/bash
# Load environment variables
source ~/.bashrc

# Verify API key is set
if [ -z "$OPENAI_API_KEY" ]; then
    echo "Error: OPENAI_API_KEY not set!"
    exit 1
fi

echo "✅ OPENAI_API_KEY is set"
echo "🚀 Starting backtest with proper environment..."

# Run the backtest
python test_debug_backtest.py

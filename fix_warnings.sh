#!/bin/bash
# Fix WebUI warnings

echo "🔧 Fixing WebUI warnings..."

# 1. Install fsevents for better file watching performance (macOS only)
echo "📦 Installing fsevents..."
arch -arm64 pip install --no-cache-dir fsevents

# 2. Fix TradingMultiAgents dataflows import
echo "🔗 Creating symbolic link for tradingagents module..."
cd /Users/y-sato/TradingAgents2/backtest2
ln -sf ../TradingMultiAgents/tradingagents tradingagents 2>/dev/null || echo "Link already exists"

# 3. Optional: Install push notifications if needed
# echo "📦 Installing streamlit-push-notifications..."
# arch -arm64 pip install --no-cache-dir streamlit-push-notifications

echo "✅ Warnings fix completed!"
echo "🚀 Restart WebUI to see the changes"
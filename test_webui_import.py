#!/usr/bin/env python
"""Test script to verify WebUI can import Backtest2"""

import os
import sys

# Navigate to TradingMultiAgents directory
current_dir = os.path.dirname(os.path.abspath(__file__))
trading_agents_dir = os.path.join(current_dir, 'TradingMultiAgents')
os.chdir(trading_agents_dir)

# Add parent directory to path (contains backtest2)
sys.path.insert(0, current_dir)
# Also add TradingMultiAgents directory for webui imports
sys.path.insert(0, trading_agents_dir)

print(f"Current directory: {os.getcwd()}")
print(f"Python path (first 3): {sys.path[:3]}")

try:
    from webui.backend.backtest2_wrapper import Backtest2Wrapper
    print("✓ Successfully imported Backtest2Wrapper")
    
    # Test instantiation
    wrapper = Backtest2Wrapper()
    print("✓ Successfully instantiated Backtest2Wrapper")
    
    # Test configuration creation
    test_config = {
        "tickers": ["AAPL"],
        "start_date": "2024-01-01",
        "end_date": "2024-01-31",
        "initial_capital": 10000,
        "agent_config": {
            "llm_provider": "openai",
            "max_debate_rounds": 1,
            "max_risk_rounds": 1,
            "online_tools": False
        },
        "temperature": 0.7,
        "max_tokens": 2000,
        "use_japanese": False,
        "enable_memory": True,
        "force_refresh": False,
        "aggressive_limit": 0.3,
        "neutral_limit": 0.2,
        "conservative_limit": 0.1,
        "stop_loss": 0.1,
        "take_profit": 0.2,
        "max_positions": 5,
        "enable_reflection": True,
        "immediate_reflection": True,
        "slippage": 0.001,
        "commission": 0.001,
        "risk_free_rate": 0.02,
        "generate_plots": True
    }
    
    config = wrapper._create_backtest_config(test_config)
    print("✓ Successfully created BacktestConfig")
    print(f"  - Symbols: {config.symbols}")
    print(f"  - Time range: {config.time_range.start} to {config.time_range.end}")
    print(f"  - Initial capital: ${config.initial_capital}")
    
    print("\n✅ All imports and basic functionality working!")
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
#!/usr/bin/env python3
"""
Test backtest2 with real LLM (GPT-4 instead of o3 for testing)
"""

import asyncio
import os
import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

# Check API key
if not os.getenv("OPENAI_API_KEY"):
    print("ERROR: OPENAI_API_KEY not set")
    print("Please set: export OPENAI_API_KEY=your_key_here")
    sys.exit(1)

print("=" * 60)
print("TESTING BACKTEST2 WITH REAL LLM (GPT-4)")
print("=" * 60)

# Create config with GPT-4 instead of o3
config = {
    "tickers": ["AAPL"],
    "start_date": "2024-01-01",
    "end_date": "2024-01-02",  # Just 2 days for quick test
    "initial_capital": 100000.0,
    "llm_provider": "openai",
    "agent_settings": {
        "debate_rounds": 1,
        "risk_rounds": 1,
        "enable_memory": True,
        "enable_reflection": True
    },
    # Override agent config to use GPT-4
    "agent_config": {
        "llm_provider": "openai",
        "deep_model": "gpt-4-turbo-preview",  # Use GPT-4 instead of o3
        "fast_model": "gpt-3.5-turbo",
        "temperature": 0.7,
        "max_tokens": 2000,
        "max_debate_rounds": 1,
        "max_risk_rounds": 1,
        "use_japanese": False,
        "online_tools": False
    },
    # Relaxed risk settings
    "aggressive_limit": 0.5,
    "neutral_limit": 0.3,
    "conservative_limit": 0.2,
    "stop_loss": 0.05,
    "take_profit": 0.10,
    "max_positions": 10,
    # Force real LLM
    "use_mock": False,
    "debug": True
}

# Import and run
from TradingMultiAgents.webui.backend.backtest2_wrapper import Backtest2Wrapper

async def run_test():
    wrapper = Backtest2Wrapper()
    
    def log_callback(msg):
        print(f"[LOG] {msg}")
    
    def progress_callback(progress, status, ticker):
        print(f"[PROGRESS] {progress:.0f}% - {status} - {ticker}")
    
    try:
        results = await wrapper.run_backtest_async(
            config, 
            progress_callback=progress_callback,
            log_callback=log_callback
        )
        
        print("\n" + "=" * 60)
        print("RESULTS:")
        print("=" * 60)
        
        for ticker, result in results.items():
            print(f"\n{ticker}:")
            if isinstance(result, dict):
                metrics = result.get('metrics', {})
                agent_perf = result.get('agent_performance', {})
                print(f"  Total Trades: {metrics.get('total_trades', 0)}")
                print(f"  Total Return: {metrics.get('total_return', 0):.2%}")
                print(f"  Agent Decisions: {agent_perf.get('total_decisions', 0)}")
                
                # Print decision breakdown if available
                if 'decision_breakdown' in agent_perf:
                    print(f"  Decision Breakdown: {agent_perf['decision_breakdown']}")
                if 'trade_execution_rate' in agent_perf:
                    print(f"  Trade Execution Rate: {agent_perf['trade_execution_rate']:.2%}")
            else:
                print(f"  Result type: {type(result)}")
                
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

# Set logging
import logging
logging.basicConfig(level=logging.INFO)
logging.getLogger("backtest2").setLevel(logging.DEBUG)
logging.getLogger("backtest2.agents.llm_client").setLevel(logging.INFO)

# Run test
asyncio.run(run_test())
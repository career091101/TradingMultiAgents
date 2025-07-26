#!/usr/bin/env python3
"""
Test backtest with JSON serialization fixes applied
"""

import asyncio
import logging
from datetime import datetime
from TradingMultiAgents.webui.backend.backtest2_wrapper import Backtest2Wrapper

# Enable debug logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Reduce noise from specific loggers
logging.getLogger('urllib3').setLevel(logging.WARNING)
logging.getLogger('httpx').setLevel(logging.WARNING)

async def test_with_o3_o4():
    print("=== TESTING WITH O3/O4 MODELS (WITH FIXES) ===\n")
    
    # Create configuration with o3/o4 models
    config = {
        "tickers": ["AAPL"],
        "start_date": "2024-01-01",
        "end_date": "2024-01-10",
        "initial_capital": 100000.0,
        "debug": True,
        "agent_config": {
            "llm_provider": "openai",
            "deep_model": "o3-2025-04-16",
            "fast_model": "o4-mini-2025-04-16",
            "temperature": 1.0,  # Required for o3/o4
            "max_debate_rounds": 1,
            "max_risk_rounds": 1,
            "enable_memory": True
        }
    }
    
    # Create wrapper
    wrapper = Backtest2Wrapper()
    
    # Callbacks
    def on_progress(progress, status, ticker):
        print(f"[Progress] {progress:.1f}% - {status}")
    
    def on_log(message):
        print(f"[Log] {message}")
    
    # Run backtest
    print("Starting backtest with o3/o4 models...\n")
    try:
        results = await wrapper.run_backtest_async(
            config,
            progress_callback=on_progress,
            log_callback=on_log
        )
        
        print("\n=== RESULTS ===")
        for ticker, result in results.items():
            print(f"\n{ticker}:")
            print(f"  Final Value: ${result['final_value']:,.2f}")
            print(f"  Total Return: {result['metrics']['total_return']:.2%}")
            print(f"  Total Trades: {result['metrics']['total_trades']}")
            print(f"  Win Rate: {result['metrics']['win_rate']:.2%}")
            
            if 'agent_performance' in result:
                perf = result['agent_performance']
                print(f"  Agent Decisions: {perf.get('total_decisions', 0)}")
                print(f"  Memory Entries: {perf.get('memory_entries', 0)}")
        
        # Check if trades were executed
        total_trades = sum(r['metrics']['total_trades'] for r in results.values())
        if total_trades == 0:
            print("\n⚠️  WARNING: No trades were executed!")
            print("This indicates the JSON serialization fix may not be complete.")
        else:
            print(f"\n✅ SUCCESS: {total_trades} trades executed!")
            
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_with_o3_o4())
#!/usr/bin/env python3
"""
Run backtest with mock mode to verify logic flow
"""

import asyncio
import logging
from datetime import datetime
from TradingMultiAgents.webui.backend.backtest2_wrapper import Backtest2Wrapper

# Enable all debug logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Set specific loggers to INFO to reduce noise
logging.getLogger('urllib3').setLevel(logging.INFO)
logging.getLogger('asyncio').setLevel(logging.INFO)

async def run_mock_test():
    print("=== MOCK MODE BACKTEST TEST ===\n")
    
    # Create configuration
    config = {
        "tickers": ["AAPL"],
        "start_date": "2024-01-01",
        "end_date": "2024-01-10",
        "initial_capital": 100000.0,
        "use_mock": True,  # Enable mock mode
        "debug": True,     # Enable debug logging
        "agent_config": {
            "llm_provider": "custom",
            "deep_model": "mock",
            "fast_model": "mock",
            "max_debate_rounds": 1,
            "max_risk_rounds": 1,
            "enable_memory": True
        }
    }
    
    # Create wrapper
    wrapper = Backtest2Wrapper()
    
    # Progress callback
    def on_progress(progress, status, ticker):
        print(f"[Progress] {progress:.1f}% - {status}")
    
    # Log callback
    def on_log(message):
        print(f"[Log] {message}")
    
    # Run backtest
    print("Starting backtest...\n")
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
                print(f"  Agent Decisions: {result['agent_performance'].get('total_decisions', 0)}")
        
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(run_mock_test())
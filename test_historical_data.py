#!/usr/bin/env python3
"""
Test with proper historical dates
"""

import asyncio
from datetime import datetime
from TradingMultiAgents.webui.backend.backtest2_wrapper import Backtest2Wrapper

async def test_historical():
    print("=== TESTING WITH HISTORICAL DATA ===\n")
    
    # Use proper historical dates
    config = {
        "tickers": ["AAPL"],
        "start_date": "2024-01-01",  # Historical date
        "end_date": "2024-06-30",     # 6 months of data
        "initial_capital": 100000.0,
        "debug": True,
        "agent_config": {
            "llm_provider": "openai",
            "deep_model": "o3-2025-04-16",
            "fast_model": "o4-mini-2025-04-16",
            "temperature": 1.0,
            "max_debate_rounds": 1,
            "max_risk_rounds": 1
        }
    }
    
    wrapper = Backtest2Wrapper()
    
    def on_progress(progress, status, ticker):
        print(f"[{progress:.1f}%] {status}")
    
    def on_log(message):
        if "Return=" in message or "Error" in message or "trades" in message:
            print(f">> {message}")
    
    try:
        results = await wrapper.run_backtest_async(
            config,
            progress_callback=on_progress,
            log_callback=on_log
        )
        
        print("\n=== RESULTS ===")
        for ticker, result in results.items():
            print(f"{ticker}:")
            print(f"  Total Trades: {result['metrics']['total_trades']}")
            print(f"  Return: {result['metrics']['total_return']:.2%}")
            
            if result['metrics']['total_trades'] == 0:
                print("\n⚠️  Still no trades - checking for errors in logs")
            else:
                print(f"\n✅ SUCCESS: {result['metrics']['total_trades']} trades executed!")
                
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_historical())
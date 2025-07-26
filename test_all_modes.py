#!/usr/bin/env python3
"""
Test backtest2 in all modes to diagnose trading issues
"""

import asyncio
import os
import sys
from pathlib import Path
from datetime import datetime, timedelta
import json

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

from backtest2.core.config import BacktestConfig
from backtest2.core.engine import BacktestEngine
# Results class is returned by engine.run()

async def test_mock_mode():
    """Test 1: Mock mode with relaxed settings"""
    print("\n" + "="*60)
    print("TEST 1: MOCK MODE")
    print("="*60)
    
    config = BacktestConfig(
        tickers=["AAPL", "MSFT"],
        start_date=datetime.now() - timedelta(days=30),
        end_date=datetime.now(),
        initial_capital=100000,
        # Relaxed settings
        aggressive_limit=0.6,
        neutral_limit=0.4,
        conservative_limit=0.2,
        stop_loss=0.05,
        take_profit=0.15,
        max_positions=10,
        # Agent settings
        agent_config={
            "llm_provider": "openai",
            "use_mock": True,  # MOCK MODE
            "max_debate_rounds": 2,
            "max_risk_rounds": 1,
            "temperature": 0.7,
            "debug": True
        },
        debug=True
    )
    
    engine = BacktestEngine(config)
    results = await engine.run()
    
    print("\nMOCK MODE RESULTS:")
    for ticker, result in results.results.items():
        print(f"\n{ticker}:")
        print(f"  Total Trades: {result.metrics.total_trades}")
        print(f"  Total Return: {result.metrics.total_return:.2%}")
        print(f"  Agent Decisions: {result.agent_performance.get('total_decisions', 0)}")
        
    return results

async def test_past_dates():
    """Test 2: Real LLM with past dates"""
    print("\n" + "="*60)
    print("TEST 2: REAL LLM WITH PAST DATES (2024)")
    print("="*60)
    
    config = BacktestConfig(
        tickers=["AAPL"],
        start_date=datetime(2024, 1, 1),
        end_date=datetime(2024, 1, 31),
        initial_capital=100000,
        # Relaxed settings
        aggressive_limit=0.5,
        neutral_limit=0.3,
        conservative_limit=0.2,
        stop_loss=0.05,
        take_profit=0.10,
        # Agent settings  
        agent_config={
            "llm_provider": "openai",
            "use_mock": False,  # REAL LLM
            "deep_model": "gpt-4-turbo-preview",  # Use GPT-4 instead of o3
            "fast_model": "gpt-3.5-turbo",
            "max_debate_rounds": 1,
            "max_risk_rounds": 1,
            "temperature": 0.7,
            "debug": True
        },
        debug=True
    )
    
    engine = BacktestEngine(config)
    results = await engine.run()
    
    print("\nREAL LLM (PAST DATES) RESULTS:")
    for ticker, result in results.results.items():
        print(f"\n{ticker}:")
        print(f"  Total Trades: {result.metrics.total_trades}")
        print(f"  Total Return: {result.metrics.total_return:.2%}")
        print(f"  Agent Decisions: {result.agent_performance.get('total_decisions', 0)}")
        
    return results

async def test_single_day():
    """Test 3: Single day test with maximum debug"""
    print("\n" + "="*60)
    print("TEST 3: SINGLE DAY TEST")
    print("="*60)
    
    config = BacktestConfig(
        tickers=["AAPL"],
        start_date=datetime(2024, 1, 2),
        end_date=datetime(2024, 1, 2),  # Single day
        initial_capital=100000,
        # Very relaxed settings
        aggressive_limit=0.3,
        neutral_limit=0.2,
        conservative_limit=0.1,
        # Agent settings
        agent_config={
            "llm_provider": "openai",
            "use_mock": False,
            "deep_model": "gpt-4-turbo-preview",
            "fast_model": "gpt-3.5-turbo",
            "max_debate_rounds": 1,
            "max_risk_rounds": 1,
            "temperature": 0.9,  # Higher temperature
            "debug": True
        },
        debug=True
    )
    
    # Set debug logging
    import logging
    logging.getLogger("backtest2").setLevel(logging.DEBUG)
    
    engine = BacktestEngine(config)
    results = await engine.run()
    
    print("\nSINGLE DAY TEST RESULTS:")
    for ticker, result in results.results.items():
        print(f"\n{ticker}:")
        print(f"  Total Trades: {result.metrics.total_trades}")
        print(f"  Agent Decisions: {result.agent_performance.get('total_decisions', 0)}")
        
        # Print decision details if available
        if 'decision_breakdown' in result.agent_performance:
            print(f"  Decision Breakdown: {result.agent_performance['decision_breakdown']}")
            
    return results

async def main():
    """Run all tests"""
    print("BACKTEST2 COMPREHENSIVE TEST SUITE")
    print("Testing all modes to diagnose 0 trades issue")
    
    # Test 1: Mock mode
    try:
        mock_results = await test_mock_mode()
    except Exception as e:
        print(f"Mock mode test failed: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 2: Real LLM with past dates
    if os.getenv("OPENAI_API_KEY"):
        try:
            past_results = await test_past_dates()
        except Exception as e:
            print(f"Past dates test failed: {e}")
            import traceback
            traceback.print_exc()
    else:
        print("\nSkipping real LLM tests - OPENAI_API_KEY not set")
    
    # Test 3: Single day test
    if os.getenv("OPENAI_API_KEY"):
        try:
            single_day_results = await test_single_day()
        except Exception as e:
            print(f"Single day test failed: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "="*60)
    print("ALL TESTS COMPLETED")
    print("="*60)

if __name__ == "__main__":
    asyncio.run(main())
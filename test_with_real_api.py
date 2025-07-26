#!/usr/bin/env python3
"""
Test with real API keys
"""

import os
import asyncio
import logging
from datetime import datetime
from dotenv import load_dotenv
from backtest2.core.config import BacktestConfig
from backtest2.core.engine import BacktestEngine

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Suppress JSON serialization errors
logging.getLogger('backtest2.agents.llm_client').setLevel(logging.WARNING)

async def test_real_api():
    """Test with real OpenAI API"""
    
    # Verify API keys are loaded
    openai_key = os.getenv('OPENAI_API_KEY')
    finnhub_key = os.getenv('FINNHUB_API_KEY')
    
    print("=== API KEY CHECK ===")
    print(f"OpenAI API Key: {'✓ Set' if openai_key else '✗ Missing'}")
    print(f"Finnhub API Key: {'✓ Set' if finnhub_key else '✗ Missing'}")
    
    if not openai_key or not finnhub_key:
        print("\nError: API keys not found. Please check .env file")
        return
    
    # Create config
    config = BacktestConfig(
        symbols=["AAPL"],
        start_date=datetime(2024, 1, 1),
        end_date=datetime(2024, 1, 10),
        initial_capital=100000.0,
        debug=True
    )
    
    print("\n=== BACKTEST CONFIGURATION ===")
    print(f"Symbols: {config.symbols}")
    print(f"Date range: {config.start_date} to {config.end_date}")
    print(f"Initial capital: ${config.initial_capital:,.2f}")
    print(f"LLM models: {config.llm_config.deep_think_model} / {config.llm_config.quick_think_model}")
    
    # Create and run engine
    engine = BacktestEngine(config)
    
    # Track decisions
    decisions = []
    original_make_decision = engine.agent_orchestrator.make_decision
    
    async def track_decision(*args, **kwargs):
        result = await original_make_decision(*args, **kwargs)
        if result.action.value != 'HOLD' or result.confidence > 0:
            decisions.append({
                'date': kwargs.get('date'),
                'symbol': kwargs.get('symbol'),
                'action': result.action.value,
                'confidence': result.confidence,
                'quantity': result.quantity
            })
        return result
    
    engine.agent_orchestrator.make_decision = track_decision
    
    try:
        print("\n=== RUNNING BACKTEST ===")
        result = await engine.run()
        
        print("\n=== RESULTS ===")
        print(f"Final value: ${result.final_portfolio.total_value:,.2f}")
        print(f"Total return: {result.metrics.total_return:.2%}")
        print(f"Total trades: {result.metrics.total_trades}")
        print(f"Sharpe ratio: {result.metrics.sharpe_ratio:.2f}")
        
        print(f"\n=== TRADING DECISIONS ===")
        print(f"Total decisions with action: {len(decisions)}")
        
        if decisions:
            print("\nFirst 5 decisions:")
            for i, d in enumerate(decisions[:5]):
                print(f"{i+1}. {d['date']}: {d['action']} {d['symbol']} (confidence: {d['confidence']:.2f})")
        
        if result.transactions:
            print("\n=== TRANSACTIONS ===")
            for i, tx in enumerate(result.transactions[:5]):
                print(f"{i+1}. {tx.timestamp}: {tx.action.value} {tx.quantity:.2f} {tx.symbol} @ ${tx.price:.2f}")
        else:
            print("\n⚠️  No transactions executed - all decisions were HOLD")
            
    except Exception as e:
        print(f"\n=== ERROR ===")
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_real_api())
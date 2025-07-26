#!/usr/bin/env python
"""Test script to run backtest with debug logging enabled"""

import asyncio
import logging
from datetime import datetime, timedelta
from backtest2.core.config import BacktestConfig, AgentConfig, LLMConfig, RiskConfig, TimeRange
from backtest2.core.engine import BacktestEngine

# Configure logging to show debug messages
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('debug_backtest.log'),
        logging.StreamHandler()
    ]
)

async def run_debug_test():
    """Run a minimal backtest with debug logging"""
    print("🔍 Starting debug backtest with enhanced logging")
    print("=" * 60)
    
    # Create configuration with debug enabled
    config = BacktestConfig(
        symbols=["AAPL"],  # Single symbol for simplicity
        time_range=TimeRange(
            start=datetime.now() - timedelta(days=7),  # Last 7 days
            end=datetime.now() - timedelta(days=1)
        ),
        initial_capital=100000.0,
        debug=True,  # Enable debug mode
        agent_config=AgentConfig(
            llm_config=LLMConfig(
                deep_think_model="gpt-4",  # Use gpt-4 instead of o3
                quick_think_model="gpt-4o-mini",  # Use correct model name
                temperature=0.7
            ),
            use_japanese_prompts=True,  # Test with Japanese prompts
            max_debate_rounds=1,
            max_risk_discuss_rounds=1,
            enable_memory=True
        ),
        risk_config=RiskConfig(
            max_positions=5,
            position_limits={'AAPL': 0.5},
            stop_loss=0.1,
            take_profit=0.2
        )
    )
    
    print(f"Config: ")
    print(f"  - Symbol: {config.symbols}")
    print(f"  - Date range: {config.time_range.start} to {config.time_range.end}")
    print(f"  - Debug: {config.debug}")
    print(f"  - Japanese prompts: {config.agent_config.use_japanese_prompts}")
    print()
    
    # Create and run backtest engine
    engine = BacktestEngine(config)
    
    try:
        print("Running backtest...")
        result = await engine.run()
        
        print("\n📊 Results:")
        print(f"Total decisions: {result.agent_performance.get('total_decisions', 0)}")
        print(f"Decision breakdown:")
        breakdown = result.agent_performance.get('decision_breakdown', {})
        for action, count in breakdown.items():
            print(f"  - {action}: {count}")
        
        print(f"\nTotal trades executed: {result.agent_performance.get('total_trades', 0)}")
        
        print("\n📁 Check the following for debug info:")
        print("  1. debug_backtest.log - Full debug log")
        print("  2. logs/llm_debug/ - Raw LLM responses")
        print("  3. logs/backtest_debug_*.log - Backtest debug logs")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        logging.exception("Backtest failed")
        
    finally:
        await engine._cleanup()

if __name__ == "__main__":
    print("🚀 Debug Backtest Tool")
    print("This will help identify why all decisions are HOLD")
    print()
    
    asyncio.run(run_debug_test())
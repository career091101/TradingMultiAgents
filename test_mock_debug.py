#!/usr/bin/env python
"""Test with mock mode to check if the issue is with LLM or with the logic"""

import asyncio
import logging
from datetime import datetime, timedelta
from backtest2.core.config import BacktestConfig, AgentConfig, LLMConfig, RiskConfig, TimeRange
from backtest2.core.engine import BacktestEngine

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('mock_debug.log'),
        logging.StreamHandler()
    ]
)

async def run_mock_test():
    """Run backtest with mock agents"""
    print("🤖 Running Mock Mode Test")
    print("=" * 60)
    
    # Use mock mode
    config = BacktestConfig(
        symbols=["AAPL"],
        time_range=TimeRange(
            start=datetime.now() - timedelta(days=3),
            end=datetime.now() - timedelta(days=1)
        ),
        initial_capital=100000.0,
        debug=True,
        agent_config=AgentConfig(
            llm_config=LLMConfig(
                deep_think_model="mock",  # Use mock mode
                quick_think_model="mock",
                temperature=0.7
            ),
            use_japanese_prompts=True,
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
    
    print(f"Config: Mock mode enabled")
    print(f"  - Symbol: {config.symbols}")
    print(f"  - Date range: {config.time_range.start} to {config.time_range.end}")
    print()
    
    engine = BacktestEngine(config)
    
    try:
        print("Running mock backtest...")
        result = await engine.run()
        
        print("\n📊 Mock Mode Results:")
        print(f"Total decisions: {result.agent_performance.get('total_decisions', 0)}")
        
        breakdown = result.agent_performance.get('decision_breakdown', {})
        print(f"Decision breakdown:")
        for action, count in breakdown.items():
            print(f"  - {action}: {count}")
        
        print(f"\nTotal trades executed: {result.agent_performance.get('total_trades', 0)}")
        
        # Check if mock mode is also producing all HOLDs
        if breakdown.get('HOLD', 0) == result.agent_performance.get('total_decisions', 0):
            print("\n⚠️  WARNING: Even mock mode is producing all HOLD decisions!")
            print("This suggests the issue is in the decision logic, not the LLM.")
        else:
            print("\n✅ Mock mode produces varied decisions.")
            print("This suggests the issue is with LLM response parsing.")
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        logging.exception("Mock test failed")
        
    finally:
        await engine._cleanup()

if __name__ == "__main__":
    print("🧪 Mock Mode Test")
    print("Testing if the issue is with LLM responses or decision logic")
    print()
    
    asyncio.run(run_mock_test())
#!/usr/bin/env python3
"""
Test the fixed backtest to verify trades are being recorded
"""

import asyncio
import logging
import sys
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add project root to path
sys.path.insert(0, '/Users/y-sato/TradingAgents2')

async def test_backtest():
    """Test backtest with fixed code"""
    
    from backtest2.core.config import BacktestConfig, TimeRange, LLMConfig
    from backtest2.core.engine import BacktestEngine
    
    # Create simple config with mock agents
    config = BacktestConfig(
        name="test_fixed",
        symbols=["AAPL"],
        time_range=TimeRange(
            start=datetime(2024, 1, 1),
            end=datetime(2024, 1, 10)
        ),
        initial_capital=100000.0,
        llm_config=LLMConfig(
            deep_think_model="mock",
            quick_think_model="mock"
        )
    )
    
    logger.info("Running backtest with fixed code...")
    logger.info(f"Symbols: {config.symbols}")
    logger.info(f"Date range: {config.time_range.start} to {config.time_range.end}")
    
    # Create and run engine
    engine = BacktestEngine(config)
    result = await engine.run()
    
    # Check results
    logger.info("\n=== BACKTEST RESULTS ===")
    logger.info(f"Total decisions: {result.agent_performance.get('total_decisions', 0)}")
    logger.info(f"Total trades: {result.agent_performance.get('total_trades', 0)}")
    logger.info(f"Decision breakdown:")
    breakdown = result.agent_performance.get('decision_breakdown', {})
    for action, count in breakdown.items():
        logger.info(f"  {action}: {count}")
    logger.info(f"Trade execution rate: {result.agent_performance.get('trade_execution_rate', 0):.2%}")
    
    # Check metrics
    if result.metrics:
        logger.info(f"\nPerformance metrics:")
        logger.info(f"  Total return: {result.metrics.total_return:.2f}%")
        logger.info(f"  Total trades: {result.metrics.total_trades}")
        logger.info(f"  Win rate: {result.metrics.win_rate:.2f}%")
    
    # Verify fix worked
    if result.agent_performance.get('total_decisions', 0) > 0:
        logger.info("\n✅ SUCCESS: Decisions are now being tracked!")
    else:
        logger.error("\n❌ FAILED: Still showing 0 decisions")
    
    return result

if __name__ == "__main__":
    asyncio.run(test_backtest())
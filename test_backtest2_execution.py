#!/usr/bin/env python3
"""
Test backtest2 execution with detailed logging
"""

import logging
import sys

# Set up detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)

# Now import after logging is configured
import asyncio
from datetime import datetime, timedelta
from backtest2.core.config import BacktestConfig, LLMConfig
from backtest2.core.engine import BacktestEngine

async def test_backtest_execution():
    """Test backtest execution with detailed debugging"""
    
    logger = logging.getLogger(__name__)
    logger.info("=== Starting Backtest2 Execution Test ===")
    
    # Create config
    config = BacktestConfig(
        symbols=["AAPL"],
        start_date=datetime.now() - timedelta(days=7),  # Just 7 days for quick test
        end_date=datetime.now() - timedelta(days=1),
        initial_capital=100000,
        llm_config=LLMConfig(
            deep_think_model="mock",  # Use mock to isolate issues
            quick_think_model="mock",
            temperature=0.7,
            max_tokens=2000
        )
    )
    
    logger.info(f"Config created: symbols={config.symbols}, date_range={config.start_date} to {config.end_date}")
    
    # Create engine
    engine = BacktestEngine(config)
    logger.info("Engine created successfully")
    
    # Hook into engine methods to log execution flow
    original_process_symbol = engine._process_symbol
    async def logged_process_symbol(symbol, date):
        logger.info(f"Processing {symbol} on {date}")
        result = await original_process_symbol(symbol, date)
        logger.info(f"Finished processing {symbol} on {date}")
        return result
    engine._process_symbol = logged_process_symbol
    
    # Hook into orchestrator if it exists
    if hasattr(engine, 'agent_orchestrator') and engine.agent_orchestrator:
        orchestrator = engine.agent_orchestrator
        original_make_decision = orchestrator.make_decision
        
        async def logged_make_decision(date, symbol, market_data, portfolio):
            logger.info(f"Orchestrator making decision for {symbol} on {date}")
            logger.info(f"Portfolio state: cash={portfolio.cash if portfolio else 'None'}")
            
            try:
                decision = await original_make_decision(date, symbol, market_data, portfolio)
                logger.info(f"Decision made: action={decision.action}, quantity={decision.quantity}")
                return decision
            except Exception as e:
                logger.error(f"Decision failed: {e}")
                raise
                
        orchestrator.make_decision = logged_make_decision
    
    # Run backtest
    try:
        logger.info("Starting backtest execution...")
        result = await engine.run()
        
        logger.info("=== Backtest Results ===")
        logger.info(f"Result type: {type(result)}")
        
        if hasattr(result, 'metrics'):
            metrics = result.metrics
            logger.info(f"Total return: {getattr(metrics, 'total_return', 'N/A')}")
            logger.info(f"Total trades: {getattr(metrics, 'total_trades', 'N/A')}")
            logger.info(f"Final value: {getattr(metrics, 'final_value', 'N/A')}")
        
        if hasattr(result, 'trades'):
            logger.info(f"Number of trades executed: {len(result.trades) if result.trades else 0}")
            if result.trades:
                for i, trade in enumerate(result.trades[:5]):  # Show first 5 trades
                    logger.info(f"Trade {i+1}: {trade}")
        
        # Check if we have any daily returns
        if hasattr(result, 'daily_returns'):
            logger.info(f"Daily returns available: {len(result.daily_returns) if result.daily_returns else 0} days")
            
    except Exception as e:
        logger.error(f"Backtest failed with error: {e}", exc_info=True)
    finally:
        if hasattr(engine, 'cleanup'):
            await engine.cleanup()
        logger.info("=== Test Complete ===")

if __name__ == "__main__":
    asyncio.run(test_backtest_execution())
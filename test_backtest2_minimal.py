#!/usr/bin/env python3
"""Minimal test to identify backtest2 bottleneck"""

import asyncio
import logging
import sys
import os
from datetime import datetime, timedelta

# Add paths
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configure detailed logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)

from backtest2.core.config import BacktestConfig, LLMConfig, TimeRange
from backtest2.core.engine import BacktestEngine


async def test_single_day():
    """Test backtest2 with single day to isolate issues"""
    logger = logging.getLogger(__name__)
    
    # Single day configuration
    config = BacktestConfig(
        name="single_day_test",
        symbols=["AAPL"],
        initial_capital=10000,
        time_range=TimeRange(
            start=datetime(2024, 1, 2),
            end=datetime(2024, 1, 3)  # Two days for single day test
        ),
        llm_config=LLMConfig(
            deep_think_model="mock",  # Use mock for isolation
            quick_think_model="mock",
            timeout=60,  # 1 minute timeout
            temperature=0.0
        ),
        debug=True
    )
    
    engine = BacktestEngine(config)
    
    try:
        logger.info("Starting single day backtest...")
        start_time = asyncio.get_event_loop().time()
        
        # Run with overall timeout
        result = await asyncio.wait_for(engine.run(), timeout=120.0)  # 2 minute overall timeout
        
        elapsed = asyncio.get_event_loop().time() - start_time
        logger.info(f"Backtest completed in {elapsed:.2f} seconds")
        
        # Print results
        if result:
            logger.info(f"Total return: {result.metrics.total_return:.2%}")
            logger.info(f"Number of trades: {result.metrics.total_trades}")
            logger.info(f"Win rate: {result.metrics.win_rate:.2%}")
        
        return result
        
    except asyncio.TimeoutError:
        elapsed = asyncio.get_event_loop().time() - start_time
        logger.error(f"Backtest timed out after {elapsed:.2f} seconds")
        
        # Check decision count
        if hasattr(engine, 'all_decisions'):
            logger.info(f"Decisions made before timeout: {len(engine.all_decisions)}")
            
    except Exception as e:
        logger.error(f"Backtest failed: {e}", exc_info=True)
        
    finally:
        # Cleanup
        if hasattr(engine, '_cleanup'):
            await engine._cleanup()


async def test_phase_by_phase():
    """Test each phase individually"""
    logger = logging.getLogger(__name__)
    
    from backtest2.core.config import BacktestConfig, LLMConfig
    from backtest2.agents.orchestrator import AgentOrchestrator
    from backtest2.memory import MemoryStore
    from backtest2.core.types import MarketData, PortfolioState, DecisionContext
    
    # Create minimal config
    config = BacktestConfig(
        symbols=["AAPL"],
        initial_capital=10000,
        llm_config=LLMConfig(
            deep_think_model="mock",
            quick_think_model="mock",
            timeout=30
        )
    )
    
    # Create components
    memory_store = MemoryStore(None)
    orchestrator = AgentOrchestrator(config, memory_store)
    
    # Initialize
    await orchestrator.initialize()
    
    # Test data
    market_data = MarketData(
        symbol="AAPL",
        open=190.0,
        high=195.0,
        low=189.0,
        close=194.0,
        volume=1000000,
        indicators={},
        news=[]
    )
    
    portfolio = PortfolioState(
        timestamp=datetime.now(),
        cash=10000.0,
        positions={},
        total_value=10000.0,
        unrealized_pnl=0.0,
        realized_pnl=0.0,
        exposure=0.0,
        position_count=0
    )
    
    context = DecisionContext(
        timestamp=datetime.now(),
        market_state={'symbol': 'AAPL', 'data': market_data},
        portfolio_state=portfolio,
        recent_performance={},
        risk_metrics={}
    )
    
    # Test each phase with timing
    phases = [
        ("Data Collection", orchestrator._data_collection_phase, (market_data, context)),
        ("Investment Analysis", orchestrator._investment_analysis_phase, None),  # Will be set after phase 1
        ("Investment Decision", orchestrator._investment_decision_phase, None),
        ("Trading Decision", orchestrator._trading_decision_phase, None),
        ("Risk Assessment", orchestrator._risk_assessment_phase, None),
        ("Final Decision", orchestrator._final_decision_phase, None)
    ]
    
    results = {}
    
    for phase_name, phase_func, args in phases:
        try:
            logger.info(f"\nTesting {phase_name}...")
            start_time = asyncio.get_event_loop().time()
            
            # Prepare arguments based on previous phase results
            if phase_name == "Investment Analysis" and "Data Collection" in results:
                args = (results["Data Collection"], context)
            elif phase_name == "Investment Decision" and "Investment Analysis" in results:
                args = (results["Investment Analysis"], context)
            elif phase_name == "Trading Decision" and "Investment Decision" in results:
                args = (results["Investment Decision"], portfolio, context)
            elif phase_name == "Risk Assessment" and "Trading Decision" in results:
                args = (results["Trading Decision"], portfolio, context)
            elif phase_name == "Final Decision" and "Risk Assessment" in results:
                args = (results["Risk Assessment"], context)
                
            if args is None:
                logger.warning(f"Skipping {phase_name} - missing prerequisites")
                continue
                
            # Run phase with timeout
            result = await asyncio.wait_for(phase_func(*args), timeout=30.0)
            
            elapsed = asyncio.get_event_loop().time() - start_time
            logger.info(f"{phase_name} completed in {elapsed:.2f} seconds")
            
            results[phase_name] = result
            
        except asyncio.TimeoutError:
            logger.error(f"{phase_name} timed out!")
            break
        except Exception as e:
            logger.error(f"{phase_name} failed: {e}")
            break
            
    # Cleanup
    await orchestrator.cleanup()
    
    return results


if __name__ == "__main__":
    print("Testing Backtest2 minimal scenarios...")
    print("=" * 60)
    
    # Test 1: Single day full backtest
    print("\n1. Testing single day backtest...")
    asyncio.run(test_single_day())
    
    # Test 2: Phase by phase
    print("\n2. Testing phase by phase...")
    asyncio.run(test_phase_by_phase())
    
    print("\nTests completed.")
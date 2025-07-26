#!/usr/bin/env python3
"""Debug script to investigate backtest2 timeout issues"""

import asyncio
import logging
from datetime import datetime, timedelta
import os
import sys

# Add backtest2 to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backtest2.core.config import BacktestConfig, LLMConfig, TimeRange
from backtest2.core.engine import BacktestEngine


async def test_data_collection_timeout():
    """Test specifically the data collection phase with timeout tracking"""
    
    # Configure detailed logging
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('backtest2_timeout_debug.log')
        ]
    )
    
    logger = logging.getLogger(__name__)
    logger.info("Starting timeout debug test")
    
    # Create configuration with mock LLM to isolate agent logic
    config = BacktestConfig(
        name="timeout_debug_test",
        symbols=["AAPL"],
        initial_capital=10000,
        time_range=TimeRange(
            start=datetime(2024, 1, 1),
            end=datetime(2024, 1, 3)  # Just 3 days
        ),
        llm_config=LLMConfig(
            deep_think_model="mock",  # Use mock to isolate timeout issues
            quick_think_model="mock",
            timeout=10,  # Short timeout for testing
            temperature=0.0
        ),
        debug=True  # Enable debug mode
    )
    
    # Create engine
    engine = BacktestEngine(config)
    
    try:
        # Initialize engine
        logger.info("Initializing engine...")
        await engine._initialize()
        logger.info("Engine initialized successfully")
        
        # Test the orchestrator directly
        orchestrator = engine.agent_orchestrator
        if orchestrator:
            logger.info("Testing orchestrator data collection phase...")
            
            # Create minimal test data
            from backtest2.core.types import MarketData, PortfolioState, DecisionContext
            
            test_market_data = MarketData(
                timestamp=datetime(2024, 1, 2),
                symbol="AAPL",
                open=190.0,
                high=195.0,
                low=189.0,
                close=194.0,
                volume=1000000,
                indicators={},
                news=[]
            )
            
            test_portfolio = PortfolioState(
                timestamp=datetime(2024, 1, 2),
                cash=10000.0,
                positions={},
                total_value=10000.0,
                unrealized_pnl=0.0,
                realized_pnl=0.0,
                exposure=0.0,
                position_count=0
            )
            
            # Create context
            context = DecisionContext(
                timestamp=datetime(2024, 1, 2),
                market_state={'symbol': 'AAPL', 'data': test_market_data},
                portfolio_state=test_portfolio,
                recent_performance={},
                risk_metrics={}
            )
            
            # Test data collection phase with timeout
            start_time = asyncio.get_event_loop().time()
            try:
                logger.info("Starting data collection phase...")
                reports = await asyncio.wait_for(
                    orchestrator._data_collection_phase(test_market_data, context),
                    timeout=30.0  # 30 second timeout
                )
                elapsed = asyncio.get_event_loop().time() - start_time
                logger.info(f"Data collection completed in {elapsed:.2f} seconds")
                logger.info(f"Reports received: {list(reports.keys())}")
                
                # Check each report
                for name, report in reports.items():
                    logger.info(f"{name}: confidence={getattr(report, 'confidence', 'N/A')}, "
                              f"has_content={hasattr(report, 'content')}")
                    
            except asyncio.TimeoutError:
                elapsed = asyncio.get_event_loop().time() - start_time
                logger.error(f"Data collection phase timed out after {elapsed:.2f} seconds!")
                
                # Check which agents might be hanging
                for agent_name, agent in orchestrator.agents.items():
                    logger.error(f"Agent {agent_name}: type={type(agent).__name__}")
                    
        else:
            logger.error("No orchestrator found!")
            
    except Exception as e:
        logger.error(f"Test failed with error: {e}", exc_info=True)
        
    finally:
        # Cleanup
        logger.info("Cleaning up...")
        if hasattr(engine, 'cleanup'):
            await engine.cleanup()
        logger.info("Cleanup completed")


async def test_llm_client_timeout():
    """Test LLM client timeout handling"""
    logger = logging.getLogger(__name__)
    
    from backtest2.agents.llm_client import OpenAILLMClient
    from backtest2.core.config import LLMConfig
    
    # Test with real API (if available) with very short timeout
    config = LLMConfig(
        deep_think_model="gpt-4o-mini",
        quick_think_model="gpt-4o-mini",
        timeout=5,  # 5 second timeout
        temperature=0.0
    )
    
    client = OpenAILLMClient(config)
    
    # Test basic generation
    try:
        logger.info("Testing LLM client with short timeout...")
        start_time = asyncio.get_event_loop().time()
        
        result = await asyncio.wait_for(
            client.generate(
                prompt="Analyze this stock: AAPL",
                context={"test": "data"},
                use_deep_thinking=False,
                agent_name="test_agent"
            ),
            timeout=10.0
        )
        
        elapsed = asyncio.get_event_loop().time() - start_time
        logger.info(f"LLM response received in {elapsed:.2f} seconds")
        logger.info(f"Response length: {len(result)} chars")
        
    except asyncio.TimeoutError:
        elapsed = asyncio.get_event_loop().time() - start_time
        logger.error(f"LLM client timed out after {elapsed:.2f} seconds")
    except Exception as e:
        logger.error(f"LLM client error: {e}")
        
    finally:
        await client.cleanup()


if __name__ == "__main__":
    print("Testing backtest2 timeout issues...")
    print("=" * 60)
    
    # Test data collection phase
    print("\n1. Testing data collection phase timeout...")
    asyncio.run(test_data_collection_timeout())
    
    # Test LLM client if API key is available
    if os.getenv("OPENAI_API_KEY"):
        print("\n2. Testing LLM client timeout...")
        asyncio.run(test_llm_client_timeout())
    else:
        print("\n2. Skipping LLM client test (no API key)")
    
    print("\nTest completed. Check backtest2_timeout_debug.log for details.")
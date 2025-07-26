#!/usr/bin/env python3
"""Test backtest2 with fixed model settings"""

import asyncio
import logging
import sys
import os
from datetime import datetime, timedelta

# Add paths
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)

from TradingMultiAgents.webui.backend.backtest2_wrapper import Backtest2Wrapper


async def test_webui_with_fast_models():
    """Test backtest2 with fast models and proper timeout"""
    logger = logging.getLogger(__name__)
    
    # Create wrapper
    wrapper = Backtest2Wrapper()
    
    # Configuration with fast models
    config = {
        "name": "fast_model_test",
        "symbols": ["AAPL"],
        "start_date": (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d"),
        "end_date": (datetime.now() - timedelta(days=5)).strftime("%Y-%m-%d"),
        "initial_capital": 10000,
        "agent_config": {
            "llm_provider": "openai",
            "deep_model": "gpt-4o-mini",  # Use fast model for all agents
            "fast_model": "gpt-4o-mini",
            "max_debate_rounds": 1,
            "max_risk_rounds": 1
        },
        "temperature": 0.0,
        "max_tokens": 1000,  # Limit tokens for faster response
        "timeout": 60,  # 1 minute timeout
        "debug": True
    }
    
    logger.info(f"Starting test with fast models: {config}")
    
    # Track phases
    phase_times = {}
    last_phase = None
    start_time = asyncio.get_event_loop().time()
    
    # Progress callback
    def progress_callback(progress, status, phase=None):
        nonlocal last_phase
        current_time = asyncio.get_event_loop().time()
        
        if phase and phase != last_phase:
            if last_phase:
                phase_times[last_phase] = current_time - phase_times.get(last_phase, start_time)
            phase_times[phase] = current_time
            last_phase = phase
            
        logger.info(f"Progress: {progress}% - Status: {status} - Phase: {phase}")
    
    try:
        # Run backtest with timeout
        result = await asyncio.wait_for(
            wrapper.run_backtest_async(config, progress_callback),
            timeout=180.0  # 3 minute overall timeout
        )
        
        total_time = asyncio.get_event_loop().time() - start_time
        logger.info(f"\nBacktest completed in {total_time:.2f} seconds")
        
        # Log phase times
        logger.info("\nPhase execution times:")
        for phase, time in phase_times.items():
            logger.info(f"  {phase}: {time:.2f} seconds")
            
        # Check result
        if result.get("success"):
            logger.info("\nBacktest succeeded!")
            metrics = result.get('metrics', {})
            logger.info(f"Total return: {metrics.get('total_return', 'N/A')}")
            logger.info(f"Number of trades: {metrics.get('total_trades', 'N/A')}")
            logger.info(f"Win rate: {metrics.get('win_rate', 'N/A')}")
        else:
            logger.error(f"\nBacktest failed: {result.get('error', 'Unknown error')}")
            
    except asyncio.TimeoutError:
        elapsed = asyncio.get_event_loop().time() - start_time
        logger.error(f"\nBacktest timed out after {elapsed:.2f} seconds")
        logger.info("\nPhase times before timeout:")
        for phase, time in phase_times.items():
            logger.info(f"  {phase}: {time:.2f} seconds")
    except Exception as e:
        logger.error(f"\nTest failed with error: {e}", exc_info=True)


async def test_mock_mode_performance():
    """Test performance in mock mode as baseline"""
    logger = logging.getLogger(__name__)
    
    wrapper = Backtest2Wrapper()
    
    config = {
        "name": "mock_performance_test",
        "symbols": ["AAPL", "GOOGL", "MSFT"],  # Multiple symbols
        "start_date": (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d"),
        "end_date": (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d"),
        "initial_capital": 100000,
        "use_mock": True,  # Use mock mode
        "debug": True
    }
    
    logger.info("Testing mock mode performance...")
    start_time = asyncio.get_event_loop().time()
    
    def progress_callback(progress, status, phase=None):
        if progress % 10 == 0:  # Log every 10%
            logger.info(f"Progress: {progress}% - {phase or status}")
    
    try:
        result = await wrapper.run_backtest_async(config, progress_callback)
        elapsed = asyncio.get_event_loop().time() - start_time
        
        logger.info(f"\nMock mode completed in {elapsed:.2f} seconds")
        if result.get("success"):
            logger.info(f"Processed {len(config['symbols'])} symbols over {30} days")
            logger.info(f"Average time per symbol-day: {elapsed / (len(config['symbols']) * 30):.3f} seconds")
    except Exception as e:
        logger.error(f"Mock mode test failed: {e}")


if __name__ == "__main__":
    print("Testing Backtest2 with fixed model settings...")
    print("=" * 60)
    
    # Only run real LLM test if API key is available
    if os.getenv("OPENAI_API_KEY"):
        print("\n1. Testing with fast models (gpt-4o-mini)...")
        asyncio.run(test_webui_with_fast_models())
    else:
        print("\n1. Skipping real LLM test (no API key)")
    
    # Always test mock mode
    print("\n2. Testing mock mode performance...")
    asyncio.run(test_mock_mode_performance())
    
    print("\nTests completed.")
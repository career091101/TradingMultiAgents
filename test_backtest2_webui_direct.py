#!/usr/bin/env python3
"""Test backtest2 directly through WebUI wrapper to debug timeout"""

import asyncio
import logging
import sys
import os
from datetime import datetime, timedelta

# Add paths
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configure detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('backtest2_webui_debug.log')
    ]
)

# Import WebUI wrapper
from TradingMultiAgents.webui.backend.backtest2_wrapper import Backtest2Wrapper


async def test_webui_backtest2():
    """Test backtest2 through WebUI wrapper"""
    logger = logging.getLogger(__name__)
    
    # Create wrapper
    wrapper = Backtest2Wrapper()
    
    # Create minimal config - using mock mode for faster testing
    config = {
        "name": "debug_test",
        "symbols": ["AAPL"],
        "start_date": (datetime.now() - timedelta(days=10)).strftime("%Y-%m-%d"),
        "end_date": (datetime.now() - timedelta(days=8)).strftime("%Y-%m-%d"),
        "initial_capital": 10000,
        "llm_config": {
            "deep_think_model": "mock",
            "quick_think_model": "mock",
            "timeout": 30,  # 30 seconds
            "temperature": 0.0
        },
        "debug": True
    }
    
    logger.info(f"Starting test with config: {config}")
    
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
        # Run backtest
        logger.info("Starting backtest...")
        result = await wrapper.run_backtest_async(config, progress_callback)
        
        total_time = asyncio.get_event_loop().time() - start_time
        logger.info(f"Backtest completed in {total_time:.2f} seconds")
        
        # Log phase times
        logger.info("Phase execution times:")
        for phase, time in phase_times.items():
            logger.info(f"  {phase}: {time:.2f} seconds")
            
        # Check result
        if result.get("success"):
            logger.info("Backtest succeeded!")
            logger.info(f"Total return: {result.get('metrics', {}).get('total_return', 'N/A')}")
        else:
            logger.error(f"Backtest failed: {result.get('error', 'Unknown error')}")
            
    except asyncio.TimeoutError:
        logger.error("Backtest timed out!")
    except Exception as e:
        logger.error(f"Test failed with error: {e}", exc_info=True)


async def test_data_source():
    """Test data source directly"""
    logger = logging.getLogger(__name__)
    
    from backtest2.data import DataManager
    from backtest2.core.config import BacktestConfig, TimeRange
    
    config = BacktestConfig(
        symbols=["AAPL"],
        time_range=TimeRange(
            start=datetime.now() - timedelta(days=10),
            end=datetime.now() - timedelta(days=8)
        ),
        initial_capital=10000
    )
    
    data_manager = DataManager(config)
    
    try:
        logger.info("Testing data source...")
        await data_manager.initialize()
        
        # Get data for a specific date
        test_date = datetime.now() - timedelta(days=9)
        data = await data_manager.get_data("AAPL", test_date)
        
        if data:
            logger.info(f"Data retrieved: {data.symbol}")
            logger.info(f"Price: ${data.close:.2f}, Volume: {data.volume}")
        else:
            logger.warning("No data retrieved")
            
    except Exception as e:
        logger.error(f"Data source test failed: {e}", exc_info=True)


if __name__ == "__main__":
    print("Testing Backtest2 through WebUI wrapper...")
    print("=" * 60)
    
    # Test data source first
    print("\n1. Testing data source...")
    asyncio.run(test_data_source())
    
    # Test WebUI wrapper
    print("\n2. Testing WebUI wrapper...")
    asyncio.run(test_webui_backtest2())
    
    print("\nTest completed. Check backtest2_webui_debug.log for details.")
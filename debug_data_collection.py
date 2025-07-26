#!/usr/bin/env python3
"""
Debug script to trace data collection phase issues
"""

import asyncio
import logging
import sys
import os
from pathlib import Path
from datetime import datetime
import time

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

# Setup detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Set specific loggers to DEBUG
loggers = [
    "backtest2",
    "backtest2.agents.orchestrator",
    "backtest2.agents.llm_client",
    "backtest2.agents.analysts",
    "langchain",
    "openai"
]

for logger_name in loggers:
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.DEBUG)

# Import after logging setup
from TradingMultiAgents.webui.backend.backtest2_wrapper import Backtest2Wrapper

async def test_data_collection():
    """Test data collection phase with detailed debugging"""
    
    print("="*60)
    print("DEBUGGING DATA COLLECTION PHASE")
    print("="*60)
    
    # Simple config for one ticker, one day
    config = {
        "tickers": ["AAPL"],
        "start_date": "2024-01-02",
        "end_date": "2024-01-03",  # Must be after start date
        "initial_capital": 100000.0,
        "llm_provider": "openai",
        "agent_settings": {
            "debate_rounds": 1,
            "risk_rounds": 1,
            "enable_memory": False,  # Disable to simplify
            "enable_reflection": False
        },
        "agent_config": {
            "llm_provider": "openai",
            "deep_model": "gpt-4-turbo-preview",  # Valid model
            "fast_model": "gpt-3.5-turbo",      # Valid model
            "temperature": 0.7,
            "max_tokens": 500,  # Reduced for faster response
            "timeout": 15,      # Short timeout
            "max_debate_rounds": 1,
            "max_risk_rounds": 1,
            "use_japanese": False,
            "online_tools": False
        },
        "debug": True,
        "use_mock": False  # Use real LLM
    }
    
    # Check API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("\n[WARNING] OPENAI_API_KEY not set - will use mock mode")
        config["use_mock"] = True
    else:
        print(f"\n[OK] API key found: {api_key[:8]}...")
    
    wrapper = Backtest2Wrapper()
    
    # Track phases
    phase_times = {}
    current_phase = None
    
    def log_callback(msg):
        nonlocal current_phase
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        print(f"[{timestamp}] {msg}")
        
        # Track phase transitions
        if "Phase" in msg:
            if current_phase:
                phase_times[current_phase] = time.time() - phase_times.get(current_phase, time.time())
            current_phase = msg
            phase_times[current_phase] = time.time()
    
    def progress_callback(progress, status, ticker):
        print(f"[PROGRESS] {progress:.0f}% - {status} - {ticker}")
    
    try:
        print("\nStarting backtest...")
        start_time = time.time()
        
        # Run with timeout
        results = await asyncio.wait_for(
            wrapper.run_backtest_async(
                config, 
                progress_callback=progress_callback,
                log_callback=log_callback
            ),
            timeout=60  # 60 second overall timeout
        )
        
        end_time = time.time()
        
        print("\n" + "="*60)
        print("RESULTS:")
        print("="*60)
        print(f"Total time: {end_time - start_time:.2f} seconds")
        
        # Print phase timings
        print("\nPhase timings:")
        for phase, duration in phase_times.items():
            if isinstance(duration, float) and duration < 1000:  # Completed phases
                print(f"  {phase}: {duration:.2f}s")
        
        # Print results
        for ticker, result in results.items():
            print(f"\n{ticker}:")
            if isinstance(result, dict):
                agent_perf = result.get('agent_performance', {})
                print(f"  Agent Decisions: {agent_perf.get('total_decisions', 0)}")
                
    except asyncio.TimeoutError:
        print("\n[ERROR] Backtest timed out after 60 seconds")
        print("\nPhase when timeout occurred:")
        if current_phase:
            print(f"  {current_phase}")
            elapsed = time.time() - phase_times.get(current_phase, time.time())
            print(f"  Time in phase: {elapsed:.2f}s")
            
    except Exception as e:
        print(f"\n[ERROR] {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

async def test_individual_analyst():
    """Test individual analyst to isolate the issue"""
    print("\n" + "="*60)
    print("TESTING INDIVIDUAL ANALYST")
    print("="*60)
    
    # Import necessary modules
    from backtest2.agents.analysts import MarketAnalyst
    from backtest2.agents.llm_client import OpenAILLMClient
    from backtest2.core.config import LLMConfig
    from backtest2.core.types import MarketData
    
    # Create LLM client with short timeout
    llm_config = LLMConfig(
        deep_think_model="gpt-3.5-turbo",  # Use fast model for test
        quick_think_model="gpt-3.5-turbo",
        temperature=0.7,
        max_tokens=200,
        timeout=10  # 10 second timeout
    )
    
    # Check if using mock
    is_mock = not os.getenv("OPENAI_API_KEY")
    if is_mock:
        print("[INFO] Using mock LLM client")
    
    llm_client = OpenAILLMClient(llm_config, is_mock=is_mock)
    
    # Create analyst
    analyst = MarketAnalyst("market_analyst", llm_client)
    
    # Create test market data
    market_data = MarketData(
        date=datetime(2024, 1, 2),
        symbol="AAPL",
        open=185.0,
        high=186.0,
        low=184.0,
        close=185.5,
        volume=50000000,
        adjusted_close=185.5
    )
    
    # Test analyst
    try:
        print("\nCalling market analyst...")
        start = time.time()
        
        result = await asyncio.wait_for(
            analyst.process({
                'market_data': market_data,
                'context': {'symbol': 'AAPL'}
            }),
            timeout=15
        )
        
        elapsed = time.time() - start
        print(f"\nAnalyst completed in {elapsed:.2f}s")
        print(f"Result type: {type(result)}")
        if hasattr(result, 'content'):
            print(f"Content: {result.content}")
            
    except asyncio.TimeoutError:
        print(f"\n[ERROR] Analyst timed out after 15 seconds")
    except Exception as e:
        print(f"\n[ERROR] Analyst failed: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

async def main():
    """Run all debug tests"""
    
    # Test 1: Full backtest with debugging
    await test_data_collection()
    
    # Test 2: Individual analyst
    await test_individual_analyst()

if __name__ == "__main__":
    print("Starting debug session...")
    print(f"Python: {sys.version}")
    print(f"Working directory: {os.getcwd()}")
    print(f"OPENAI_API_KEY set: {'Yes' if os.getenv('OPENAI_API_KEY') else 'No'}")
    
    asyncio.run(main())
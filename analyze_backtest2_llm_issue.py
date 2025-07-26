#!/usr/bin/env python3
"""Analyze the LLM timeout issue in backtest2"""

import os
import asyncio
import logging
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)

logger = logging.getLogger(__name__)


async def test_llm_timeout():
    """Test LLM with actual API to understand timeout behavior"""
    
    if not os.getenv("OPENAI_API_KEY"):
        logger.warning("No OpenAI API key found. Skipping LLM test.")
        return
        
    from backtest2.agents.llm_client import OpenAILLMClient
    from backtest2.core.config import LLMConfig
    
    # Test with different configurations
    configs = [
        {
            "name": "Fast model with short timeout",
            "config": LLMConfig(
                deep_think_model="gpt-4o-mini",
                quick_think_model="gpt-4o-mini",
                timeout=10,  # 10 seconds
                temperature=0.0
            )
        },
        {
            "name": "Fast model with medium timeout",
            "config": LLMConfig(
                deep_think_model="gpt-4o-mini",
                quick_think_model="gpt-4o-mini",
                timeout=30,  # 30 seconds
                temperature=0.0
            )
        },
        {
            "name": "Deep think model (o1-preview)",
            "config": LLMConfig(
                deep_think_model="o1-preview",
                quick_think_model="gpt-4o-mini",
                timeout=120,  # 2 minutes for o1
                temperature=0.0
            )
        }
    ]
    
    for test_config in configs:
        logger.info(f"\nTesting: {test_config['name']}")
        client = OpenAILLMClient(test_config['config'])
        
        # Test quick thinking
        try:
            start_time = asyncio.get_event_loop().time()
            result = await client.generate(
                prompt="Analyze this stock briefly: AAPL at $190",
                context={"test": "quick"},
                use_deep_thinking=False,
                agent_name="test_quick"
            )
            elapsed = asyncio.get_event_loop().time() - start_time
            logger.info(f"Quick think completed in {elapsed:.2f}s - Response length: {len(result)}")
        except Exception as e:
            logger.error(f"Quick think failed: {e}")
            
        # Test deep thinking (if using o1)
        if "o1" in test_config['config'].deep_think_model:
            try:
                start_time = asyncio.get_event_loop().time()
                result = await client.generate(
                    prompt="Provide detailed investment analysis for AAPL",
                    context={"test": "deep"},
                    use_deep_thinking=True,
                    agent_name="test_deep"
                )
                elapsed = asyncio.get_event_loop().time() - start_time
                logger.info(f"Deep think completed in {elapsed:.2f}s - Response length: {len(result)}")
            except Exception as e:
                logger.error(f"Deep think failed: {e}")
                
        await client.cleanup()


async def analyze_phase_timing():
    """Analyze timing of each phase with real LLM"""
    
    if not os.getenv("OPENAI_API_KEY"):
        logger.warning("No OpenAI API key found. Skipping phase timing analysis.")
        return
        
    from backtest2.core.config import BacktestConfig, LLMConfig, TimeRange
    from backtest2.core.engine import BacktestEngine
    
    # Use fast model for testing
    config = BacktestConfig(
        name="timing_test",
        symbols=["AAPL"],
        initial_capital=10000,
        time_range=TimeRange(
            start=datetime(2024, 1, 2),
            end=datetime(2024, 1, 3)  # Single day
        ),
        llm_config=LLMConfig(
            deep_think_model="gpt-4o-mini",  # Fast model for testing
            quick_think_model="gpt-4o-mini",
            timeout=30,  # 30 seconds per call
            temperature=0.0,
            max_tokens=500  # Limit tokens for faster response
        ),
        debug=True
    )
    
    engine = BacktestEngine(config)
    
    # Add custom logging to track phases
    original_make_decision = engine.agent_orchestrator.make_decision
    
    phase_times = {}
    
    async def logged_make_decision(*args, **kwargs):
        decision_start = asyncio.get_event_loop().time()
        phase_times.clear()
        
        # Patch phase methods to log timing
        orchestrator = engine.agent_orchestrator
        
        # Wrap each phase method
        for phase_name, method_name in [
            ("Data Collection", "_data_collection_phase"),
            ("Investment Analysis", "_investment_analysis_phase"),
            ("Investment Decision", "_investment_decision_phase"),
            ("Trading Decision", "_trading_decision_phase"),
            ("Risk Assessment", "_risk_assessment_phase"),
            ("Final Decision", "_final_decision_phase")
        ]:
            original_method = getattr(orchestrator, method_name)
            
            async def timed_method(*a, **kw):
                phase_start = asyncio.get_event_loop().time()
                logger.info(f"Starting {phase_name}...")
                try:
                    result = await original_method(*a, **kw)
                    elapsed = asyncio.get_event_loop().time() - phase_start
                    phase_times[phase_name] = elapsed
                    logger.info(f"{phase_name} completed in {elapsed:.2f}s")
                    return result
                except Exception as e:
                    elapsed = asyncio.get_event_loop().time() - phase_start
                    logger.error(f"{phase_name} failed after {elapsed:.2f}s: {e}")
                    raise
                    
            # Bind the phase name to the closure
            timed_method = timed_method.__get__(orchestrator, type(orchestrator))
            setattr(orchestrator, method_name, timed_method)
        
        # Call original method
        result = await original_make_decision(*args, **kwargs)
        
        total_time = asyncio.get_event_loop().time() - decision_start
        logger.info(f"\nDecision completed in {total_time:.2f}s")
        logger.info("Phase breakdown:")
        for phase, time in phase_times.items():
            logger.info(f"  {phase}: {time:.2f}s ({time/total_time*100:.1f}%)")
            
        return result
        
    engine.agent_orchestrator.make_decision = logged_make_decision
    
    try:
        logger.info("Starting backtest with phase timing...")
        result = await asyncio.wait_for(engine.run(), timeout=300.0)  # 5 minute timeout
        logger.info("Backtest completed successfully!")
    except asyncio.TimeoutError:
        logger.error("Backtest timed out after 5 minutes")
    except Exception as e:
        logger.error(f"Backtest failed: {e}", exc_info=True)


if __name__ == "__main__":
    print("Analyzing Backtest2 LLM timeout issue...")
    print("=" * 60)
    
    # Test 1: LLM timeout behavior
    print("\n1. Testing LLM timeout behavior...")
    asyncio.run(test_llm_timeout())
    
    # Test 2: Phase timing analysis
    print("\n2. Analyzing phase timing with real LLM...")
    asyncio.run(analyze_phase_timing())
    
    print("\nAnalysis completed.")
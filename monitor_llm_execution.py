#!/usr/bin/env python3
"""
Monitor LLM execution in real-time
"""

import asyncio
import logging
from datetime import datetime
from backtest2.core.config import BacktestConfig, LLMConfig, AgentConfig, TimeRange
from backtest2.core.engine import BacktestEngine

# Setup detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/llm_execution.log'),
        logging.StreamHandler()
    ]
)

# Patch the llm_client to log all responses
from backtest2.agents import llm_client

original_generate = llm_client.OpenAILLMClient.generate

async def logged_generate(self, prompt, context, **kwargs):
    """Wrapper to log LLM interactions"""
    logger = logging.getLogger("LLM_MONITOR")
    
    agent_name = kwargs.get('agent_name', 'unknown')
    logger.info(f"\n{'='*60}")
    logger.info(f"Agent: {agent_name}")
    logger.info(f"Prompt length: {len(prompt)} chars")
    logger.info(f"Context keys: {list(context.keys()) if isinstance(context, dict) else 'non-dict'}")
    
    try:
        response = await original_generate(self, prompt, context, **kwargs)
        logger.info(f"Response preview: {response[:200]}...")
        logger.info(f"Response length: {len(response)} chars")
        return response
    except Exception as e:
        logger.error(f"LLM Error: {type(e).__name__}: {e}")
        raise

llm_client.OpenAILLMClient.generate = logged_generate

async def test_real_llm():
    """Test with real LLM configuration"""
    
    print("=== Testing Real LLM Mode ===\n")
    
    # Create config with real LLM
    llm_config = LLMConfig(
        deep_think_model="gpt-4",  # Change to your actual model
        quick_think_model="gpt-3.5-turbo",
        temperature=0.7,
        max_tokens=2000
    )
    
    agent_config = AgentConfig(
        llm_config=llm_config,
        max_debate_rounds=1,  # Reduce for testing
        max_risk_discuss_rounds=1
    )
    
    time_range = TimeRange(
        start=datetime(2024, 1, 1),
        end=datetime(2024, 1, 2)  # Just 2 days for testing
    )
    
    config = BacktestConfig(
        symbols=["AAPL"],
        time_range=time_range,
        initial_capital=100000.0,
        agent_config=agent_config,
        debug=True
    )
    
    print(f"LLM Models: deep={llm_config.deep_think_model}, quick={llm_config.quick_think_model}")
    print(f"Date range: {time_range.start} to {time_range.end}")
    print("\nStarting backtest...\n")
    
    engine = BacktestEngine(config)
    
    try:
        result = await engine.run()
        
        print(f"\n=== Results ===")
        print(f"Total trades: {result.metrics.total_trades}")
        print(f"Final value: ${result.final_portfolio.total_value:,.2f}")
        print(f"Total return: {result.metrics.total_return:.2%}")
        
        # Check transactions
        if hasattr(result, 'transactions') and result.transactions:
            print(f"\nTransactions:")
            for i, tx in enumerate(result.transactions[:5]):  # First 5
                print(f"  {i+1}. {tx.timestamp}: {tx.action} {tx.quantity} {tx.symbol} @ ${tx.price}")
        
    except Exception as e:
        print(f"\nError during backtest: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    import os
    
    # Check for API key
    if not os.getenv("OPENAI_API_KEY"):
        print("Error: OPENAI_API_KEY not set")
        print("Set it with: export OPENAI_API_KEY='your-key'")
    else:
        print("Starting LLM execution monitor...")
        print("Log file: logs/llm_execution.log")
        asyncio.run(test_real_llm())
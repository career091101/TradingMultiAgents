#!/usr/bin/env python3
"""
Test LLM agent directly
"""

import asyncio
import logging
from datetime import datetime, timedelta

# Setup detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

from backtest2.core.config import LLMConfig
from backtest2.core.types import MarketData, DecisionContext, PortfolioState
from backtest2.agents.agent_adapter import MarketAnalystAdapter
from backtest2.memory.agent_memory import AgentMemory

async def test_llm_agent():
    """Test LLM agent directly"""
    
    logger = logging.getLogger(__name__)
    
    # Create LLM config
    llm_config = LLMConfig(
        deep_think_model="gpt-4",  # Use a valid OpenAI model
        quick_think_model="gpt-3.5-turbo",
        temperature=0.7,
        max_tokens=2000
    )
    
    # Create agent
    memory = AgentMemory("test_agent")
    agent = MarketAnalystAdapter("Market Analyst", llm_config, memory)
    
    # Create test data
    market_data = MarketData(
        symbol="AAPL",
        date=datetime.now(),
        open=150.0,
        high=155.0,
        low=149.0,
        close=154.0,
        volume=1000000,
        adjusted_close=154.0
    )
    
    context = DecisionContext(
        timestamp=datetime.now(),
        market_state={'symbol': 'AAPL', 'data': market_data},
        portfolio_state=PortfolioState(
            cash=100000,
            positions={},
            total_value=100000,
            exposure=0,
            position_count=0,
            unrealized_pnl=0,
            realized_pnl=0
        ),
        recent_performance={},
        risk_metrics={}
    )
    
    logger.info("Testing agent with real data...")
    
    try:
        # Test agent
        result = await agent.process({
            'market_data': market_data,
            'context': context
        })
        
        logger.info(f"Agent result: {result}")
        logger.info(f"Result type: {type(result)}")
        logger.info(f"Content: {result.content if hasattr(result, 'content') else 'N/A'}")
        logger.info(f"Confidence: {result.confidence if hasattr(result, 'confidence') else 'N/A'}")
        
    except Exception as e:
        logger.error(f"Agent test failed: {e}", exc_info=True)

if __name__ == "__main__":
    # Check for OpenAI API key
    import os
    if not os.getenv("OPENAI_API_KEY"):
        print("ERROR: OPENAI_API_KEY environment variable not set")
        exit(1)
    
    asyncio.run(test_llm_agent())
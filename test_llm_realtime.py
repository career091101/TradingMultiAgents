#!/usr/bin/env python3
"""
Test LLM response in real-time
"""

import asyncio
import logging
from datetime import datetime
from backtest2.core.config import LLMConfig
from backtest2.agents.llm_client import OpenAILLMClient

# Setup logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def test_llm_response():
    """Test real LLM response parsing"""
    
    # Create LLM config with a real model
    llm_config = LLMConfig(
        deep_think_model="gpt-4",  # or whatever model you're using
        quick_think_model="gpt-3.5-turbo"
    )
    
    client = OpenAILLMClient(llm_config)
    
    # Test with a simple schema
    test_schema = {
        "action": {"type": "string", "enum": ["BUY", "SELL", "HOLD"]},
        "confidence": {"type": "number", "minimum": 0, "maximum": 1},
        "rationale": {"type": "string"}
    }
    
    # Test context
    context = {
        "symbol": "AAPL",
        "price": 150.0,
        "timestamp": datetime.now().isoformat()
    }
    
    # Test prompt
    prompt = """
    Based on the current market conditions, should we BUY, SELL, or HOLD AAPL?
    
    Please respond in JSON format with:
    - action: BUY, SELL, or HOLD
    - confidence: a number between 0 and 1
    - rationale: your reasoning
    """
    
    try:
        print("Testing LLM response parsing...")
        response = await client.generate_structured(
            prompt=prompt,
            context=context,
            output_schema=test_schema,
            use_deep_thinking=False,
            agent_name="test_agent"
        )
        
        print("\n=== LLM Response ===")
        print(f"Action: {response.get('action', 'N/A')}")
        print(f"Confidence: {response.get('confidence', 'N/A')}")
        print(f"Rationale: {response.get('rationale', 'N/A')}")
        
        # Check if response is valid
        if response.get('action') in ['BUY', 'SELL', 'HOLD']:
            print("\n✓ Response successfully parsed!")
        else:
            print("\n✗ Response parsing failed - invalid action")
            
    except Exception as e:
        print(f"\nError during test: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await client.cleanup()

if __name__ == "__main__":
    # Check if API key is set
    import os
    if not os.getenv("OPENAI_API_KEY"):
        print("Error: OPENAI_API_KEY environment variable not set")
        print("Please set it with: export OPENAI_API_KEY='your-api-key'")
    else:
        asyncio.run(test_llm_response())
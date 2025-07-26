#!/usr/bin/env python
"""Test the JSON parsing fixes for BUY/SELL/HOLD decisions"""

import os
import asyncio
import logging
from datetime import datetime
from pathlib import Path

# Set API key
bashrc_path = Path.home() / ".bashrc"
if bashrc_path.exists():
    with open(bashrc_path, 'r') as f:
        for line in f:
            if 'export OPENAI_API_KEY=' in line:
                key = line.strip().split('=', 1)[1].strip('"')
                os.environ['OPENAI_API_KEY'] = key
                break

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def test_json_parsing():
    """Test JSON parsing with the improved implementation"""
    print("🧪 Testing JSON Parsing Fixes")
    print("=" * 50)
    
    from backtest2.agents.llm_client import OpenAILLMClient
    from backtest2.core.config import LLMConfig
    
    # Create LLM client
    config = LLMConfig(
        deep_think_model="gpt-3.5-turbo",
        quick_think_model="gpt-3.5-turbo",
        temperature=0.7,
        max_tokens=300
    )
    
    client = OpenAILLMClient(config)
    
    # Test structured response generation
    test_cases = [
        {
            "agent": "Risk Manager",
            "prompt": "Based on strong bullish signals, should we buy?",
            "schema": {
                "action": {"type": "string", "enum": ["BUY", "SELL", "HOLD"]},
                "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                "rationale": {"type": "string"}
            }
        },
        {
            "agent": "Trader",
            "prompt": "Market is oversold, RSI at 25, what action?",
            "schema": {
                "action": {"type": "string", "enum": ["BUY", "SELL", "HOLD"]},
                "entry_strategy": {"type": "string"},
                "confidence": {"type": "number"}
            }
        },
        {
            "agent": "Bear Researcher",
            "prompt": "Valuation concerns are rising, P/E at 40",
            "schema": {
                "recommendation": {"type": "string", "enum": ["BUY", "SELL", "HOLD"]},
                "confidence": {"type": "number"},
                "rationale": {"type": "string"}
            }
        }
    ]
    
    print("\n📊 Testing structured responses:\n")
    
    results = []
    for i, test in enumerate(test_cases, 1):
        print(f"Test {i}: {test['agent']}")
        print(f"Prompt: {test['prompt'][:50]}...")
        
        try:
            result = await client.generate_structured(
                prompt=test['prompt'],
                context={"test": True, "market_data": {"price": 100}},
                output_schema=test['schema'],
                agent_name=test['agent'],
                use_cache=False  # Disable cache for testing
            )
            
            print(f"✅ Success! Result: {result}")
            
            # Validate result
            action_field = "action" if "action" in result else "recommendation"
            if action_field in result and result[action_field] in ["BUY", "SELL", "HOLD"]:
                print(f"   Decision: {result[action_field]}")
                print(f"   Confidence: {result.get('confidence', 'N/A')}")
                results.append(result[action_field])
            else:
                print("   ❌ Invalid action format")
                
        except Exception as e:
            print(f"❌ Error: {e}")
            
        print("-" * 50)
    
    # Summary
    print("\n📊 SUMMARY")
    print("=" * 50)
    
    if results:
        from collections import Counter
        counts = Counter(results)
        print(f"Total valid decisions: {len(results)}")
        for action, count in counts.items():
            print(f"  {action}: {count}")
        
        if len(set(results)) > 1:
            print("\n✅ SUCCESS! System generates varied decisions with fixed JSON parsing!")
        else:
            print("\n⚠️  All decisions are the same")
    else:
        print("❌ No valid decisions generated")
    
    # Cleanup
    await client.cleanup()

if __name__ == "__main__":
    print("🔧 JSON Parsing Fix Test")
    print("This tests the improved JSON parsing implementation\n")
    
    asyncio.run(test_json_parsing())
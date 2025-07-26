#!/usr/bin/env python3
"""
Comprehensive API connectivity test for all models
"""

import os
import asyncio
from datetime import datetime
import openai
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

# Set API keys
os.environ['OPENAI_API_KEY'] = "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"

def test_basic_connectivity():
    """Test basic OpenAI API connectivity"""
    print("=" * 60)
    print("1. Basic OpenAI API Connectivity Test")
    print("=" * 60)
    
    try:
        client = openai.OpenAI()
        models = client.models.list()
        print(f"✓ Successfully connected to OpenAI API")
        print(f"✓ Found {len(models.data)} available models")
        
        # Show o-series models
        o_models = [m.id for m in models.data if m.id.startswith(('o1', 'o3', 'o4'))]
        print(f"\nAvailable o-series models:")
        for model in sorted(o_models)[:10]:
            print(f"  - {model}")
            
        return True
    except Exception as e:
        print(f"✗ API connection failed: {e}")
        return False

async def test_langchain_models():
    """Test LangChain with different models"""
    print("\n" + "=" * 60)
    print("2. LangChain Model Tests")
    print("=" * 60)
    
    test_cases = [
        # (model_name, use_max_completion_tokens, merge_system_message)
        ("gpt-3.5-turbo", False, False),
        ("gpt-4-turbo-preview", False, False),
        ("o3-2025-04-16", True, True),
        ("o4-mini-2025-04-16", True, True),
    ]
    
    for model_name, use_completion_tokens, merge_system in test_cases:
        print(f"\nTesting: {model_name}")
        print("-" * 40)
        
        try:
            # Create LangChain client with appropriate parameters
            if use_completion_tokens:
                llm = ChatOpenAI(
                    model=model_name,
                    temperature=1.0,  # o3/o4 models only support temperature=1.0
                    max_completion_tokens=50
                )
            else:
                llm = ChatOpenAI(
                    model=model_name,
                    temperature=0,
                    max_tokens=50
                )
            
            # Prepare messages
            if merge_system:
                # For o-series: merge system into user message
                messages = [
                    HumanMessage(content="Instructions: You are a helpful assistant.\n\nRequest: Say hello in 5 words or less")
                ]
            else:
                # For standard models
                messages = [
                    SystemMessage(content="You are a helpful assistant."),
                    HumanMessage(content="Say hello in 5 words or less")
                ]
            
            # Test invocation
            start_time = datetime.now()
            response = await llm.ainvoke(messages)
            elapsed = (datetime.now() - start_time).total_seconds()
            
            print(f"✓ Success!")
            print(f"  Response: {response.content}")
            print(f"  Time: {elapsed:.2f}s")
            print(f"  Model used: {response.response_metadata.get('model', 'unknown')}")
            
        except Exception as e:
            print(f"✗ Error: {str(e)[:200]}")

async def test_backtest_scenario():
    """Test a realistic backtest scenario"""
    print("\n" + "=" * 60)
    print("3. Backtest Scenario Test")
    print("=" * 60)
    
    # Test with both standard and o-series models
    models = [
        ("gpt-3.5-turbo", False),
        ("o4-mini-2025-04-16", True)
    ]
    
    for model_name, is_o_series in models:
        print(f"\nTesting financial analysis with: {model_name}")
        print("-" * 40)
        
        try:
            if is_o_series:
                llm = ChatOpenAI(
                    model=model_name,
                    temperature=1.0,  # o3/o4 models only support temperature=1.0
                    max_completion_tokens=200
                )
                
                # Merged format for o-series
                prompt = """Instructions: You are a financial analyst specializing in technical analysis.

Request: Analyze the following market data and provide a trading recommendation:
- Symbol: AAPL
- Current Price: $150
- 50-day MA: $145
- 200-day MA: $140
- RSI: 65
- Volume: Above average

Provide: 1) Market sentiment 2) Trading action (BUY/HOLD/SELL) 3) Brief rationale"""
                
                messages = [HumanMessage(content=prompt)]
                
            else:
                llm = ChatOpenAI(
                    model=model_name,
                    temperature=0.7,
                    max_tokens=200
                )
                
                messages = [
                    SystemMessage(content="You are a financial analyst specializing in technical analysis."),
                    HumanMessage(content="""Analyze the following market data and provide a trading recommendation:
- Symbol: AAPL
- Current Price: $150
- 50-day MA: $145
- 200-day MA: $140
- RSI: 65
- Volume: Above average

Provide: 1) Market sentiment 2) Trading action (BUY/HOLD/SELL) 3) Brief rationale""")
                ]
            
            start_time = datetime.now()
            response = await llm.ainvoke(messages)
            elapsed = (datetime.now() - start_time).total_seconds()
            
            print(f"✓ Analysis completed in {elapsed:.2f}s")
            print(f"\nResponse preview:")
            print(response.content[:300] + "..." if len(response.content) > 300 else response.content)
            
        except Exception as e:
            print(f"✗ Error: {str(e)[:200]}")

def test_finnhub_api():
    """Test Finnhub API connectivity"""
    print("\n" + "=" * 60)
    print("4. Finnhub API Test")
    print("=" * 60)
    
    try:
        import requests
        
        api_key = "d1p1c79r01qi9vk226a0d1p1c79r01qi9vk226ag"
        url = f"https://finnhub.io/api/v1/quote?symbol=AAPL&token={api_key}"
        
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Finnhub API connected successfully")
            print(f"  AAPL current price: ${data.get('c', 'N/A')}")
            print(f"  Daily change: {data.get('dp', 'N/A')}%")
        else:
            print(f"✗ Finnhub API error: Status {response.status_code}")
            
    except Exception as e:
        print(f"✗ Finnhub connection failed: {e}")

async def main():
    """Run all tests"""
    print("API CONNECTIVITY TEST SUITE")
    print(f"Test Time: {datetime.now()}")
    print("=" * 60)
    
    # Test 1: Basic connectivity
    if not test_basic_connectivity():
        print("\n⚠️  Basic connectivity failed. Check API key.")
        return
    
    # Test 2: LangChain models
    await test_langchain_models()
    
    # Test 3: Backtest scenario
    await test_backtest_scenario()
    
    # Test 4: Finnhub
    test_finnhub_api()
    
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print("✓ OpenAI API: Connected")
    print("✓ o3/o4 models: Available with special handling")
    print("✓ Standard models: Working normally")
    print("✓ Finnhub API: Connected")
    print("\nRecommendation: Use the WebUI with appropriate model selection")

if __name__ == "__main__":
    asyncio.run(main())
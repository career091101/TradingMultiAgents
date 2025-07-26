#!/usr/bin/env python
"""Quick test to check decision generation with reduced context"""

import os
import asyncio
import logging
from datetime import datetime, timedelta
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

from backtest2.core.config import BacktestConfig, AgentConfig, LLMConfig, RiskConfig, TimeRange, RiskProfile
from backtest2.core.engine import BacktestEngine

# Minimal logging
logging.basicConfig(level=logging.WARNING)
logging.getLogger('backtest2.agents.orchestrator').setLevel(logging.INFO)

async def quick_test():
    """Quick decision test with minimal period"""
    print("⚡ Quick Decision Generation Test")
    print("Testing with 1 day only to reduce API calls\n")
    
    config = BacktestConfig(
        symbols=["AAPL"],
        time_range=TimeRange(
            start=datetime(2025, 7, 23),
            end=datetime(2025, 7, 24)  # Just 1 day
        ),
        initial_capital=100000.0,
        debug=False,  # Disable debug to reduce output
        agent_config=AgentConfig(
            llm_config=LLMConfig(
                deep_think_model="gpt-3.5-turbo",  # Use cheaper/faster model
                quick_think_model="gpt-3.5-turbo",
                temperature=0.7,
                max_tokens=500  # Further reduced
            ),
            use_japanese_prompts=True,
            max_debate_rounds=1,
            max_risk_discuss_rounds=1,
            enable_memory=False  # Disable to reduce context
        ),
        risk_config=RiskConfig(
            max_positions=5,
            position_limits={
                'AAPL': 0.5,
                RiskProfile.AGGRESSIVE: 0.8,
                RiskProfile.NEUTRAL: 0.5,
                RiskProfile.CONSERVATIVE: 0.3
            }
        )
    )
    
    engine = BacktestEngine(config)
    
    try:
        print("Running quick test...")
        result = await engine.run()
        
        perf = result.agent_performance
        total = perf.get('total_decisions', 0)
        breakdown = perf.get('decision_breakdown', {})
        
        print(f"\n🎯 Results:")
        print(f"Total decisions: {total}")
        
        if total > 0:
            for action, count in breakdown.items():
                print(f"  {action}: {count}")
                
            if breakdown.get('HOLD', 0) < total:
                print("\n✅ SUCCESS! System generated BUY/SELL decisions!")
            else:
                print("\n❌ Still only HOLD decisions")
                
            # Check debug logs
            debug_dir = Path("logs/llm_debug")
            if debug_dir.exists():
                latest_files = sorted(debug_dir.glob("*.json"))[-3:]
                if latest_files:
                    print(f"\n📄 Latest debug file: {latest_files[-1].name}")
                    with open(latest_files[-1], 'r') as f:
                        import json
                        data = json.load(f)
                        print(f"Agent: {data.get('agent')}")
                        print(f"Response preview: {data.get('response', '')[:200]}...")
                        
    except Exception as e:
        print(f"❌ Error: {e}")
        
    finally:
        await engine._cleanup()

if __name__ == "__main__":
    asyncio.run(quick_test())
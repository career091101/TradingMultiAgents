#!/usr/bin/env python
"""Simple test for BUY/SELL/HOLD decisions with minimal complexity"""

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

# Set minimal logging
logging.basicConfig(level=logging.WARNING)

# Create a simple test directly with the components
async def simple_test():
    print("🧪 Simple BUY/SELL/HOLD Test")
    print("=" * 50)
    
    try:
        # Import after setting env
        from backtest2.agents.llm_client import OpenAILLMClient
        from backtest2.core.config import LLMConfig
        
        # Create LLM client
        config = LLMConfig(
            deep_think_model="gpt-3.5-turbo",
            quick_think_model="gpt-3.5-turbo",
            temperature=0.7,
            max_tokens=200
        )
        
        client = OpenAILLMClient(config)
        
        # Test direct decision generation
        print("\n📊 Testing direct decision generation...")
        
        test_prompts = [
            "The stock price has increased 10% in the last week with strong volume. Should I BUY, SELL, or HOLD?",
            "The company reported lower than expected earnings and the stock dropped 5%. Should I BUY, SELL, or HOLD?",
            "The stock has been trading sideways for a month with no clear trend. Should I BUY, SELL, or HOLD?"
        ]
        
        decisions = []
        
        for i, prompt in enumerate(test_prompts, 1):
            print(f"\nTest {i}: {prompt[:50]}...")
            
            response = await client.generate(
                prompt=prompt + "\n\nRespond with only one word: BUY, SELL, or HOLD.",
                context={},
                use_deep_thinking=False,
                system_message="You are a trading assistant. Respond with only BUY, SELL, or HOLD.",
                agent_name="test"
            )
            
            # Clean response
            decision = response.strip().upper()
            if decision in ["BUY", "SELL", "HOLD"]:
                decisions.append(decision)
                print(f"✅ Decision: {decision}")
            else:
                print(f"❌ Invalid response: {response}")
                
        # Analyze results
        print("\n" + "="*50)
        print("📊 RESULTS SUMMARY")
        print("="*50)
        
        if len(decisions) == len(test_prompts):
            print(f"\n✅ All {len(test_prompts)} tests generated valid decisions!")
            
            from collections import Counter
            counts = Counter(decisions)
            
            print("\nDecision breakdown:")
            for action in ["BUY", "SELL", "HOLD"]:
                count = counts.get(action, 0)
                print(f"  {action}: {count}")
                
            if len(set(decisions)) > 1:
                print("\n✅ SUCCESS! System generates varied decisions!")
            else:
                print("\n⚠️  WARNING: All decisions are the same")
        else:
            print(f"\n❌ Only {len(decisions)}/{len(test_prompts)} valid decisions generated")
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

# Run full backtest test
async def backtest_test():
    print("\n\n🧪 Full Backtest Decision Test")
    print("=" * 50)
    
    from backtest2.core.config import BacktestConfig, AgentConfig, LLMConfig, RiskConfig, TimeRange, RiskProfile
    from backtest2.core.engine import BacktestEngine
    
    # Minimal config
    config = BacktestConfig(
        symbols=["AAPL"],
        time_range=TimeRange(
            start=datetime(2025, 7, 23),
            end=datetime(2025, 7, 25)  # Just 2 days
        ),
        initial_capital=100000.0,
        debug=False,
        agent_config=AgentConfig(
            llm_config=LLMConfig(
                deep_think_model="gpt-3.5-turbo",
                quick_think_model="gpt-3.5-turbo",
                temperature=0.7,
                max_tokens=200  # Very limited to avoid context issues
            ),
            use_japanese_prompts=False,  # Use English for simplicity
            max_debate_rounds=1,
            max_risk_discuss_rounds=1,
            enable_memory=False
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
    
    # Capture orchestrator logs
    decisions_made = []
    original_log = logging.getLogger('backtest2.agents.orchestrator').info
    
    def capture_log(msg):
        if "Final decision for" in msg and "with confidence" in msg:
            decisions_made.append(msg)
        original_log(msg)
    
    logging.getLogger('backtest2.agents.orchestrator').setLevel(logging.INFO)
    logging.getLogger('backtest2.agents.orchestrator').info = capture_log
    
    try:
        print("\nRunning backtest...")
        result = await engine.run()
        
        perf = result.agent_performance
        total = perf.get('total_decisions', 0)
        breakdown = perf.get('decision_breakdown', {})
        
        print(f"\n📊 Backtest Results:")
        print(f"Total decisions: {total}")
        
        if total > 0:
            for action, count in breakdown.items():
                print(f"  {action}: {count}")
                
            # Check captured decisions
            print(f"\nCaptured decision logs: {len(decisions_made)}")
            for decision in decisions_made[-3:]:  # Last 3
                if "BUY" in decision:
                    print(f"  ✅ {decision}")
                elif "SELL" in decision:
                    print(f"  ✅ {decision}")
                else:
                    print(f"  ⚠️  {decision}")
                    
            if breakdown.get('BUY', 0) > 0 or breakdown.get('SELL', 0) > 0:
                print("\n✅ SUCCESS! System generates BUY/SELL decisions in backtest!")
            else:
                print("\n❌ No BUY/SELL decisions in backtest")
                
    except Exception as e:
        print(f"\n❌ Backtest error: {e}")
        
    finally:
        await engine._cleanup()

async def main():
    # Run simple test first
    await simple_test()
    
    # Then run backtest
    await backtest_test()

if __name__ == "__main__":
    print("🎯 BUY/SELL/HOLD Decision Capability Test")
    print("Testing if the system can generate appropriate trading decisions\n")
    
    asyncio.run(main())
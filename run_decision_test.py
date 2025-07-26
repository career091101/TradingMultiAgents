#!/usr/bin/env python
"""Test if BUY/SELL/HOLD decisions are properly generated"""

import os
import asyncio
import logging
from datetime import datetime, timedelta
from pathlib import Path

# Set API key from .bashrc
bashrc_path = Path.home() / ".bashrc"
if bashrc_path.exists():
    with open(bashrc_path, 'r') as f:
        for line in f:
            if 'export OPENAI_API_KEY=' in line:
                key = line.strip().split('=', 1)[1].strip('"')
                os.environ['OPENAI_API_KEY'] = key
                print(f"✅ Loaded OPENAI_API_KEY")
                break

# Import after setting environment
from backtest2.core.config import BacktestConfig, AgentConfig, LLMConfig, RiskConfig, TimeRange
from backtest2.core.engine import BacktestEngine

# Configure minimal logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

async def run_decision_test():
    """Run a short backtest to test decision generation"""
    print("🧪 Testing BUY/SELL/HOLD Decision Generation")
    print("=" * 60)
    
    # Short test period (3 days)
    config = BacktestConfig(
        symbols=["AAPL"],
        time_range=TimeRange(
            start=datetime(2025, 7, 21),
            end=datetime(2025, 7, 24)
        ),
        initial_capital=100000.0,
        debug=True,
        agent_config=AgentConfig(
            llm_config=LLMConfig(
                deep_think_model="gpt-4",
                quick_think_model="gpt-4o-mini",
                temperature=0.7
            ),
            use_japanese_prompts=True,
            max_debate_rounds=1,
            max_risk_discuss_rounds=1,
            enable_memory=True
        ),
        risk_config=RiskConfig(
            max_positions=5,
            position_limits={'AAPL': 0.5},
            stop_loss=0.1,
            take_profit=0.2
        )
    )
    
    print("Configuration:")
    print(f"  - Symbols: {config.symbols}")
    print(f"  - Period: {config.time_range.start} to {config.time_range.end}")
    print(f"  - Models: deep={config.agent_config.llm_config.deep_think_model}, quick={config.agent_config.llm_config.quick_think_model}")
    print(f"  - Japanese prompts: {config.agent_config.use_japanese_prompts}")
    print()
    
    engine = BacktestEngine(config)
    
    try:
        print("🚀 Running backtest...")
        print("Please wait, this may take a few minutes...")
        print()
        
        result = await engine.run()
        
        print("\n" + "="*60)
        print("📊 RESULTS SUMMARY")
        print("="*60)
        
        # Get agent performance
        perf = result.agent_performance
        total_decisions = perf.get('total_decisions', 0)
        decision_stats = perf.get('decision_stats', {})
        breakdown = perf.get('decision_breakdown', {})
        
        print(f"\n🎯 Total Decisions Made: {total_decisions}")
        
        if total_decisions > 0:
            print("\n📈 Decision Breakdown:")
            for action, count in breakdown.items():
                percentage = (count / total_decisions) * 100
                bar = "█" * int(percentage / 5)  # Visual bar
                print(f"  {action:6}: {count:3} ({percentage:5.1f}%) {bar}")
            
            print(f"\n💰 Trades Executed: {perf.get('total_trades', 0)}")
            print(f"📊 Trade Execution Rate: {perf.get('trade_execution_rate', 0):.1%}")
            
            # Check if all decisions are HOLD
            if breakdown.get('HOLD', 0) == total_decisions:
                print("\n⚠️  WARNING: All decisions are HOLD!")
                print("   This indicates the issue is NOT resolved.")
            else:
                print("\n✅ SUCCESS: Decisions include BUY/SELL actions!")
                print("   The system is now generating varied trading decisions.")
                
        else:
            print("\n❌ ERROR: No decisions were made!")
            
        # Show some example decisions from debug log
        print("\n📝 Sample Decision Log:")
        debug_dir = Path("logs/llm_debug")
        if debug_dir.exists():
            files = sorted(debug_dir.glob("*.json"))[-5:]  # Last 5 files
            print(f"   Found {len(list(debug_dir.glob('*.json')))} debug files")
            print("   Check logs/llm_debug/ for detailed LLM responses")
            
    except Exception as e:
        print(f"\n❌ Error during backtest: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        await engine._cleanup()

if __name__ == "__main__":
    print("🔍 BUY/SELL/HOLD Decision Generation Test")
    print("This test verifies that the system can generate varied trading decisions")
    print()
    
    # Check API key
    if not os.environ.get('OPENAI_API_KEY'):
        print("❌ OPENAI_API_KEY not set!")
        print("Please run: source ~/.bashrc")
        exit(1)
        
    asyncio.run(run_decision_test())
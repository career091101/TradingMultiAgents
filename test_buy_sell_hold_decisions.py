#!/usr/bin/env python
"""Comprehensive test for BUY/SELL/HOLD decision generation"""

import os
import asyncio
import logging
from datetime import datetime, timedelta
from pathlib import Path
from collections import Counter
import json

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

from backtest2.core.config import BacktestConfig, AgentConfig, LLMConfig, RiskConfig, TimeRange, RiskProfile
from backtest2.core.engine import BacktestEngine

# Configure logging to capture decision info
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('decision_test.log'),
        logging.StreamHandler()
    ]
)

# Capture decision logs
decision_log = []
original_info = logging.getLogger('backtest2.agents.orchestrator').info

def capture_decisions(msg):
    if "[DECISION DEBUG]" in msg:
        decision_log.append(msg)
    original_info(msg)

logging.getLogger('backtest2.agents.orchestrator').info = capture_decisions

async def test_decisions():
    """Test BUY/SELL/HOLD decision generation over multiple days"""
    print("🧪 BUY/SELL/HOLD Decision Generation Test")
    print("=" * 70)
    print()
    
    # Test configuration
    config = BacktestConfig(
        symbols=["AAPL", "MSFT"],  # Test with 2 symbols
        time_range=TimeRange(
            start=datetime(2025, 7, 20),
            end=datetime(2025, 7, 25)  # 5 days
        ),
        initial_capital=100000.0,
        debug=True,
        agent_config=AgentConfig(
            llm_config=LLMConfig(
                deep_think_model="gpt-3.5-turbo",  # Faster model for testing
                quick_think_model="gpt-3.5-turbo",
                temperature=0.7,
                max_tokens=500
            ),
            use_japanese_prompts=True,
            max_debate_rounds=1,
            max_risk_discuss_rounds=1,
            enable_memory=True
        ),
        risk_config=RiskConfig(
            max_positions=5,
            position_limits={
                'AAPL': 0.5,
                'MSFT': 0.5,
                RiskProfile.AGGRESSIVE: 0.8,
                RiskProfile.NEUTRAL: 0.5,
                RiskProfile.CONSERVATIVE: 0.3
            },
            stop_loss=0.1,
            take_profit=0.2
        )
    )
    
    print("📊 Test Configuration:")
    print(f"  Symbols: {config.symbols}")
    print(f"  Period: {config.time_range.start.date()} to {config.time_range.end.date()}")
    print(f"  Days: {(config.time_range.end - config.time_range.start).days}")
    print(f"  Models: {config.agent_config.llm_config.deep_think_model}")
    print()
    
    engine = BacktestEngine(config)
    
    try:
        print("🚀 Running backtest...")
        print("Please wait, this will test multiple trading decisions...\n")
        
        start_time = datetime.now()
        result = await engine.run()
        end_time = datetime.now()
        
        print(f"\n✅ Backtest completed in {(end_time - start_time).total_seconds():.1f} seconds")
        print("\n" + "="*70)
        print("📊 DECISION STATISTICS")
        print("="*70)
        
        # Analyze results
        perf = result.agent_performance
        total_decisions = perf.get('total_decisions', 0)
        breakdown = perf.get('decision_breakdown', {})
        
        print(f"\n🎯 Total Decisions: {total_decisions}")
        
        if total_decisions > 0:
            print("\n📈 Decision Distribution:")
            
            # Visual representation
            max_count = max(breakdown.values()) if breakdown else 1
            for action in ['BUY', 'SELL', 'HOLD']:
                count = breakdown.get(action, 0)
                percentage = (count / total_decisions) * 100
                bar_length = int((count / max_count) * 40)
                bar = "█" * bar_length + "░" * (40 - bar_length)
                print(f"  {action:5}: {count:3} ({percentage:5.1f}%) |{bar}|")
            
            # Decision quality check
            print("\n🔍 Decision Quality Analysis:")
            
            buy_count = breakdown.get('BUY', 0)
            sell_count = breakdown.get('SELL', 0)
            hold_count = breakdown.get('HOLD', 0)
            
            if hold_count == total_decisions:
                print("  ❌ PROBLEM: All decisions are HOLD!")
                print("     The issue is NOT resolved.")
            elif buy_count == 0 or sell_count == 0:
                print("  ⚠️  WARNING: Missing BUY or SELL decisions")
                print(f"     BUY: {buy_count}, SELL: {sell_count}")
            else:
                print("  ✅ SUCCESS: System generates varied decisions!")
                print(f"     BUY: {buy_count}, SELL: {sell_count}, HOLD: {hold_count}")
                
                # Calculate decision diversity
                diversity = min(buy_count, sell_count, hold_count) / max(buy_count, sell_count, hold_count)
                print(f"  📊 Decision Diversity Score: {diversity:.2f} (1.0 = perfectly balanced)")
            
            # Trade execution stats
            print(f"\n💰 Trade Execution:")
            print(f"  Executed Trades: {perf.get('total_trades', 0)}")
            print(f"  Execution Rate: {perf.get('trade_execution_rate', 0):.1%}")
            
            # Parse decision log for details
            print("\n📝 Sample Decisions:")
            for i, log_entry in enumerate(decision_log[-5:]):  # Last 5 decisions
                # Extract decision info from log
                if "Final decision:" in log_entry:
                    parts = log_entry.split("Final decision:")[-1]
                    print(f"  {i+1}. {parts.strip()}")
                    
        else:
            print("\n❌ ERROR: No decisions were made!")
            
        # Check for errors
        if len(decision_log) < total_decisions:
            print(f"\n⚠️  Note: Expected {total_decisions} decision logs but found {len(decision_log)}")
            
        # Save detailed results
        results_file = Path("decision_test_results.json")
        with open(results_file, 'w') as f:
            json.dump({
                "test_date": datetime.now().isoformat(),
                "config": {
                    "symbols": config.symbols,
                    "days": (config.time_range.end - config.time_range.start).days,
                    "model": config.agent_config.llm_config.deep_think_model
                },
                "results": {
                    "total_decisions": total_decisions,
                    "breakdown": breakdown,
                    "trades_executed": perf.get('total_trades', 0),
                    "execution_rate": perf.get('trade_execution_rate', 0)
                },
                "decision_logs": decision_log[-10:]  # Last 10 decisions
            }, f, indent=2)
            
        print(f"\n💾 Detailed results saved to: {results_file}")
        
    except Exception as e:
        print(f"\n❌ Error during test: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        await engine._cleanup()
        print("\n✅ Test completed")

if __name__ == "__main__":
    print("🎯 BUY/SELL/HOLD Decision Generation Test")
    print("This test verifies that the system generates appropriate trading decisions")
    print()
    
    # Check API key
    if not os.environ.get('OPENAI_API_KEY'):
        print("❌ OPENAI_API_KEY not set!")
        exit(1)
        
    asyncio.run(test_decisions())
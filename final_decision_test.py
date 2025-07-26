#!/usr/bin/env python
"""Final comprehensive test for BUY/SELL/HOLD decision generation"""

import os
import asyncio
import logging
from datetime import datetime
from pathlib import Path
import json

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
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)

from backtest2.core.config import BacktestConfig, AgentConfig, LLMConfig, RiskConfig, TimeRange, RiskProfile
from backtest2.core.engine import BacktestEngine

async def final_test():
    """Final test with all improvements"""
    print("🎯 Final BUY/SELL/HOLD Decision Test")
    print("=" * 70)
    print()
    
    # Test configuration optimized for decision generation
    config = BacktestConfig(
        symbols=["AAPL", "MSFT"],
        time_range=TimeRange(
            start=datetime(2025, 7, 20),
            end=datetime(2025, 7, 23)  # 3 days
        ),
        initial_capital=100000.0,
        debug=False,
        agent_config=AgentConfig(
            llm_config=LLMConfig(
                deep_think_model="gpt-3.5-turbo",
                quick_think_model="gpt-3.5-turbo",
                temperature=0.8,  # Slightly higher for more variation
                max_tokens=500
            ),
            use_japanese_prompts=True,
            max_debate_rounds=1,
            max_risk_discuss_rounds=1,
            enable_memory=False
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
    print()
    
    engine = BacktestEngine(config)
    
    try:
        print("🚀 Running comprehensive test...")
        start_time = datetime.now()
        
        # Capture orchestrator decision logs
        decisions_captured = []
        original_info = logging.getLogger('backtest2.agents.orchestrator').info
        
        def capture_info(msg):
            if "Final decision for" in msg and "with confidence" in msg:
                decisions_captured.append(msg)
            original_info(msg)
        
        logging.getLogger('backtest2.agents.orchestrator').info = capture_info
        
        # Run backtest
        result = await engine.run()
        end_time = datetime.now()
        
        print(f"\n✅ Test completed in {(end_time - start_time).total_seconds():.1f} seconds")
        print("\n" + "="*70)
        print("📊 RESULTS SUMMARY")
        print("="*70)
        
        # Analyze results
        perf = result.agent_performance
        total_decisions = perf.get('total_decisions', 0)
        breakdown = perf.get('decision_breakdown', {})
        trades_executed = perf.get('total_trades', 0)
        
        print(f"\n🎯 Total Decisions: {total_decisions}")
        print(f"💰 Trades Executed: {trades_executed}")
        
        if total_decisions > 0:
            print("\n📈 Decision Distribution:")
            for action in ['BUY', 'SELL', 'HOLD']:
                count = breakdown.get(action, 0)
                percentage = (count / total_decisions) * 100
                bar = "█" * int(percentage / 5) + "░" * (20 - int(percentage / 5))
                print(f"  {action:5}: {count:3} ({percentage:5.1f}%) |{bar}|")
            
            # Analyze quality
            buy_count = breakdown.get('BUY', 0)
            sell_count = breakdown.get('SELL', 0)
            hold_count = breakdown.get('HOLD', 0)
            
            print("\n🔍 Analysis:")
            
            if hold_count == total_decisions:
                print("  ❌ PROBLEM: All decisions are HOLD!")
                print("     JSON parsing fixes are working but Risk Manager is too conservative.")
            elif buy_count == 0 or sell_count == 0:
                print("  ⚠️  WARNING: Missing BUY or SELL decisions")
                print(f"     BUY: {buy_count}, SELL: {sell_count}")
            else:
                print("  ✅ SUCCESS: System generates varied BUY/SELL/HOLD decisions!")
                print(f"     BUY: {buy_count}, SELL: {sell_count}, HOLD: {hold_count}")
                
                # Decision diversity
                diversity = min(buy_count, sell_count, hold_count) / max(buy_count, sell_count, hold_count)
                print(f"  📊 Diversity Score: {diversity:.2f} (1.0 = perfectly balanced)")
            
            # Show captured decisions
            print("\n📝 Sample Decisions Captured:")
            for i, decision in enumerate(decisions_captured[-5:], 1):
                print(f"  {i}. {decision}")
                
        else:
            print("\n❌ ERROR: No decisions were made!")
        
        # Check JSON parsing
        debug_dir = Path("logs/llm_debug")
        if debug_dir.exists():
            latest_files = sorted(debug_dir.glob("*.json"))[-10:]
            errors = 0
            for file in latest_files:
                with open(file, 'r') as f:
                    data = json.load(f)
                    if "Failed to parse" in data.get('response', ''):
                        errors += 1
            
            print(f"\n🔧 JSON Parsing: {len(latest_files) - errors}/{len(latest_files)} successful")
            
        # Financial performance
        print(f"\n💰 Financial Performance:")
        print(f"  Final Capital: ${result.metrics.final_capital:,.2f}")
        print(f"  Total Return: {result.metrics.total_return:.2%}")
        print(f"  Sharpe Ratio: {result.metrics.sharpe_ratio:.2f}")
        
    except Exception as e:
        print(f"\n❌ Error during test: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        await engine._cleanup()
        print("\n✅ Test cleanup completed")

if __name__ == "__main__":
    print("🎯 Final Comprehensive BUY/SELL/HOLD Test")
    print("This test validates the complete decision-making pipeline")
    print("with all JSON parsing improvements implemented\n")
    
    asyncio.run(final_test())
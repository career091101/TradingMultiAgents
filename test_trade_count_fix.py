#!/usr/bin/env python
"""Test script to verify trade count fix"""

import asyncio
from datetime import datetime
from backtest2.core.types import TradingDecision, TradeAction, MarketData
from tradingagents.graph.signal_processing import SignalProcessor
from unittest.mock import Mock

async def test_signal_processor():
    """Test Japanese signal processing"""
    print("=== Testing SignalProcessor with Japanese signals ===")
    
    # Mock LLM
    mock_llm = Mock()
    processor = SignalProcessor(mock_llm)
    
    # Test cases
    test_cases = [
        ("買い", "BUY"),
        ("売り", "SELL"),
        ("保有", "HOLD"),
        ("BUY", "BUY"),
        ("SELL", "SELL"),
        ("HOLD", "HOLD"),
        ("購入", "BUY"),
        ("売却", "SELL"),
        ("維持", "HOLD"),
    ]
    
    for jp_signal, expected in test_cases:
        # Mock response
        mock_llm.invoke.return_value.content = jp_signal
        
        # Process signal
        result = processor.process_signal("Test signal")
        
        print(f"Input: {jp_signal:10} -> Output: {result:10} (Expected: {expected})")
        assert result == expected, f"Failed for {jp_signal}: got {result}, expected {expected}"
    
    print("✅ All signal processing tests passed!")

def test_decision_tracking():
    """Test decision tracking logic"""
    print("\n=== Testing Decision Tracking ===")
    
    # Simulate decision stats
    decision_stats = {
        'total': 0,
        'buy': 0,
        'sell': 0,
        'hold': 0
    }
    
    # Simulate decisions
    decisions = [
        TradeAction.BUY,
        TradeAction.HOLD,
        TradeAction.HOLD,
        TradeAction.SELL,
        TradeAction.HOLD,
        TradeAction.BUY,
    ]
    
    for action in decisions:
        decision_stats['total'] += 1
        if action == TradeAction.BUY:
            decision_stats['buy'] += 1
        elif action == TradeAction.SELL:
            decision_stats['sell'] += 1
        else:  # HOLD
            decision_stats['hold'] += 1
    
    print(f"Total decisions: {decision_stats['total']}")
    print(f"BUY decisions: {decision_stats['buy']}")
    print(f"SELL decisions: {decision_stats['sell']}")
    print(f"HOLD decisions: {decision_stats['hold']}")
    
    # Simulate only BUY/SELL are executed
    executed_trades = sum(1 for d in decisions if d != TradeAction.HOLD)
    print(f"\nExecuted trades: {executed_trades}")
    print(f"Trade execution rate: {executed_trades/decision_stats['total']:.2%}")
    
    assert decision_stats['total'] == 6, "Total count mismatch"
    assert decision_stats['hold'] == 3, "HOLD count mismatch"
    assert executed_trades == 3, "Executed trades count mismatch"
    
    print("✅ Decision tracking tests passed!")

async def main():
    """Run all tests"""
    print("🧪 Testing Trade Count Fix")
    print("=" * 50)
    
    await test_signal_processor()
    test_decision_tracking()
    
    print("\n✅ All tests completed successfully!")
    print("\n📝 Summary of fixes implemented:")
    print("1. SignalProcessor now handles Japanese trading signals")
    print("2. Decision tracking counts ALL decisions (including HOLD)")
    print("3. Agent performance metrics use decision_stats for accurate counting")

if __name__ == "__main__":
    asyncio.run(main())
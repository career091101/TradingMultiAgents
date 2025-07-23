"""Test script to verify MemoryStore get_recent_performance method"""

import asyncio
from datetime import datetime
from backtest2.memory import MemoryStore
from backtest2.core.types import Position, PositionStatus, TradingDecision, TradeAction
# DecisionContext will be mocked inline


async def test_memory_store_performance():
    """Test the new get_recent_performance method"""
    print("Testing MemoryStore.get_recent_performance() method...")
    
    # Create memory store
    memory_store = MemoryStore()
    
    # Test 1: No data should return empty metrics
    print("\n1. Testing with no data...")
    performance = await memory_store.get_recent_performance("AAPL")
    assert performance['trade_count'] == 0
    assert performance['win_rate'] == 0.0
    print("✅ Empty metrics returned correctly")
    
    # Test 2: Add some position closed memories
    print("\n2. Adding closed position memories...")
    
    # Add winning trade
    await memory_store.add('engine', {
        'type': 'position_closed',
        'outcome': {
            'position': {'symbol': 'AAPL'},
            'pnl': 500.0,
            'return_pct': 0.05
        }
    })
    
    # Add losing trade
    await memory_store.add('engine', {
        'type': 'position_closed',
        'outcome': {
            'position': {'symbol': 'AAPL'},
            'pnl': -200.0,
            'return_pct': -0.02
        }
    })
    
    # Add another winning trade
    await memory_store.add('engine', {
        'type': 'position_closed',
        'outcome': {
            'position': {'symbol': 'AAPL'},
            'pnl': 300.0,
            'return_pct': 0.03
        }
    })
    
    # Add a trade for different symbol (should not be included)
    await memory_store.add('engine', {
        'type': 'position_closed',
        'outcome': {
            'position': {'symbol': 'GOOGL'},
            'pnl': 1000.0,
            'return_pct': 0.10
        }
    })
    
    # Test performance metrics
    performance = await memory_store.get_recent_performance("AAPL")
    
    print(f"Trade count: {performance['trade_count']}")
    print(f"Win rate: {performance['win_rate']:.2%}")
    print(f"Average return: {performance['avg_return']:.2%}")
    print(f"Recent P&L: ${performance['recent_pnl']:.2f}")
    
    assert performance['trade_count'] == 3
    assert performance['win_rate'] == 2/3  # 2 wins out of 3 trades
    assert abs(performance['avg_return'] - 0.02) < 0.001  # (0.05 - 0.02 + 0.03) / 3
    assert performance['recent_pnl'] == 600.0  # 500 - 200 + 300
    
    print("✅ Performance metrics calculated correctly")
    
    # Test 3: Test store_decision method
    print("\n3. Testing store_decision method...")
    
    # Create mock decision and context
    class MockDecision:
        symbol = "AAPL"
        action = TradeAction.BUY
        confidence = 0.8
        reasoning = "Strong bullish signals"
    
    class MockContext:
        timestamp = datetime.now()
        portfolio_state = type('obj', (object,), {'total_value': 100000})()
        risk_metrics = {'exposure': 0.5}
        recent_performance = {'win_rate': 0.6}
    
    decision = MockDecision()
    context = MockContext()
    
    await memory_store.store_decision(decision, context)
    
    # Verify decision was stored
    decision_memories = await memory_store.get_recent('decision_store', limit=1)
    assert len(decision_memories) == 1
    assert decision_memories[0]['symbol'] == 'AAPL'
    assert decision_memories[0]['action'] == 'BUY'
    
    print("✅ Decision stored correctly")
    
    print("\n✅ All MemoryStore tests passed!")
    return True


if __name__ == "__main__":
    success = asyncio.run(test_memory_store_performance())
    if success:
        print("\n🎉 MemoryStore performance methods are working correctly!")
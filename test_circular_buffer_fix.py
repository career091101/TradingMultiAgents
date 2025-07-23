"""Test script to verify CircularBuffer fixes"""

import asyncio
from datetime import datetime, timedelta
from backtest2.core.config import BacktestConfig, TimeRange, LLMConfig, RiskConfig, RiskProfile
from backtest2.core.engine import BacktestEngine
from pathlib import Path


async def test_circular_buffer_fixes():
    """Test that CircularBuffer iteration is fixed throughout the system"""
    print("Testing CircularBuffer fixes...")
    
    # Create test configuration
    config = BacktestConfig(
        name="CircularBuffer Test",
        symbols=["AAPL"],
        time_range=TimeRange(
            start=datetime.now() - timedelta(days=7),
            end=datetime.now()
        ),
        initial_capital=100000.0,
        random_seed=42,
        max_positions=5,
        position_limits={
            RiskProfile.AGGRESSIVE: 0.3,
            RiskProfile.NEUTRAL: 0.2,
            RiskProfile.CONSERVATIVE: 0.1
        },
        llm_config=LLMConfig(
            deep_think_model="gpt-4",
            quick_think_model="gpt-4",
            temperature=0.7,
            max_tokens=1000,
            timeout=30
        ),
        data_sources=["finnhub"],
        result_dir=Path("results/circular_buffer_test"),
        slippage=0.001,
        commission=0.001,
        risk_free_rate=0.05,
        benchmark="SPY",
        risk_config=RiskConfig(
            position_limits={
                RiskProfile.AGGRESSIVE: 0.3,
                RiskProfile.NEUTRAL: 0.2,
                RiskProfile.CONSERVATIVE: 0.1
            },
            max_positions=5,
            stop_loss=0.1,
            take_profit=0.2
        )
    )
    
    # Create engine
    engine = BacktestEngine(config)
    
    # Test 1: Test position manager get_portfolio_state()
    print("\n1. Testing PositionManager.get_portfolio_state()...")
    try:
        # Add some dummy closed positions
        from backtest2.core.types import Position, PositionStatus
        for i in range(5):
            pos = Position(
                symbol=f"TEST{i}",
                entry_date=datetime.now(),
                entry_price=100.0,
                quantity=10,
                entry_reason="Test",
                realized_pnl=(i - 2) * 100  # Mix of profits and losses
            )
            pos.status = PositionStatus.CLOSED
            engine.position_manager.closed_positions.append(pos)
        
        # This should not raise "CircularBuffer is not iterable" error
        state = engine.position_manager.get_portfolio_state()
        print(f"✅ Portfolio state retrieved successfully. Realized P&L: ${state.realized_pnl:.2f}")
    except Exception as e:
        print(f"❌ Error in get_portfolio_state(): {e}")
        return False
    
    # Test 2: Test engine _get_daily_transactions()
    print("\n2. Testing BacktestEngine._get_daily_transactions()...")
    try:
        # Add some dummy transactions
        from backtest2.core.types import Transaction, TradeAction
        for i in range(5):
            trans = Transaction(
                timestamp=datetime.now() - timedelta(days=i),
                symbol=f"TEST{i}",
                action=TradeAction.BUY if i % 2 == 0 else TradeAction.SELL,
                quantity=10,
                price=100.0 + i,
                commission=1.0,
                slippage=0.1,
                total_cost=1001.1
            )
            engine.transactions.append(trans)
        
        # This should not raise "CircularBuffer is not iterable" error
        daily_trans = engine._get_daily_transactions(datetime.now())
        print(f"✅ Daily transactions retrieved successfully. Count: {len(daily_trans)}")
    except Exception as e:
        print(f"❌ Error in _get_daily_transactions(): {e}")
        return False
    
    # Test 3: Test transaction history iteration
    print("\n3. Testing transaction history access...")
    try:
        # Add transactions to position manager's transaction history
        for i in range(5):
            trans = Transaction(
                timestamp=datetime.now(),
                symbol=f"TEST{i}",
                action=TradeAction.BUY,
                quantity=10,
                price=100.0,
                commission=1.0,
                slippage=0.1,
                total_cost=1001.1
            )
            engine.position_manager.transaction_history.append(trans)
        
        # Access transactions via get_all()
        all_transactions = engine.position_manager.transaction_history.get_all()
        print(f"✅ Transaction history accessed successfully. Count: {len(all_transactions)}")
    except Exception as e:
        print(f"❌ Error accessing transaction history: {e}")
        return False
    
    print("\n✅ All CircularBuffer fixes verified successfully!")
    return True


if __name__ == "__main__":
    success = asyncio.run(test_circular_buffer_fixes())
    if success:
        print("\n🎉 CircularBuffer iteration issues have been fixed!")
    else:
        print("\n❌ Some CircularBuffer issues remain.")
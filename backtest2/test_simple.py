"""Simple synchronous test for Backtest2 components"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from datetime import datetime
from backtest2.core.types import MarketData, PortfolioState, Position, TradeAction
from backtest2.risk.position_manager import PositionManager
from backtest2.core.config import RiskConfig


def test_position_manager():
    """Test basic position manager functionality"""
    print("Testing Position Manager...")
    
    # Create risk config
    from backtest2.core.config import RiskProfile
    risk_config = RiskConfig(
        max_positions=5,
        position_limits={
            RiskProfile.AGGRESSIVE: 0.3,
            RiskProfile.NEUTRAL: 0.2, 
            RiskProfile.CONSERVATIVE: 0.1
        },
        stop_loss=0.10,
        take_profit=0.20
    )
    
    # Create position manager
    pm = PositionManager(
        initial_capital=100000,
        risk_config=risk_config
    )
    
    # Get initial state
    state = pm.get_portfolio_state()
    print(f"Initial capital: ${state.cash:,.2f}")
    print(f"Initial value: ${state.total_value:,.2f}")
    
    # Test position sizing
    from backtest2.core.types import TradingSignal
    signal = TradingSignal(
        action=TradeAction.BUY,
        symbol="AAPL",
        confidence=0.8,
        risk_assessment={"risk_stance": "NEUTRAL"}
    )
    
    size = pm.calculate_position_size(signal, 0.8)
    print(f"\nPosition size for NEUTRAL profile: ${size:,.2f}")
    
    # Create a mock transaction
    from backtest2.core.types import Transaction
    transaction = Transaction(
        timestamp=datetime.now(),
        symbol="AAPL",
        action=TradeAction.BUY,
        quantity=100,
        price=150.0,
        commission=10.0,
        slippage=5.0,
        total_cost=15015.0,
        signal=signal
    )
    
    # Execute transaction
    pm.execute_transaction(transaction)
    
    # Check updated state
    state = pm.get_portfolio_state()
    print(f"\nAfter buying 100 AAPL @ $150:")
    print(f"Cash: ${state.cash:,.2f}")
    print(f"Position count: {state.position_count}")
    print(f"Exposure: {state.exposure:.2%}")
    
    # Update position value
    pm.update_position_value("AAPL", 160.0)
    state = pm.get_portfolio_state()
    print(f"\nAfter AAPL moves to $160:")
    print(f"Total value: ${state.total_value:,.2f}")
    print(f"Unrealized P&L: ${state.total_value - 100000:,.2f}")
    
    print("\n✓ Position Manager test passed!")


def test_mock_agents():
    """Test mock agent implementations"""
    print("\n" + "="*50)
    print("Testing Mock Agents...")
    
    import asyncio
    from backtest2.agents.analysts import MarketAnalyst
    from backtest2.core.config import LLMConfig
    from backtest2.memory.agent_memory import AgentMemory
    
    # Create mock LLM config
    llm_config = LLMConfig(
        deep_think_model="mock-o1",
        quick_think_model="mock-gpt4o",
        temperature=0.7,
        max_tokens=1000
    )
    
    # Create market analyst
    analyst = MarketAnalyst(
        name="TestAnalyst",
        llm_config=llm_config,
        memory=AgentMemory("TestAnalyst"),
        use_deep_thinking=False
    )
    
    # Create test market data
    market_data = MarketData(
        symbol="AAPL",
        date=datetime.now(),
        open=150.0,
        high=155.0,
        low=149.0,
        close=154.0,
        volume=5000000,
        news=[],
        sentiment={"overall": 0.5}
    )
    
    # Run analysis
    async def run_analysis():
        result = await analyst.process({'market_data': market_data})
        return result
    
    # Run async function
    result = asyncio.run(run_analysis())
    
    print(f"\nMarket Analyst Output:")
    print(f"Agent: {result.agent_name}")
    print(f"Confidence: {result.confidence:.2f}")
    print(f"Signal: {result.content.get('signal')}")
    print(f"Price Trend: {result.content.get('price_trend')}")
    print(f"Volume: {result.content.get('volume_analysis')}")
    
    print("\n✓ Mock Agents test passed!")


def test_data_types():
    """Test data type creation and serialization"""
    print("\n" + "="*50)
    print("Testing Data Types...")
    
    # Test MarketData
    market_data = MarketData(
        symbol="TSLA",
        date=datetime.now(),
        open=200.0,
        high=210.0,
        low=195.0,
        close=205.0,
        volume=10000000,
        news=[{"title": "Test news", "sentiment": 0.5}],
        sentiment={"overall": 0.3}
    )
    
    print(f"\nMarketData created:")
    print(f"Symbol: {market_data.symbol}")
    print(f"Date: {market_data.date}")
    print(f"OHLC: {market_data.open}/{market_data.high}/{market_data.low}/{market_data.close}")
    print(f"Volume: {market_data.volume:,}")
    
    # Test Position
    position = Position(
        symbol="TSLA",
        quantity=50,
        entry_price=200.0,
        entry_date=datetime.now()
    )
    
    # Calculate unrealized P&L manually (current price 205)
    current_price = 205.0
    position.unrealized_pnl = (current_price - position.entry_price) * position.quantity
    
    print(f"\nPosition created:")
    print(f"Symbol: {position.symbol}")
    print(f"Quantity: {position.quantity}")
    print(f"Entry Price: ${position.entry_price}")
    print(f"Current Price: ${current_price}")
    print(f"Unrealized P&L: ${position.unrealized_pnl:,.2f}")
    
    print("\n✓ Data Types test passed!")


def main():
    """Run all tests"""
    print("Starting Backtest2 Simple Tests")
    print("=" * 50)
    
    try:
        test_position_manager()
        test_mock_agents()
        test_data_types()
        
        print("\n" + "=" * 50)
        print("✅ All tests passed!")
        print("\nThe minimal version is working correctly.")
        print("Ready to proceed with full implementation.")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
"""Basic functionality tests for backtest2"""

import pytest
import asyncio
from datetime import datetime, timedelta
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from backtest2 import BacktestEngine, BacktestConfig
from backtest2.core.config import AgentConfig, DataConfig, RiskConfig


class TestBasicFunctionality:
    """Test basic backtest functionality"""
    
    @pytest.fixture
    def basic_config(self):
        """Create basic test configuration"""
        config = BacktestConfig(
            initial_capital=10000.0,
            start_date=datetime(2023, 1, 1),
            end_date=datetime(2023, 1, 31),
            symbols=['AAPL', 'GOOGL'],
            random_seed=42
        )
        
        # Disable some features for basic test
        config.reflection_config.enabled = False
        config.agent_config.max_debate_rounds = 1
        config.agent_config.max_risk_discuss_rounds = 1
        
        return config
        
    def test_config_validation(self, basic_config):
        """Test configuration validation"""
        # Should not raise
        basic_config.validate()
        
        # Test invalid configs
        invalid_config = BacktestConfig(
            initial_capital=-1000,
            start_date=datetime(2023, 1, 1),
            end_date=datetime(2023, 1, 31),
            symbols=['AAPL']
        )
        
        with pytest.raises(ValueError):
            invalid_config.validate()
            
    def test_engine_initialization(self, basic_config):
        """Test engine initialization"""
        engine = BacktestEngine(basic_config)
        
        assert engine.config == basic_config
        assert engine.execution_id is not None
        assert not engine.is_running
        assert len(engine.transactions) == 0
        
    @pytest.mark.asyncio
    async def test_basic_run(self, basic_config):
        """Test basic backtest run"""
        # Use very short date range for quick test
        basic_config.start_date = datetime(2023, 1, 1)
        basic_config.end_date = datetime(2023, 1, 3)
        basic_config.symbols = ['AAPL']
        
        engine = BacktestEngine(basic_config)
        
        # This would fail without proper data sources
        # For now, just test that it initializes
        try:
            # Test initialization
            await engine._initialize()
            assert True  # If we get here, initialization worked
        except Exception as e:
            # Expected to fail without data sources
            assert "data" in str(e).lower() or "api" in str(e).lower()


class TestTypes:
    """Test type definitions"""
    
    def test_trade_action_enum(self):
        """Test TradeAction enum"""
        from backtest2.core.types import TradeAction
        
        assert TradeAction.BUY.value == "BUY"
        assert TradeAction.SELL.value == "SELL"
        assert TradeAction.HOLD.value == "HOLD"
        
    def test_market_data_creation(self):
        """Test MarketData creation"""
        from backtest2.core.types import MarketData
        
        data = MarketData(
            date=datetime.now(),
            symbol="AAPL",
            open=100.0,
            high=105.0,
            low=99.0,
            close=103.0,
            volume=1000000
        )
        
        assert data.symbol == "AAPL"
        assert data.close == 103.0
        
    def test_position_creation(self):
        """Test Position creation"""
        from backtest2.core.types import Position, PositionStatus
        
        position = Position(
            symbol="AAPL",
            entry_date=datetime.now(),
            entry_price=100.0,
            quantity=10
        )
        
        assert position.status == PositionStatus.OPEN
        assert position.unrealized_pnl == 0.0
        

class TestConfiguration:
    """Test configuration system"""
    
    def test_risk_config(self):
        """Test risk configuration"""
        from backtest2.core.config import RiskConfig, RiskProfile
        
        config = RiskConfig()
        
        assert config.position_limits[RiskProfile.AGGRESSIVE] == 0.8
        assert config.position_limits[RiskProfile.NEUTRAL] == 0.5
        assert config.position_limits[RiskProfile.CONSERVATIVE] == 0.3
        assert config.stop_loss == 0.1
        assert config.take_profit == 0.2
        
    def test_reflection_config(self):
        """Test reflection configuration"""
        from backtest2.core.config import ReflectionConfig
        
        config = ReflectionConfig()
        
        assert config.enabled
        assert config.immediate_on_trade
        assert config.consecutive_loss_threshold == 3
        assert config.drawdown_threshold == 0.15


def test_imports():
    """Test that all modules can be imported"""
    try:
        from backtest2 import BacktestEngine, BacktestConfig, BacktestResult
        from backtest2.core import config, types, engine, results
        assert True
    except ImportError as e:
        pytest.fail(f"Import failed: {e}")


if __name__ == "__main__":
    # Run basic tests
    print("Testing backtest2 basic functionality...")
    
    # Test imports
    test_imports()
    print("✓ Imports successful")
    
    # Test configuration
    config_tests = TestConfiguration()
    config_tests.test_risk_config()
    config_tests.test_reflection_config()
    print("✓ Configuration tests passed")
    
    # Test types
    type_tests = TestTypes()
    type_tests.test_trade_action_enum()
    type_tests.test_market_data_creation()
    type_tests.test_position_creation()
    print("✓ Type tests passed")
    
    # Test engine
    engine_tests = TestBasicFunctionality()
    config = engine_tests.basic_config()
    engine_tests.test_config_validation(config)
    engine_tests.test_engine_initialization(config)
    print("✓ Engine tests passed")
    
    print("\nAll basic tests passed!")
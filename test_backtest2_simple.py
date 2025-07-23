"""Simple test of backtest2 module"""

import sys
sys.path.append('.')

print("Testing backtest2 imports...")

try:
    # Test basic imports
    from backtest2.core.config import BacktestConfig, RiskProfile, ReflectionLevel
    print("✓ Config imports successful")
    
    from backtest2.core.types import TradeAction, MarketData, Position
    print("✓ Types imports successful")
    
    # Test configuration
    from datetime import datetime
    
    config = BacktestConfig(
        initial_capital=10000.0,
        start_date=datetime(2023, 1, 1),
        end_date=datetime(2023, 1, 31),
        symbols=['AAPL']
    )
    
    print(f"✓ Created config: {config.initial_capital} capital, {len(config.symbols)} symbols")
    
    # Test validation
    try:
        config.validate()
        print("✓ Config validation passed")
    except Exception as e:
        print(f"✗ Config validation failed: {e}")
        
    # Test risk profiles
    print(f"✓ Risk profiles: {list(RiskProfile)}")
    
    # Test trade actions
    print(f"✓ Trade actions: {list(TradeAction)}")
    
    print("\nBasic functionality tests passed!")
    
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
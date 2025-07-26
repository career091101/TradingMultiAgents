#!/usr/bin/env python3
"""
Diagnostic script for Backtest2 configuration issues
"""

import sys
import os
import importlib
import traceback
from pathlib import Path

def diagnose():
    print("=" * 80)
    print("BACKTEST2 DIAGNOSTIC REPORT")
    print("=" * 80)
    
    # 1. Check Python environment
    print("\n1. PYTHON ENVIRONMENT")
    print(f"Python version: {sys.version}")
    print(f"Executable: {sys.executable}")
    
    # 2. Check Python path
    print("\n2. PYTHON PATH")
    for i, path in enumerate(sys.path[:10]):
        print(f"  [{i}] {path}")
    
    # 3. Try to import backtest2
    print("\n3. IMPORT TEST")
    try:
        import backtest2
        print(f"✓ backtest2 imported from: {backtest2.__file__ if hasattr(backtest2, '__file__') else 'Unknown'}")
    except ImportError as e:
        print(f"✗ Failed to import backtest2: {e}")
        return
    
    # 4. Check BacktestConfig
    print("\n4. BACKTEST CONFIG CHECK")
    try:
        from backtest2.core.config import BacktestConfig
        print(f"✓ BacktestConfig imported from: {BacktestConfig.__module__}")
        
        # Check if it's a dataclass
        import dataclasses
        is_dataclass = dataclasses.is_dataclass(BacktestConfig)
        print(f"✓ Is dataclass: {is_dataclass}")
        
        if is_dataclass:
            fields = BacktestConfig.__dataclass_fields__
            print(f"✓ Number of fields: {len(fields)}")
            print(f"✓ Has 'debug' field: {'debug' in fields}")
            
            if 'debug' in fields:
                debug_field = fields['debug']
                print(f"  - Type: {debug_field.type}")
                print(f"  - Default: {debug_field.default}")
        
        # Try to create instance
        print("\n5. INSTANCE CREATION TEST")
        try:
            config = BacktestConfig(
                name="test",
                symbols=["AAPL"],
                initial_capital=10000,
                debug=True
            )
            print(f"✓ Instance created successfully")
            print(f"✓ debug attribute value: {config.debug}")
            print(f"✓ hasattr(config, 'debug'): {hasattr(config, 'debug')}")
        except Exception as e:
            print(f"✗ Failed to create instance: {e}")
            traceback.print_exc()
            
    except Exception as e:
        print(f"✗ Failed to check BacktestConfig: {e}")
        traceback.print_exc()
    
    # 6. Check for duplicate modules
    print("\n6. MODULE DUPLICATION CHECK")
    backtest2_modules = [name for name in sys.modules if name.startswith('backtest2')]
    print(f"Loaded backtest2 modules: {len(backtest2_modules)}")
    for mod_name in sorted(backtest2_modules)[:10]:
        mod = sys.modules[mod_name]
        if hasattr(mod, '__file__'):
            print(f"  - {mod_name}: {mod.__file__}")
    
    # 7. Check file modification times
    print("\n7. FILE TIMESTAMPS")
    config_file = Path("/Users/y-sato/TradingAgents2/backtest2/core/config.py")
    if config_file.exists():
        import datetime
        mtime = datetime.datetime.fromtimestamp(config_file.stat().st_mtime)
        print(f"config.py last modified: {mtime}")
    
    # 8. Force reload test
    print("\n8. FORCE RELOAD TEST")
    try:
        import backtest2.core.config
        importlib.reload(backtest2.core.config)
        from backtest2.core.config import BacktestConfig as ReloadedConfig
        
        fields = ReloadedConfig.__dataclass_fields__ if hasattr(ReloadedConfig, '__dataclass_fields__') else {}
        print(f"✓ After reload - Has 'debug' field: {'debug' in fields}")
    except Exception as e:
        print(f"✗ Reload failed: {e}")
    
    print("\n" + "=" * 80)
    print("END OF DIAGNOSTIC REPORT")
    print("=" * 80)

if __name__ == "__main__":
    diagnose()
#!/usr/bin/env python3
"""Collect comprehensive debug information for backtest2 issues"""

import os
import sys
import json
import subprocess
from datetime import datetime as dt
from pathlib import Path

def run_command(cmd):
    """Run command and return output"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return result.stdout + result.stderr
    except Exception as e:
        return f"Error running command: {e}"

def main():
    print("=== Backtest2 Debug Information Collection ===")
    print(f"Timestamp: {dt.now().isoformat()}")
    print()
    
    # 1. Python Environment
    print("1. Python Environment:")
    print("-" * 50)
    print(f"Python Version: {sys.version}")
    print(f"Python Executable: {sys.executable}")
    print()
    
    # 2. Check WebUI Process
    print("2. WebUI Process Status:")
    print("-" * 50)
    ps_output = run_command("ps aux | grep -E '(streamlit|python.*app.py)' | grep -v grep")
    print(ps_output if ps_output else "No WebUI process found")
    print()
    
    # 3. Port Status
    print("3. Port 8501 Status:")
    print("-" * 50)
    port_output = run_command("lsof -i :8501")
    print(port_output if port_output else "Port 8501 is not in use")
    print()
    
    # 4. Recent Error Logs
    print("4. Recent Error Logs:")
    print("-" * 50)
    
    log_files = [
        "TradingMultiAgents/webui.log",
        "webui_safe_mode.log",
        "TradingMultiAgents/streamlit.log"
    ]
    
    for log_file in log_files:
        if os.path.exists(log_file):
            print(f"\n--- {log_file} (last 50 lines with errors) ---")
            error_lines = run_command(f"tail -100 {log_file} | grep -E '(ERROR|CRITICAL|Exception|Traceback|failed)' | tail -50")
            print(error_lines if error_lines else "No recent errors found")
    
    # 5. File Permissions
    print("\n5. Critical File Permissions:")
    print("-" * 50)
    critical_files = [
        "backtest2/agents/llm_client.py",
        "backtest2/agents/agent_adapter.py",
        "backtest2/core/types.py",
        "TradingMultiAgents/webui/components/backtest2.py"
    ]
    
    for file in critical_files:
        if os.path.exists(file):
            stat = os.stat(file)
            print(f"{file}: {oct(stat.st_mode)[-3:]}")
    
    # 6. Module Import Test
    print("\n6. Module Import Test:")
    print("-" * 50)
    
    try:
        sys.path.insert(0, os.getcwd())
        from backtest2.agents.llm_client import OpenAILLMClient, BacktestJSONEncoder
        print("✓ llm_client imports successfully")
        
        # Test JSON encoder
        from backtest2.core.types import TradeAction, MarketData
        from datetime import datetime
        from decimal import Decimal
        
        test_data = {
            "action": TradeAction.BUY,
            "date": dt.now(),
            "price": Decimal("100.50"),
            "market_data": MarketData(
                date=dt.now(),
                symbol="TEST",
                open=100.0,
                high=101.0,
                low=99.0,
                close=100.5,
                volume=1000000,
                adjusted_close=100.5
            )
        }
        
        try:
            json_str = json.dumps(test_data, cls=BacktestJSONEncoder)
            print("✓ JSON serialization works")
            print(f"  Sample output: {json_str[:100]}...")
        except Exception as e:
            print(f"✗ JSON serialization failed: {e}")
            
    except Exception as e:
        print(f"✗ Import failed: {e}")
    
    # 7. OpenAI API Key Status
    print("\n7. OpenAI API Key Status:")
    print("-" * 50)
    api_key = os.environ.get("OPENAI_API_KEY", "")
    if api_key:
        print(f"✓ API Key set (length: {len(api_key)}, starts with: {api_key[:7]}...)")
    else:
        print("✗ API Key not set")
    
    # 8. Memory Usage
    print("\n8. System Memory:")
    print("-" * 50)
    mem_output = run_command("vm_stat | head -5")
    print(mem_output)
    
    # 9. Test Backtest2 Configuration
    print("\n9. Backtest2 Configuration Test:")
    print("-" * 50)
    
    try:
        from backtest2.core.config import BacktestConfig, LLMConfig
        
        config = BacktestConfig()
        print(f"✓ Default config loaded")
        print(f"  Deep think model: {config.llm_config.deep_think_model}")
        print(f"  Quick think model: {config.llm_config.quick_think_model}")
        print(f"  Max tokens: {config.llm_config.max_tokens}")
        
    except Exception as e:
        print(f"✗ Config load failed: {e}")
    
    # 10. WebUI Connection Test
    print("\n10. WebUI Connection Test:")
    print("-" * 50)
    curl_output = run_command("curl -s -o /dev/null -w '%{http_code}' http://localhost:8501")
    if curl_output == "200":
        print("✓ WebUI is accessible")
    else:
        print(f"✗ WebUI not accessible (HTTP status: {curl_output})")
    
    print("\n=== Debug collection complete ===")

if __name__ == "__main__":
    main()
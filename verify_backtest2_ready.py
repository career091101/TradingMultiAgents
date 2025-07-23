#!/usr/bin/env python3
"""
Verify that backtest2 system is ready to run
"""

import os
import sys
import importlib.util
import ast

def check_syntax(file_path):
    """Check if Python file has syntax errors"""
    try:
        with open(file_path, 'r') as f:
            ast.parse(f.read())
        return True, None
    except SyntaxError as e:
        return False, str(e)

def check_imports(module_path):
    """Check if module can be imported"""
    try:
        spec = importlib.util.spec_from_file_location("test_module", module_path)
        module = importlib.util.module_from_spec(spec)
        return True, None
    except Exception as e:
        return False, str(e)

def verify_backtest2():
    """Verify backtest2 system readiness"""
    print("🔍 Verifying backtest2 system...")
    
    critical_files = [
        "/Users/y-sato/TradingAgents2/backtest2/agents/orchestrator.py",
        "/Users/y-sato/TradingAgents2/backtest2/agents/agent_adapter.py",
        "/Users/y-sato/TradingAgents2/backtest2/core/types.py",
        "/Users/y-sato/TradingAgents2/backtest2/agents/llm_client.py",
        "/Users/y-sato/TradingAgents2/TradingMultiAgents/webui/components/backtest2.py"
    ]
    
    all_good = True
    
    # Check syntax
    print("\n📝 Checking syntax...")
    for file_path in critical_files:
        if os.path.exists(file_path):
            success, error = check_syntax(file_path)
            if success:
                print(f"✅ {os.path.basename(file_path)}: Syntax OK")
            else:
                print(f"❌ {os.path.basename(file_path)}: Syntax Error - {error}")
                all_good = False
        else:
            print(f"⚠️  {os.path.basename(file_path)}: File not found")
    
    # Check critical patterns
    print("\n🔍 Checking critical patterns...")
    
    # Check orchestrator context passing
    with open("/Users/y-sato/TradingAgents2/backtest2/agents/orchestrator.py", 'r') as f:
        content = f.read()
        if "context.to_dict() if hasattr(context, 'to_dict') else context" in content:
            print("✅ Context passing uses to_dict() properly")
        else:
            print("⚠️  Some context passing might not use to_dict()")
    
    # Check agent adapter portfolio handling
    with open("/Users/y-sato/TradingAgents2/backtest2/agents/agent_adapter.py", 'r') as f:
        content = f.read()
        if "(portfolio.cash if portfolio else 0)" in content:
            print("✅ Portfolio None checks in place")
        else:
            print("⚠️  Some portfolio access might not have None checks")
    
    # Check types.py has to_dict methods
    with open("/Users/y-sato/TradingAgents2/backtest2/core/types.py", 'r') as f:
        content = f.read()
        if "def to_dict(self)" in content:
            print("✅ Types have to_dict() methods")
        else:
            print("❌ Types missing to_dict() methods")
            all_good = False
    
    # Check LLM client has JSON encoder
    with open("/Users/y-sato/TradingAgents2/backtest2/agents/llm_client.py", 'r') as f:
        content = f.read()
        if "BacktestJSONEncoder" in content:
            print("✅ Custom JSON encoder present")
        else:
            print("⚠️  Custom JSON encoder might be missing")
    
    # Summary
    print("\n" + "="*50)
    if all_good:
        print("✅ Backtest2 system appears ready!")
        print("\nNext steps:")
        print("1. Restart the WebUI")
        print("2. Run a backtest")
        print("3. Monitor logs for any runtime errors")
    else:
        print("❌ Issues found! Please fix before running backtest.")
        
    return all_good

if __name__ == "__main__":
    success = verify_backtest2()
    sys.exit(0 if success else 1)
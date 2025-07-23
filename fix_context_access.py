#!/usr/bin/env python3
"""
Fix context access in agent_adapter.py to handle both dict and object formats
"""

import re
import os

def fix_context_access(file_path):
    """Fix context access patterns in the file"""
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Pattern to fix context.get() calls
    # Replace context = input_data.get('context', {}) followed by context.get() patterns
    
    # First, let's make sure all context accesses handle both formats
    replacements = [
        # Fix timestamp access
        (
            r"context\.get\('timestamp', datetime\.now\(\)\)",
            "(context.get('timestamp', datetime.now()) if isinstance(context, dict) else getattr(context, 'timestamp', datetime.now()))"
        ),
        # Fix market_state access
        (
            r"context\.get\('market_state', \{\}\)\.get\('symbol', 'UNKNOWN'\)",
            "(context.get('market_state', {}).get('symbol', 'UNKNOWN') if isinstance(context, dict) else getattr(getattr(context, 'market_state', {}), 'symbol', 'UNKNOWN'))"
        ),
        # Fix general pattern for context.get()
        (
            r"context\.get\('(\w+)', ([^)]+)\)",
            r"(context.get('\1', \2) if isinstance(context, dict) else getattr(context, '\1', \2))"
        ),
    ]
    
    original_content = content
    for pattern, replacement in replacements:
        content = re.sub(pattern, replacement, content)
    
    # Write back if changed
    if content != original_content:
        with open(file_path, 'w') as f:
            f.write(content)
        print(f"Fixed context access patterns in {file_path}")
        return True
    return False

def main():
    """Fix context access in agent_adapter.py"""
    file_path = "/Users/y-sato/TradingAgents2/backtest2/agents/agent_adapter.py"
    
    if os.path.exists(file_path):
        if fix_context_access(file_path):
            print("✅ Context access patterns fixed successfully!")
        else:
            print("ℹ️  No changes needed.")
    else:
        print(f"❌ File not found: {file_path}")

if __name__ == "__main__":
    main()
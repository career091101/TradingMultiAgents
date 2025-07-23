#!/usr/bin/env python3
"""
Fix backtest2 schema definitions to use proper JSON Schema format
"""

import re
import os

def fix_schema_definitions(file_path):
    """Fix schema definitions in the given file"""
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Pattern to match incorrect schema definitions
    patterns = [
        # Fix string type descriptions
        (r'"(\w+)"\s*:\s*"string\s*\([^)]+\)"', lambda m: f'"{m.group(1)}": {{"type": "string"}}'),
        # Fix number type descriptions
        (r'"(\w+)"\s*:\s*"number\s*\([^)]+\)"', lambda m: f'"{m.group(1)}": {{"type": "number"}}'),
        # Fix boolean type descriptions
        (r'"(\w+)"\s*:\s*"boolean"', lambda m: f'"{m.group(1)}": {{"type": "boolean"}}'),
        # Fix array type descriptions
        (r'"(\w+)"\s*:\s*"array\s*\([^)]+\)"', lambda m: f'"{m.group(1)}": {{"type": "array"}}'),
        # Fix object type descriptions
        (r'"(\w+)"\s*:\s*"object\s*\([^)]+\)"', lambda m: f'"{m.group(1)}": {{"type": "object"}}'),
        
        # Specific fixes for common patterns
        (r'"action"\s*:\s*"string \(BUY/SELL/HOLD\)"', '"action": {"type": "string", "enum": ["BUY", "SELL", "HOLD"]}'),
        (r'"confidence"\s*:\s*"number \(0-1\)"', '"confidence": {"type": "number", "minimum": 0, "maximum": 1}'),
        (r'"position_size"\s*:\s*"number \(0-1\)"', '"position_size": {"type": "number", "minimum": 0, "maximum": 1}'),
        (r'"sentiment"\s*:\s*"string \(positive/negative/neutral\)"', '"sentiment": {"type": "string", "enum": ["positive", "negative", "neutral"]}'),
        (r'"trend"\s*:\s*"string \(bullish/bearish/neutral\)"', '"trend": {"type": "string", "enum": ["bullish", "bearish", "neutral"]}'),
        (r'"risk_level"\s*:\s*"string \(low/medium/high\)"', '"risk_level": {"type": "string", "enum": ["low", "medium", "high"]}'),
        (r'"recommendation"\s*:\s*"string \(buy/hold/sell\)"', '"recommendation": {"type": "string", "enum": ["buy", "hold", "sell"]}'),
    ]
    
    # Apply all patterns
    original_content = content
    for pattern, replacement in patterns:
        content = re.sub(pattern, replacement, content)
    
    # Write back if changed
    if content != original_content:
        with open(file_path, 'w') as f:
            f.write(content)
        print(f"Fixed schema definitions in {file_path}")
        return True
    return False

def main():
    """Fix all agent adapter files"""
    agent_adapter_path = "/Users/y-sato/TradingAgents2/backtest2/agents/agent_adapter.py"
    
    if os.path.exists(agent_adapter_path):
        if fix_schema_definitions(agent_adapter_path):
            print("✅ Schema definitions fixed successfully!")
        else:
            print("ℹ️  No schema changes needed or already fixed.")
    else:
        print(f"❌ File not found: {agent_adapter_path}")

if __name__ == "__main__":
    main()
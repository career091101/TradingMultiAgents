#!/usr/bin/env python3
"""
Fix context handling in all agent adapter classes
"""

import os

def fix_agent_adapter():
    """Fix agent adapter to handle context properly"""
    
    file_path = "/Users/y-sato/TradingAgents2/backtest2/agents/agent_adapter.py"
    
    # Read the file
    with open(file_path, 'r') as f:
        lines = f.readlines()
    
    # Find all _generate_prompt methods and fix context handling
    in_generate_prompt = False
    modified = False
    new_lines = []
    
    for i, line in enumerate(lines):
        # Check if we're entering a _generate_prompt method
        if 'def _generate_prompt(self, input_data: Dict[str, Any]) -> str:' in line:
            in_generate_prompt = True
            new_lines.append(line)
            # Add context normalization at the start of the method
            indent = '        '  # 8 spaces for method body
            new_lines.append(f'{indent}# Normalize context to dict if it\'s an object\n')
            new_lines.append(f'{indent}context = input_data.get(\'context\', {{}})\n')
            new_lines.append(f'{indent}if hasattr(context, \'to_dict\'):\n')
            new_lines.append(f'{indent}    context = context.to_dict()\n')
            new_lines.append(f'{indent}    input_data[\'context\'] = context\n')
            new_lines.append(f'{indent}\n')
            modified = True
            continue
            
        # Skip lines that were trying to handle context in complex ways
        if in_generate_prompt and 'context = input_data.get(\'context\', {})' in line:
            # Skip this line as we already added it above
            continue
            
        # Check if we're exiting the method
        if in_generate_prompt and line.strip() and not line.startswith('        ') and not line.startswith('\t\t'):
            in_generate_prompt = False
            
        new_lines.append(line)
    
    # Write back
    if modified:
        with open(file_path, 'w') as f:
            f.writelines(new_lines)
        print(f"✅ Fixed context handling in {file_path}")
        return True
    
    return False

def simplify_context_access():
    """Simplify overly complex context access patterns"""
    
    file_path = "/Users/y-sato/TradingAgents2/backtest2/agents/agent_adapter.py"
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Fix overly complex patterns
    import re
    
    # Fix the complex timestamp pattern
    content = re.sub(
        r'\(\(context\.get\(\'timestamp\', datetime\.now\(\)\) if isinstance\(context, dict\) else getattr\(context, \'timestamp\', datetime\.now\(\)\)\) if isinstance\(context, dict\) else getattr\(context, \'timestamp\', datetime\.now\(\)\)\)',
        "context.get('timestamp', datetime.now())",
        content
    )
    
    # Fix the complex market_state pattern
    content = re.sub(
        r'\(\(context\.get\(\'market_state\', \{\}\) if isinstance\(context, dict\) else getattr\(context, \'market_state\', \{\}\)\)\.get\(\'symbol\', \'UNKNOWN\'\) if isinstance\(context, dict\) else getattr\(getattr\(context, \'market_state\', \{\}\), \'symbol\', \'UNKNOWN\'\)\)',
        "context.get('market_state', {}).get('symbol', 'UNKNOWN')",
        content
    )
    
    # Fix any remaining complex patterns
    content = re.sub(
        r'\(context\.get\(\'(\w+)\', ([^)]+)\) if isinstance\(context, dict\) else getattr\(context, \'\\1\', \\2\)\)',
        r"context.get('\1', \2)",
        content
    )
    
    with open(file_path, 'w') as f:
        f.write(content)
    
    print("✅ Simplified context access patterns")

def main():
    # First fix the adapter
    fix_agent_adapter()
    
    # Then simplify the patterns
    simplify_context_access()
    
    print("\n✅ All fixes applied successfully!")

if __name__ == "__main__":
    main()
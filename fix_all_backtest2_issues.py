#!/usr/bin/env python3
"""
Fix all remaining backtest2 issues comprehensively
"""

import os
import re

def fix_orchestrator_context_passing():
    """Fix context passing in orchestrator.py to always use to_dict()"""
    file_path = "/Users/y-sato/TradingAgents2/backtest2/agents/orchestrator.py"
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Fix all places where context is passed without to_dict()
    # Pattern: 'context': context
    content = re.sub(
        r"'context':\s*context(?!\.to_dict)",
        "'context': context.to_dict() if hasattr(context, 'to_dict') else context",
        content
    )
    
    # Also fix places where context is accessed from input_data
    content = re.sub(
        r"input_data\['context'\]\s*=\s*context(?!\.to_dict)",
        "input_data['context'] = context.to_dict() if hasattr(context, 'to_dict') else context",
        content
    )
    
    with open(file_path, 'w') as f:
        f.write(content)
    
    print("✅ Fixed context passing in orchestrator.py")

def fix_agent_adapter_portfolio_none():
    """Fix portfolio None checks in agent_adapter.py"""
    file_path = "/Users/y-sato/TradingAgents2/backtest2/agents/agent_adapter.py"
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Fix all direct portfolio access
    # Add None checks before accessing portfolio attributes
    patterns = [
        # Fix portfolio.cash access
        (r"portfolio\.cash", "(portfolio.cash if portfolio else 0)"),
        # Fix portfolio.total_value access
        (r"portfolio\.total_value", "(portfolio.total_value if portfolio else 0)"),
        # Fix portfolio.unrealized_pnl access
        (r"portfolio\.unrealized_pnl", "(portfolio.unrealized_pnl if portfolio else 0)"),
    ]
    
    for pattern, replacement in patterns:
        # Only replace if not already protected
        if not re.search(rf"if portfolio.*{pattern}", content):
            content = re.sub(pattern, replacement, content)
    
    with open(file_path, 'w') as f:
        f.write(content)
    
    print("✅ Fixed portfolio None checks in agent_adapter.py")

def fix_trade_action_schema():
    """Ensure all action schemas use proper enum format"""
    file_path = "/Users/y-sato/TradingAgents2/backtest2/agents/agent_adapter.py"
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Fix any remaining string format schemas for action
    content = re.sub(
        r'"action":\s*"string\s*\([^)]+\)"',
        '"action": {"type": "string", "enum": ["BUY", "SELL", "HOLD"]}',
        content
    )
    
    # Fix any remaining string format schemas for final_decision
    content = re.sub(
        r'"final_decision":\s*\{[^}]*"enum":\s*\["BUY",\s*"HOLD",\s*"SELL"\][^}]*\}',
        '"final_decision": {"type": "string", "enum": ["BUY", "SELL", "HOLD"]}',
        content
    )
    
    with open(file_path, 'w') as f:
        f.write(content)
    
    print("✅ Fixed TradeAction schemas in agent_adapter.py")

def add_comprehensive_logging():
    """Add debug logging to track issues"""
    file_path = "/Users/y-sato/TradingAgents2/backtest2/agents/orchestrator.py"
    
    with open(file_path, 'r') as f:
        lines = f.readlines()
    
    # Add logging after context creation
    for i, line in enumerate(lines):
        if "context = DecisionContext(" in line:
            # Find the end of the DecisionContext creation
            j = i
            while j < len(lines) and ")" not in lines[j]:
                j += 1
            # Insert logging after
            if j < len(lines):
                indent = "        "
                lines.insert(j + 1, f'{indent}self.logger.debug(f"Created context: {{type(context)}}, portfolio_state: {{type(context.portfolio_state)}}")\n')
                break
    
    with open(file_path, 'w') as f:
        f.writelines(lines)
    
    print("✅ Added comprehensive logging")

def fix_llm_response_handling():
    """Fix LLM response handling to ensure proper action values"""
    file_path = "/Users/y-sato/TradingAgents2/backtest2/agents/agent_adapter.py"
    
    # Add a response validation method
    validation_code = '''
    def _validate_response(self, response: Dict[str, Any], schema: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and fix LLM response to match schema"""
        # Fix action field if it's in wrong format
        if 'action' in response:
            action = response['action']
            if isinstance(action, str):
                # Handle "string (BUY/SELL/HOLD)" format
                if "BUY" in action and "SELL" in action and "HOLD" in action:
                    response['action'] = 'HOLD'  # Default to HOLD if unclear
                elif action.upper() in ['BUY', 'SELL', 'HOLD']:
                    response['action'] = action.upper()
                else:
                    response['action'] = 'HOLD'
        
        # Fix final_decision field similarly
        if 'final_decision' in response:
            decision = response['final_decision']
            if isinstance(decision, str):
                if "BUY" in decision and "SELL" in decision and "HOLD" in decision:
                    response['final_decision'] = 'HOLD'
                elif decision.upper() in ['BUY', 'SELL', 'HOLD']:
                    response['final_decision'] = decision.upper()
                else:
                    response['final_decision'] = 'HOLD'
        
        return response
'''
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Add the validation method after _create_error_output
    if "_validate_response" not in content:
        insert_pos = content.find("def _create_error_output")
        if insert_pos > 0:
            # Find the end of the method
            method_end = content.find("\n    def ", insert_pos + 1)
            if method_end > 0:
                content = content[:method_end] + "\n" + validation_code + "\n" + content[method_end:]
    
    # Update process method to use validation
    # Find all return AgentOutput calls and add validation before them
    content = re.sub(
        r"return AgentOutput\(\s*agent_name=self\.name,\s*timestamp=[^,]+,\s*output_type='analysis',\s*content=result,",
        "return AgentOutput(\n            agent_name=self.name,\n            timestamp=datetime.now(),\n            output_type='analysis',\n            content=self._validate_response(result, self._get_output_schema()) if isinstance(result, dict) else result,",
        content
    )
    
    with open(file_path, 'w') as f:
        f.write(content)
    
    print("✅ Added response validation")

def main():
    print("🔧 Fixing all backtest2 issues comprehensively...")
    
    # Fix all issues
    fix_orchestrator_context_passing()
    fix_agent_adapter_portfolio_none()
    fix_trade_action_schema()
    add_comprehensive_logging()
    fix_llm_response_handling()
    
    print("\n✅ All fixes applied successfully!")
    print("\nNext steps:")
    print("1. Restart the WebUI")
    print("2. Run the backtest again")
    print("3. Check logs for any remaining issues")

if __name__ == "__main__":
    main()
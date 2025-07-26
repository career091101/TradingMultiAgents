#!/usr/bin/env python3
"""
Add comprehensive debug logging to backtest2 engine
"""

import os

def add_debug_logging():
    # Add debug logging to engine.py
    engine_path = "backtest2/core/engine.py"
    
    # Read current content
    with open(engine_path, 'r') as f:
        content = f.read()
    
    # Find _process_trading_day method
    if "_process_trading_day" in content:
        # Add logging at the start of method
        insert_pos = content.find("async def _process_trading_day")
        if insert_pos > 0:
            # Find the end of the method signature
            method_start = content.find("{", insert_pos)
            if method_start < 0:
                method_start = content.find(":", insert_pos) + 1
                newline_pos = content.find("\n", method_start)
                indent = " " * 8
                
                # Insert debug logging
                debug_code = f'''
        self.logger.info(f"=== Processing trading day {{current_date}} for symbols {{symbols}} ===")
        self.logger.info(f"Portfolio state: Cash=${{self.position_manager.get_portfolio_state().cash:,.2f}}")
        '''
                
                new_content = content[:newline_pos+1] + debug_code + content[newline_pos+1:]
                
                # Write back
                with open(engine_path, 'w') as f:
                    f.write(new_content)
                print(f"Added debug logging to {engine_path}")
    
    # Add debug logging to orchestrator.py
    orchestrator_path = "backtest2/agents/orchestrator.py"
    
    # Read current content
    with open(orchestrator_path, 'r') as f:
        content = f.read()
    
    # Find make_decision method
    if "async def make_decision" in content:
        # Add logging at decision outcome
        insert_pos = content.find("# Return default HOLD decision")
        if insert_pos > 0:
            indent = " " * 8
            debug_code = f'''
        self.logger.warning("All agents failed - returning default HOLD decision")
        self.logger.debug(f"Context symbol: {{context.market_state.get('symbol', 'Unknown')}}")
        self.logger.debug(f"Available cash: ${{context.portfolio_state.cash:,.2f}}")
        '''
            new_content = content[:insert_pos] + debug_code + content[insert_pos:]
            
            # Write back
            with open(orchestrator_path, 'w') as f:
                f.write(new_content)
            print(f"Added debug logging to {orchestrator_path}")

if __name__ == "__main__":
    add_debug_logging()
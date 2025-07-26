#!/usr/bin/env python3
"""
Fix JSON serialization issues for MarketData and AgentOutput
"""

import os

def fix_market_data():
    """Add to_dict method to MarketData"""
    types_path = "backtest2/core/types.py"
    
    with open(types_path, 'r') as f:
        content = f.read()
    
    # Find MarketData class
    market_data_pos = content.find("@dataclass\nclass MarketData:")
    if market_data_pos > 0:
        # Find the end of the class
        next_class_pos = content.find("\n@dataclass", market_data_pos + 1)
        if next_class_pos < 0:
            next_class_pos = content.find("\nclass ", market_data_pos + 1)
        
        # Add to_dict method before the next class
        to_dict_method = '''
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            'date': self.date.isoformat() if hasattr(self.date, 'isoformat') else str(self.date),
            'symbol': self.symbol,
            'open': float(self.open),
            'high': float(self.high),
            'low': float(self.low),
            'close': float(self.close),
            'volume': int(self.volume),
            'adjusted_close': float(self.adjusted_close) if self.adjusted_close else None,
            'news': self.news,
            'fundamentals': self.fundamentals,
            'technicals': self.technicals,
            'sentiment': self.sentiment
        }
'''
        
        # Insert the method
        insert_pos = next_class_pos - 1
        new_content = content[:insert_pos] + to_dict_method + content[insert_pos:]
        
        with open(types_path, 'w') as f:
            f.write(new_content)
        
        print("Added to_dict method to MarketData")

def fix_agent_output():
    """Fix AgentOutput class"""
    types_path = "backtest2/core/types.py"
    
    with open(types_path, 'r') as f:
        content = f.read()
    
    # Find AgentOutput class and add @dataclass decorator
    agent_output_pos = content.find("class AgentOutput:")
    if agent_output_pos > 0:
        # Check if already has @dataclass
        check_pos = content.rfind("\n", 0, agent_output_pos)
        line_before = content[check_pos:agent_output_pos].strip()
        
        if "@dataclass" not in line_before:
            # Add @dataclass decorator
            new_content = content[:check_pos+1] + "@dataclass\n" + content[agent_output_pos:]
            
            # Now add to_dict method
            class_end = new_content.find("\n\n", agent_output_pos)
            to_dict_method = '''
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            'agent_name': self.agent_name,
            'timestamp': self.timestamp.isoformat() if hasattr(self.timestamp, 'isoformat') else str(self.timestamp),
            'output_type': self.output_type,
            'content': self.content,
            'confidence': float(self.confidence),
            'processing_time': float(self.processing_time),
            'rationale': self.rationale,
            'metadata': self.metadata
        }
'''
            
            final_content = new_content[:class_end] + to_dict_method + new_content[class_end:]
            
            with open(types_path, 'w') as f:
                f.write(final_content)
            
            print("Fixed AgentOutput class")

def fix_llm_client():
    """Update LLM client to use to_dict when available"""
    llm_path = "backtest2/agents/llm_client.py"
    
    with open(llm_path, 'r') as f:
        content = f.read()
    
    # Find the context serialization part
    search_str = "context_str = json.dumps(context, ensure_ascii=False"
    pos = content.find(search_str)
    
    if pos > 0:
        # Add conversion logic before JSON dumps
        conversion_code = '''
            # Convert objects to dict if they have to_dict method
            def convert_to_dict(obj):
                if hasattr(obj, 'to_dict'):
                    return obj.to_dict()
                elif isinstance(obj, dict):
                    return {k: convert_to_dict(v) for k, v in obj.items()}
                elif isinstance(obj, list):
                    return [convert_to_dict(item) for item in obj]
                return obj
            
            converted_context = convert_to_dict(context)
            '''
        
        # Find the right place to insert
        line_start = content.rfind("\n", 0, pos)
        indent = len(content[line_start+1:pos]) - len(content[line_start+1:pos].lstrip())
        indented_code = "\n".join(" " * indent + line for line in conversion_code.strip().split("\n"))
        
        # Update the json.dumps line
        old_line = content[pos:content.find("\n", pos)]
        new_line = old_line.replace("context,", "converted_context,")
        
        new_content = content[:line_start+1] + indented_code + "\n" + " " * indent + new_line + content[content.find("\n", pos):]
        
        with open(llm_path, 'w') as f:
            f.write(new_content)
        
        print("Updated LLM client JSON serialization")

if __name__ == "__main__":
    print("Fixing JSON serialization issues...")
    fix_market_data()
    fix_agent_output()
    fix_llm_client()
    print("\nDone! JSON serialization should now work properly.")
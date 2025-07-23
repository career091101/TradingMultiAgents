#!/usr/bin/env python3
"""Fix backtest2 LLM schema definitions"""

import re
import os

def fix_schema_definitions(filepath):
    """Fix incorrect schema definitions in agent adapter"""
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Pattern replacements
    replacements = [
        # String enums
        (r'"price_trend": "string \(bullish/bearish/neutral\)"', 
         '"price_trend": {"type": "string", "enum": ["bullish", "bearish", "neutral"]}'),
        
        (r'"recommendation": "string \(BUY/HOLD/SELL\)"', 
         '"recommendation": {"type": "string", "enum": ["BUY", "HOLD", "SELL"]}'),
        
        (r'"action": "string \(BUY/SELL/HOLD\)"', 
         '"action": {"type": "string", "enum": ["BUY", "SELL", "HOLD"]}'),
        
        (r'"market_impact": "string \(positive/negative/neutral\)"', 
         '"market_impact": {"type": "string", "enum": ["positive", "negative", "neutral"]}'),
        
        (r'"trending_level": "string \(high/medium/low\)"', 
         '"trending_level": {"type": "string", "enum": ["high", "medium", "low"]}'),
        
        (r'"community_sentiment": "string \(positive/negative/neutral\)"', 
         '"community_sentiment": {"type": "string", "enum": ["positive", "negative", "neutral"]}'),
        
        (r'"valuation": "string \(undervalued/fair/overvalued\)"', 
         '"valuation": {"type": "string", "enum": ["undervalued", "fair", "overvalued"]}'),
        
        (r'"financial_health": "string \(strong/moderate/weak\)"', 
         '"financial_health": {"type": "string", "enum": ["strong", "moderate", "weak"]}'),
        
        (r'"growth_prospects": "string \(high/medium/low\)"', 
         '"growth_prospects": {"type": "string", "enum": ["high", "medium", "low"]}'),
        
        (r'"investment_decision": "string \(BUY/HOLD/SELL\)"', 
         '"investment_decision": {"type": "string", "enum": ["BUY", "HOLD", "SELL"]}'),
        
        (r'"risk_level": "string \(low/medium/high\)"', 
         '"risk_level": {"type": "string", "enum": ["low", "medium", "high"]}'),
        
        # Numbers with ranges
        (r'"confidence": "number \(0-1\)"', 
         '"confidence": {"type": "number", "minimum": 0, "maximum": 1}'),
        
        (r'"position_size": "number \(0-1\)"', 
         '"position_size": {"type": "number", "minimum": 0, "maximum": 1}'),
        
        (r'"position_size_pct": "number \(0-1\)"', 
         '"position_size_pct": {"type": "number", "minimum": 0, "maximum": 1}'),
        
        (r'"risk_score": "number \(0-1\)"', 
         '"risk_score": {"type": "number", "minimum": 0, "maximum": 1}'),
        
        (r'"overall_sentiment": "number \(-1 to 1\)"', 
         '"overall_sentiment": {"type": "number", "minimum": -1, "maximum": 1}'),
        
        (r'"sentiment_score": "number \(-1 to 1\)"', 
         '"sentiment_score": {"type": "number", "minimum": -1, "maximum": 1}'),
        
        # Plain types
        (r'"volume_analysis": "string"', 
         '"volume_analysis": {"type": "string"}'),
        
        (r'"technical_analysis": "string"', 
         '"technical_analysis": {"type": "string"}'),
        
        (r'"rationale": "string"', 
         '"rationale": {"type": "string"}'),
        
        (r'"entry_strategy": "string"', 
         '"entry_strategy": {"type": "string"}'),
        
        (r'"stop_loss": "number"', 
         '"stop_loss": {"type": "number"}'),
        
        (r'"take_profit": "number"', 
         '"take_profit": {"type": "number"}'),
        
        (r'"quantity": "number"', 
         '"quantity": {"type": "number"}'),
        
        # Special cases
        (r'"summary_table": "string \(Markdown table\)"', 
         '"summary_table": {"type": "string", "description": "Markdown formatted table"}'),
        
        (r'"final_decision": "string \(FINAL TRANSACTION PROPOSAL: \*\*BUY/HOLD/SELL\*\*\)"', 
         '"final_decision": {"type": "string", "description": "Final transaction proposal", "enum": ["BUY", "HOLD", "SELL"]}'),
        
        # Arrays
        (r'"selected_indicators": \["string"\]', 
         '"selected_indicators": {"type": "array", "items": {"type": "string"}}'),
        
        (r'"key_topics": \["string"\]', 
         '"key_topics": {"type": "array", "items": {"type": "string"}}'),
    ]
    
    # Apply replacements
    for pattern, replacement in replacements:
        content = re.sub(pattern, replacement, content)
    
    # Write back
    with open(filepath, 'w') as f:
        f.write(content)
    
    print(f"Fixed schema definitions in {filepath}")

def main():
    """Main function"""
    filepath = "/Users/y-sato/TradingAgents2/backtest2/agents/agent_adapter.py"
    
    if os.path.exists(filepath):
        fix_schema_definitions(filepath)
        print("Schema definitions fixed successfully!")
    else:
        print(f"File not found: {filepath}")

if __name__ == "__main__":
    main()
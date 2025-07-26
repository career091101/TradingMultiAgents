#!/usr/bin/env python3
"""
Fix mock responses to generate actual trading decisions
"""

import os

def fix_mock_responses():
    print("=== モックレスポンスの修正 ===\n")
    
    llm_path = "backtest2/agents/llm_client.py"
    
    with open(llm_path, 'r') as f:
        content = f.read()
    
    # Find and replace the mock response method
    old_mock_method = '''    def _generate_mock_response(self, prompt: str, context: Dict[str, Any], agent_name: Optional[str] = None) -> str:
        """Generate mock response for testing"""
        if agent_name:
            if "market" in agent_name.lower():
                return '{"analysis": "Technical indicators suggest neutral market conditions.", "confidence": 0.7, "action": "HOLD"}'
            elif "news" in agent_name.lower():
                return '{"sentiment": "slightly positive", "score": 0.6, "action": "HOLD"}'
            elif "bull" in agent_name.lower():
                return '{"recommendation": "BUY", "confidence": 0.8, "rationale": "Strong growth potential"}'
            elif "bear" in agent_name.lower():
                return '{"recommendation": "SELL", "confidence": 0.6, "rationale": "Risk factors present"}'
            elif "trader" in agent_name.lower():
                return '{"action": "BUY", "confidence": 0.7, "quantity": 100}'
            elif "risk" in agent_name.lower():
                return '{"approval": true, "risk_score": 0.3, "position_size": 0.1}'
        
        # Default response
        return '{"action": "HOLD", "confidence": 0.5, "rationale": "Mock analysis complete"}'
'''
    
    new_mock_method = '''    def _generate_mock_response(self, prompt: str, context: Dict[str, Any], agent_name: Optional[str] = None) -> str:
        """Generate mock response for testing - with realistic trading decisions"""
        import random
        
        # Add some randomness to make it more realistic
        random_factor = random.random()
        
        if agent_name:
            if "market" in agent_name.lower() or "market_analyst" in agent_name:
                # Market analyst - technical analysis
                if random_factor > 0.7:
                    return '{"analysis": "Strong bullish momentum detected. RSI shows oversold conditions.", "confidence": 0.8, "action": "BUY", "indicators": {"RSI": 28, "MACD": "bullish_crossover", "SMA20": "above"}}'
                elif random_factor > 0.3:
                    return '{"analysis": "Market showing consolidation patterns.", "confidence": 0.6, "action": "HOLD", "indicators": {"RSI": 50, "MACD": "neutral", "SMA20": "at"}}'
                else:
                    return '{"analysis": "Bearish divergence detected. Volume declining.", "confidence": 0.7, "action": "SELL", "indicators": {"RSI": 72, "MACD": "bearish_crossover", "SMA20": "below"}}'
                    
            elif "news" in agent_name.lower():
                if random_factor > 0.6:
                    return '{"sentiment": "positive", "score": 0.8, "action": "BUY", "headlines": ["Company reports record earnings", "Analyst upgrades target"]}'
                else:
                    return '{"sentiment": "neutral", "score": 0.5, "action": "HOLD", "headlines": ["Mixed market signals"]}'
                    
            elif "bull" in agent_name.lower():
                # Bull researcher - always optimistic
                return '{"recommendation": "BUY", "confidence": 0.85, "rationale": "Strong growth potential. Fundamentals improving. Market position strengthening.", "target_price": 200}'
                
            elif "bear" in agent_name.lower():
                # Bear researcher - always cautious
                return '{"recommendation": "SELL", "confidence": 0.75, "rationale": "Overvaluation concerns. Competition increasing. Macro headwinds.", "downside_risk": 20}'
                
            elif "research_manager" in agent_name:
                # Research manager - balances bull/bear views
                if random_factor > 0.5:
                    return '{"decision": "BUY", "confidence": 0.7, "rationale": "Bull case outweighs risks", "action": "BUY"}'
                else:
                    return '{"decision": "HOLD", "confidence": 0.6, "rationale": "Mixed signals, await clarity", "action": "HOLD"}'
                    
            elif "trader" in agent_name.lower():
                # Trader - executes based on research
                if random_factor > 0.4:
                    return '{"action": "BUY", "confidence": 0.75, "quantity": 100, "entry_strategy": "market_order", "position_size": 0.1}'
                else:
                    return '{"action": "HOLD", "confidence": 0.5, "quantity": 0, "rationale": "Waiting for better entry"}'
                    
            elif "aggressive" in agent_name.lower():
                return '{"stance": "AGGRESSIVE", "risk_tolerance": "high", "position_size": 0.15, "recommendation": "increase_position"}'
                
            elif "conservative" in agent_name.lower():
                return '{"stance": "CONSERVATIVE", "risk_tolerance": "low", "position_size": 0.05, "recommendation": "reduce_position"}'
                
            elif "risk_manager" in agent_name:
                # Risk manager - final decision
                if random_factor > 0.4:
                    return '{"action": "BUY", "confidence": 0.7, "quantity": 50, "risk_assessment": {"approved": true, "risk_score": 0.3}, "position_size_pct": 0.1, "stop_loss": 0.95, "take_profit": 1.1}'
                else:
                    return '{"action": "HOLD", "confidence": 0.5, "quantity": 0, "risk_assessment": {"approved": false, "risk_score": 0.7}, "rationale": "Risk/reward unfavorable"}'
        
        # Default response with some variation
        if random_factor > 0.6:
            return '{"action": "BUY", "confidence": 0.6, "rationale": "Mock analysis suggests opportunity"}'
        elif random_factor > 0.3:
            return '{"action": "HOLD", "confidence": 0.5, "rationale": "Mock analysis suggests patience"}'
        else:
            return '{"action": "SELL", "confidence": 0.6, "rationale": "Mock analysis suggests caution"}'
'''
    
    # Replace the method
    if old_mock_method in content:
        content = content.replace(old_mock_method, new_mock_method)
        print("✓ 既存のモックメソッドを置き換えました")
    else:
        # Find the method differently
        start_pos = content.find("def _generate_mock_response")
        if start_pos > 0:
            # Find the end of the method (next def at same indentation)
            end_pos = content.find("\n    def ", start_pos + 1)
            if end_pos < 0:
                end_pos = content.find("\n\nclass", start_pos)
            if end_pos < 0:
                end_pos = len(content)
            
            # Replace the method
            indent_start = content.rfind("\n", 0, start_pos) + 1
            content = content[:indent_start] + new_mock_method + content[end_pos:]
            print("✓ モックメソッドを修正しました")
        else:
            print("✗ モックメソッドが見つかりません")
            return
    
    # Write back
    with open(llm_path, 'w') as f:
        f.write(content)
    
    print("\n修正内容:")
    print("- ランダム性を追加して現実的な取引決定を生成")
    print("- 各エージェントに適切な応答パターンを実装")
    print("- BUY/SELL/HOLDが適切な割合で発生")
    print("- リスク評価とポジションサイズを含む")
    
    print("\n次のステップ:")
    print("1. テストを再実行")
    print("2. WebUIでモックモードまたはo3/o4モードで確認")

if __name__ == "__main__":
    fix_mock_responses()
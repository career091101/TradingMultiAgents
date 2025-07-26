#!/usr/bin/env python3
"""
Fix LLM response parsing issues for real LLM mode
"""

import os
import re

def fix_llm_response_parsing():
    print("=== 実LLMモードの応答パース問題を修正 ===\n")
    
    # 1. Fix llm_client.py to better handle response parsing
    llm_client_path = "backtest2/agents/llm_client.py"
    
    with open(llm_client_path, 'r') as f:
        content = f.read()
    
    # Find and update the generate_structured method
    old_parse_section = """            # Parse JSON response
            # Extract JSON from response
            import re
            json_match = re.search(r'\\{.*\\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                self.logger.error(f"No JSON found in response: {response[:200]}")
                return self._create_default_response(output_schema)"""
    
    new_parse_section = """            # Parse JSON response with better error handling
            # Try to extract JSON from response
            import re
            
            # Log the full response for debugging
            self.logger.debug(f"Full LLM response: {response[:1000]}...")
            
            # Try multiple JSON extraction patterns
            json_patterns = [
                r'```json\s*(\{.*?\})\s*```',  # JSON in code blocks
                r'(\{.*\})',                    # Raw JSON
                r'(?:^|\n)(\{[^}]+\})',        # JSON starting at line
            ]
            
            json_text = None
            for pattern in json_patterns:
                match = re.search(pattern, response, re.DOTALL | re.IGNORECASE)
                if match:
                    json_text = match.group(1)
                    break
            
            if json_text:
                try:
                    # Clean up common issues
                    json_text = json_text.strip()
                    # Fix common LLM mistakes
                    json_text = json_text.replace('"action": "string (BUY/SELL/HOLD)"', '"action": "HOLD"')
                    json_text = json_text.replace('"string"', '""')
                    json_text = re.sub(r'"(BUY|SELL|HOLD)\\s*\\(.*?\\)"', r'"\\1"', json_text)
                    
                    result = json.loads(json_text)
                    self.logger.debug(f"Successfully parsed JSON: {result}")
                    return result
                except json.JSONDecodeError as e:
                    self.logger.error(f"Failed to parse extracted JSON: {e}")
                    self.logger.error(f"JSON text was: {json_text[:500]}")
            else:
                self.logger.error(f"No JSON found in response: {response[:500]}")
            
            # If we can't parse, create a structured response from text
            return self._parse_text_response(response, output_schema)"""
    
    content = content.replace(old_parse_section, new_parse_section)
    
    # Add the new _parse_text_response method
    parse_text_method = '''
    def _parse_text_response(self, response: str, schema: Dict[str, Any]) -> Dict[str, Any]:
        """Try to parse a text response into the expected schema"""
        result = self._create_default_response(schema)
        
        # Look for common patterns in text
        response_lower = response.lower()
        
        # Extract action
        if "買い" in response or "buy" in response_lower:
            result["action"] = "BUY"
            result["recommendation"] = "BUY"
            result["investment_decision"] = "BUY"
            result["final_decision"] = "BUY"
        elif "売り" in response or "sell" in response_lower:
            result["action"] = "SELL"
            result["recommendation"] = "SELL"
            result["investment_decision"] = "SELL"
            result["final_decision"] = "SELL"
        else:
            result["action"] = "HOLD"
            result["recommendation"] = "HOLD"
            result["investment_decision"] = "HOLD"
            result["final_decision"] = "HOLD"
        
        # Extract confidence
        confidence_patterns = [
            r'confidence[:\s]+([0-9.]+)',
            r'確信度[:\s]+([0-9.]+)',
            r'([0-9.]+)%?\s*(?:confidence|確信)',
        ]
        for pattern in confidence_patterns:
            match = re.search(pattern, response_lower)
            if match:
                try:
                    conf = float(match.group(1))
                    if conf > 1:  # Percentage
                        conf = conf / 100
                    result["confidence"] = min(1.0, max(0.0, conf))
                    result["confidence_level"] = result["confidence"]
                    break
                except:
                    pass
        
        # Set rationale to the full response if not found
        if "rationale" in schema:
            result["rationale"] = response[:500]  # First 500 chars
        
        self.logger.warning(f"Parsed text response to: {result}")
        return result'''
    
    # Insert the method before the _create_default_response method
    insert_pos = content.find("    def _create_default_response")
    content = content[:insert_pos] + parse_text_method + "\n" + content[insert_pos:]
    
    with open(llm_client_path, 'w') as f:
        f.write(content)
    
    print("✓ llm_client.pyの応答パース処理を改善しました")
    
    # 2. Update agent_adapter.py to add validation to all adapters
    adapter_path = "backtest2/agents/agent_adapter.py"
    
    with open(adapter_path, 'r') as f:
        content = f.read()
    
    # Add a base validation method
    base_validation = '''
    def _validate_response(self, response: Dict[str, Any], schema: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and fix LLM response to match schema"""
        # Fix common action field issues
        action_fields = ['action', 'final_decision', 'investment_decision', 'recommendation']
        for field in action_fields:
            if field in response:
                value = response[field]
                if isinstance(value, str):
                    # Clean up the value
                    value = value.upper().strip()
                    # Handle "BUY/SELL/HOLD" format
                    if "/" in value:
                        # Default to HOLD if multiple options
                        value = 'HOLD'
                    # Extract valid action
                    for action in ['BUY', 'SELL', 'HOLD']:
                        if action in value:
                            response[field] = action
                            break
                    else:
                        # Default to HOLD if unclear
                        response[field] = 'HOLD'
        
        # Ensure confidence is a float between 0 and 1
        confidence_fields = ['confidence', 'confidence_level']
        for field in confidence_fields:
            if field in response:
                try:
                    conf = float(response[field])
                    response[field] = min(1.0, max(0.0, conf))
                except:
                    response[field] = 0.5
        
        # Ensure required string fields have values
        string_fields = ['rationale', 'analysis', 'valuation', 'sentiment']
        for field in string_fields:
            if field in schema and field not in response:
                response[field] = ""
        
        return response'''
    
    # Insert after the _prepare_context method in TradingAgentAdapter
    insert_pos = content.find("        return context\n", content.find("def _prepare_context")) + len("        return context\n")
    content = content[:insert_pos] + base_validation + "\n" + content[insert_pos:]
    
    # Update the process method to use validation
    old_process_return = """            return self._create_output(
                content=content,
                confidence=confidence,
                processing_time=processing_time,
                rationale=rationale
            )"""
    
    new_process_return = """            # Validate response before creating output
            validated_response = self._validate_response(response, self._get_output_schema())
            
            return self._create_output(
                content=self._process_response(validated_response),
                confidence=self._calculate_confidence(validated_response),
                processing_time=processing_time,
                rationale=validated_response.get('rationale', '')
            )"""
    
    content = content.replace(old_process_return, new_process_return)
    
    # Remove the duplicate validation from MarketAnalystAdapter
    # Find and remove the old validation method
    start_marker = "\n\n    def _validate_response(self, response: Dict[str, Any], schema: Dict[str, Any]) -> Dict[str, Any]:"
    end_marker = "        return response"
    
    start_pos = content.find(start_marker, content.find("class MarketAnalystAdapter"))
    if start_pos > 0:
        end_pos = content.find(end_marker, start_pos) + len(end_marker)
        # Remove the duplicate method
        content = content[:start_pos] + content[end_pos:]
    
    with open(adapter_path, 'w') as f:
        f.write(content)
    
    print("✓ agent_adapter.pyに応答検証機能を追加しました")
    
    # 3. Add debug logging configuration
    debug_config = '''#!/usr/bin/env python3
"""
Enable debug logging for LLM responses
"""

import logging
import os

def setup_debug_logging():
    """Setup debug logging for LLM response troubleshooting"""
    
    # Create logs directory if it doesn't exist
    os.makedirs("logs", exist_ok=True)
    
    # Configure root logger
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/llm_debug.log'),
            logging.StreamHandler()
        ]
    )
    
    # Set specific loggers to debug
    loggers_to_debug = [
        'backtest2.agents.llm_client',
        'backtest2.agents.agent_adapter',
        'backtest2.agents.orchestrator'
    ]
    
    for logger_name in loggers_to_debug:
        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.DEBUG)
    
    print("Debug logging enabled. Check logs/llm_debug.log for details.")

if __name__ == "__main__":
    setup_debug_logging()
'''
    
    with open("enable_llm_debug.py", 'w') as f:
        f.write(debug_config)
    
    print("✓ デバッグログ設定スクリプトを作成しました")
    
    print("\n=== 修正内容 ===")
    print("1. JSON抽出パターンを複数追加（コードブロック、生のJSON等）")
    print("2. LLMの一般的なミスを自動修正")
    print("3. JSONパースに失敗した場合のテキスト解析フォールバック")
    print("4. すべてのアダプターに応答検証機能を追加")
    print("5. デバッグログの強化")
    
    print("\n=== 次のステップ ===")
    print("1. python enable_llm_debug.py を実行してデバッグログを有効化")
    print("2. WebUIを再起動して実LLMモードでテスト")
    print("3. logs/llm_debug.log でLLM応答の詳細を確認")
    print("4. 必要に応じてさらなる調整を実施")

if __name__ == "__main__":
    fix_llm_response_parsing()
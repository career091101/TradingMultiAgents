#!/usr/bin/env python3
"""
Complete fix for JSON serialization issues including generate_structured
"""

import os

def fix_complete():
    print("=== 完全なJSONシリアライズ修正 ===\n")
    
    # 1. Fix generate_structured method in llm_client.py
    llm_path = "backtest2/agents/llm_client.py"
    
    with open(llm_path, 'r') as f:
        content = f.read()
    
    # Find generate_structured method
    if "async def generate_structured" in content:
        print("1. generate_structuredメソッドを修正中...")
        
        # Add conversion before structured prompt creation
        structured_fix = '''async def generate_structured(
        self,
        prompt: str,
        context: Dict[str, Any],
        output_schema: Dict[str, Any],
        use_deep_thinking: bool = False,
        system_message: Optional[str] = None,
        agent_name: Optional[str] = None,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """Generate structured response from LLM with retry logic"""
        
        # Convert context to JSON-serializable format
        def convert_to_dict(obj):
            if hasattr(obj, 'to_dict'):
                return obj.to_dict()
            elif hasattr(obj, '__dataclass_fields__'):
                # Handle dataclasses
                return {field: convert_to_dict(getattr(obj, field)) 
                       for field in obj.__dataclass_fields__}
            elif isinstance(obj, dict):
                return {k: convert_to_dict(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_to_dict(item) for item in obj]
            elif hasattr(obj, 'isoformat'):  # datetime
                return obj.isoformat()
            return obj
        
        # Convert context before using it
        serializable_context = convert_to_dict(context)
        
        # Add output schema to prompt
        schema_str = json.dumps(output_schema, ensure_ascii=False, indent=2)
        structured_prompt = f"{prompt}\\n\\nPlease respond in the following JSON format:\\n{schema_str}"
        
        try:
            # Use serializable_context instead of raw context
            response = await self.generate(
                structured_prompt,
                serializable_context,  # Use converted context
                use_deep_thinking,
                system_message,
                agent_name,
                use_cache
            )'''
        
        # Replace the method
        start_pos = content.find("async def generate_structured")
        end_pos = content.find("try:", start_pos)
        
        if start_pos > 0 and end_pos > 0:
            # Find the exact position after the try:
            new_content = content[:start_pos] + structured_fix + content[end_pos:]
            
            with open(llm_path, 'w') as f:
                f.write(new_content)
            
            print("   ✓ generate_structuredメソッドを修正しました")
    
    # 2. Add debug logging
    print("\n2. デバッグログを追加中...")
    
    debug_logging = '''
        # Debug logging for JSON serialization issues
        if self.logger.isEnabledFor(logging.DEBUG):
            self.logger.debug(f"[{agent_name}] Original context type: {type(context)}")
            self.logger.debug(f"[{agent_name}] Context keys: {list(context.keys()) if isinstance(context, dict) else 'Not a dict'}")
            
            # Log problematic objects
            if isinstance(context, dict):
                for key, value in context.items():
                    if hasattr(value, '__class__'):
                        self.logger.debug(f"[{agent_name}] {key}: {value.__class__.__name__}")
        '''
    
    # Add after context conversion
    insert_pos = content.find("serializable_context = convert_to_dict(context)")
    if insert_pos > 0:
        line_end = content.find("\n", insert_pos)
        new_content = content[:line_end+1] + debug_logging + content[line_end+1:]
        
        with open(llm_path, 'w') as f:
            f.write(new_content)
        
        print("   ✓ デバッグログを追加しました")
    
    # 3. Fix all methods that might use non-serializable objects
    print("\n3. エラーハンドリングを改善中...")
    
    # Improve error handling in generate_structured
    error_handling = '''
            # Parse JSON response
            # Extract JSON from response
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                self.logger.error(f"No JSON found in response: {response[:200]}")
                return self._create_default_response(output_schema)
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse JSON response: {e}")
            self.logger.error(f"Response was: {response[:500]}")
            return self._create_default_response(output_schema)
        except Exception as e:
            self.logger.error(f"Failed to generate structured response: {e}")
            self.logger.debug(f"Context type that caused error: {type(context)}")
            if isinstance(context, dict):
                for k, v in context.items():
                    if not isinstance(v, (str, int, float, bool, type(None), list, dict)):
                        self.logger.debug(f"Problematic field '{k}': {type(v)}")
            return self._create_default_response(output_schema)'''
    
    # Update error handling section
    with open(llm_path, 'r') as f:
        content = f.read()
    
    # Find the error handling section in generate_structured
    parse_pos = content.find("# Parse JSON response")
    if parse_pos > 0:
        # Find the end of the method
        except_end = content.find("return self._create_default_response(output_schema)", parse_pos)
        if except_end > 0:
            method_end = content.find("\n    def ", except_end)
            if method_end < 0:
                method_end = len(content)
            
            new_content = content[:parse_pos] + error_handling + content[method_end:]
            
            with open(llm_path, 'w') as f:
                f.write(new_content)
            
            print("   ✓ エラーハンドリングを改善しました")
    
    print("\n4. 完了！")
    print("\n修正内容:")
    print("- generate_structuredでコンテキストを変換")
    print("- デバッグログで問題のあるオブジェクトを特定")
    print("- エラー時の詳細情報を記録")
    
    print("\n次のステップ:")
    print("1. WebUIを再起動: ps aux | grep streamlit で PID を確認して kill")
    print("2. デバッグログを有効化: logging.basicConfig(level=logging.DEBUG)")
    print("3. テストを実行して詳細ログを確認")

if __name__ == "__main__":
    fix_complete()
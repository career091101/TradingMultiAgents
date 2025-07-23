#!/usr/bin/env python3
"""
Immediate fix for backtest2 to get it working
"""

import os

def add_mock_mode_option():
    """Add mock mode option to WebUI"""
    file_path = "/Users/y-sato/TradingAgents2/TradingMultiAgents/webui/components/backtest2.py"
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Find the LLM provider section
    if "深層思考モデル" in content and "use_mock_agents" not in content:
        # Add mock mode checkbox after LLM settings
        insert_pos = content.find("st.caption(\"※ モデルを変更するには")
        if insert_pos > 0:
            indent = "            "
            new_code = f'\n{indent}# Mock mode for testing\n'
            new_code += f'{indent}use_mock = st.checkbox(\n'
            new_code += f'{indent}    "モックモードを使用 (テスト用)",\n'
            new_code += f'{indent}    value=self.state.get("bt2_use_mock", False),\n'
            new_code += f'{indent}    help="実際のLLMを使用せずに高速テストを実行"\n'
            new_code += f'{indent})\n'
            new_code += f'{indent}self.state.set("bt2_use_mock", use_mock)\n'
            new_code += f'{indent}if use_mock:\n'
            new_code += f'{indent}    st.info("⚠️ モックモードが有効です。実際のLLMは使用されません。")\n'
            
            content = content[:insert_pos] + new_code + "\n" + " "*12 + content[insert_pos:]
    
    with open(file_path, 'w') as f:
        f.write(content)
    
    print("✅ Added mock mode option to WebUI")

def update_wrapper_for_mock():
    """Update wrapper to use mock mode when selected"""
    file_path = "/Users/y-sato/TradingAgents2/TradingMultiAgents/webui/backend/backtest2_wrapper.py"
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Find LLM config creation
    if "deep_think_model=deep_model" in content:
        # Update to check for mock mode
        content = content.replace(
            "deep_think_model=deep_model or self._get_deep_model(llm_provider)",
            'deep_think_model="mock" if webui_config.get("use_mock", False) else (deep_model or self._get_deep_model(llm_provider))'
        )
        content = content.replace(
            "quick_think_model=fast_model or self._get_quick_model(llm_provider)",
            'quick_think_model="mock" if webui_config.get("use_mock", False) else (fast_model or self._get_quick_model(llm_provider))'
        )
    
    with open(file_path, 'w') as f:
        f.write(content)
    
    print("✅ Updated wrapper to support mock mode")

def main():
    print("🔧 Applying immediate fixes for backtest2...")
    
    add_mock_mode_option()
    update_wrapper_for_mock()
    
    print("\n✅ Fixes applied!")
    print("\nNext steps:")
    print("1. Restart the WebUI")
    print("2. Enable 'モックモードを使用' checkbox")
    print("3. Run backtest - it should complete with actual trades")

if __name__ == "__main__":
    main()
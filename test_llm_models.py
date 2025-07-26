#!/usr/bin/env python3
"""
Test LLM model availability and configuration
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import OpenAI to test
try:
    import openai
    print("✓ OpenAI library imported successfully")
except ImportError as e:
    print(f"✗ Failed to import OpenAI: {e}")
    sys.exit(1)

# Check API key
api_key = os.getenv("OPENAI_API_KEY")
if api_key:
    print(f"✓ OpenAI API key found (length: {len(api_key)})")
else:
    print("✗ OpenAI API key not found in environment")
    sys.exit(1)

# Test available models
print("\nTesting OpenAI models...")
test_models = ["gpt-4o", "gpt-4o-mini", "gpt-3.5-turbo", "gpt-4-turbo"]

client = openai.OpenAI(api_key=api_key)

for model in test_models:
    try:
        # Try a simple completion
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": "Say 'test' only"}],
            max_tokens=10,
            temperature=0
        )
        print(f"✓ Model {model}: Available")
    except Exception as e:
        print(f"✗ Model {model}: {str(e)}")

print("\nChecking backtest2 config...")
try:
    from backtest2.core.config import LLMConfig
    config = LLMConfig()
    print(f"✓ Default deep_think_model: {config.deep_think_model}")
    print(f"✓ Default quick_think_model: {config.quick_think_model}")
except Exception as e:
    print(f"✗ Failed to import backtest2 config: {e}")

print("\nChecking WebUI model list...")
try:
    from TradingMultiAgents.webui.utils.state import UIHelpers
    openai_models = UIHelpers.get_provider_models("openai")
    print(f"✓ OpenAI models in UI: {openai_models}")
except Exception as e:
    print(f"✗ Failed to get UI models: {e}")

print("\nConfiguration test complete!")
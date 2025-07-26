#!/usr/bin/env python
"""Test OpenAI API connection and fix environment issues"""

import os
import sys
import asyncio
from pathlib import Path

# Load environment variables from .bashrc
bashrc_path = Path.home() / ".bashrc"
if bashrc_path.exists():
    with open(bashrc_path, 'r') as f:
        for line in f:
            if 'export OPENAI_API_KEY=' in line:
                key = line.strip().split('=', 1)[1].strip('"')
                os.environ['OPENAI_API_KEY'] = key
                print(f"✅ Loaded OPENAI_API_KEY from .bashrc")
                break

# Check if API key is set
api_key = os.environ.get('OPENAI_API_KEY')
if not api_key:
    print("❌ OPENAI_API_KEY not found in environment!")
    print("\nTo fix this, run:")
    print("source ~/.bashrc")
    print("Then try again.")
    sys.exit(1)

print(f"✅ API Key found (length: {len(api_key)} chars)")
print(f"   First 20 chars: {api_key[:20]}...")

# Test actual OpenAI connection
try:
    from openai import OpenAI
    
    print("\n🧪 Testing OpenAI API connection...")
    
    client = OpenAI(api_key=api_key)
    
    # Simple test
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Say 'API connection successful!' in exactly 3 words."}
        ],
        max_tokens=10
    )
    
    result = response.choices[0].message.content
    print(f"✅ API Response: {result}")
    print("\n🎉 OpenAI API connection is working!")
    
    # Test o3 model availability
    print("\n🧪 Testing o3 model...")
    try:
        response = client.chat.completions.create(
            model="o3",
            messages=[
                {"role": "user", "content": "Test"}
            ],
            max_tokens=10
        )
        print("✅ o3 model is available")
    except Exception as e:
        print(f"⚠️  o3 model error: {str(e)}")
        print("   This might be normal if you don't have access to o3")
    
    # Test o4-mini model
    print("\n🧪 Testing gpt-4o-mini model...")
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "user", "content": "Test"}
            ],
            max_tokens=10
        )
        print("✅ gpt-4o-mini model is available")
    except Exception as e:
        print(f"⚠️  gpt-4o-mini model error: {str(e)}")
    
except ImportError:
    print("❌ OpenAI library not installed!")
    print("Run: pip install openai")
    sys.exit(1)
except Exception as e:
    print(f"❌ API Connection failed: {str(e)}")
    print("\nPossible issues:")
    print("1. Invalid API key")
    print("2. Network connection issues")
    print("3. API rate limits or billing issues")
    sys.exit(1)

# Reset Circuit Breaker
print("\n🔄 Resetting Circuit Breaker state...")
# Circuit breaker is in-memory, so restarting the process will reset it
print("✅ Circuit Breaker will be reset when you run the next backtest")

print("\n📋 Next steps:")
print("1. Run the backtest again with the API key properly set")
print("2. If using WebUI, restart it to pick up the environment variable")
print("3. Consider using gpt-4o-mini instead of o3 if o3 is not available")

# Create a script to properly set environment and run backtest
script_content = '''#!/bin/bash
# Load environment variables
source ~/.bashrc

# Verify API key is set
if [ -z "$OPENAI_API_KEY" ]; then
    echo "Error: OPENAI_API_KEY not set!"
    exit 1
fi

echo "✅ OPENAI_API_KEY is set"
echo "🚀 Starting backtest with proper environment..."

# Run the backtest
python test_debug_backtest.py
'''

with open('run_backtest_with_env.sh', 'w') as f:
    f.write(script_content)

os.chmod('run_backtest_with_env.sh', 0o755)
print("\n✅ Created run_backtest_with_env.sh")
print("   Run: ./run_backtest_with_env.sh")
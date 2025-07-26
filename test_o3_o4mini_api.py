#!/usr/bin/env python3
"""
Comprehensive API connection test for o3 and o4-mini models
Tests various parameter combinations and access methods
"""

import os
import json
from openai import OpenAI
from datetime import datetime

# Initialize the client
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    print("❌ Error: OPENAI_API_KEY not set")
    exit(1)

client = OpenAI(api_key=api_key)

# Test configurations for o3/o4-mini models
test_configs = [
    # Basic tests with different model name formats
    {
        "name": "o3 - Basic",
        "model": "o3",
        "params": {
            "messages": [{"role": "user", "content": "Say 'test successful'"}],
            "max_tokens": 10
        }
    },
    {
        "name": "o4-mini - Basic",
        "model": "o4-mini",
        "params": {
            "messages": [{"role": "user", "content": "Say 'test successful'"}],
            "max_tokens": 10
        }
    },
    {
        "name": "o3-2025-04-16 - Date format",
        "model": "o3-2025-04-16",
        "params": {
            "messages": [{"role": "user", "content": "Say 'test successful'"}],
            "max_tokens": 10
        }
    },
    {
        "name": "o4-mini-2025-04-16 - Date format",
        "model": "o4-mini-2025-04-16",
        "params": {
            "messages": [{"role": "user", "content": "Say 'test successful'"}],
            "max_tokens": 10
        }
    },
    # Test with max_completion_tokens (new parameter for o-series)
    {
        "name": "o3 - With max_completion_tokens",
        "model": "o3",
        "params": {
            "messages": [{"role": "user", "content": "What is 2+2?"}],
            "max_completion_tokens": 100
        }
    },
    {
        "name": "o4-mini - With max_completion_tokens",
        "model": "o4-mini",
        "params": {
            "messages": [{"role": "user", "content": "What is 2+2?"}],
            "max_completion_tokens": 100
        }
    },
    # Test with reasoning_effort parameter
    {
        "name": "o3 - With reasoning_effort low",
        "model": "o3",
        "params": {
            "messages": [{"role": "user", "content": "What is 2+2?"}],
            "max_tokens": 100,
            "reasoning_effort": "low"
        }
    },
    {
        "name": "o4-mini - With reasoning_effort medium",
        "model": "o4-mini",
        "params": {
            "messages": [{"role": "user", "content": "What is 2+2?"}],
            "max_tokens": 100,
            "reasoning_effort": "medium"
        }
    },
    # Test with developer message instead of system message
    {
        "name": "o3 - With developer message",
        "model": "o3",
        "params": {
            "messages": [
                {"role": "developer", "content": "You are a helpful assistant"},
                {"role": "user", "content": "Hello"}
            ],
            "max_tokens": 50
        }
    },
    # Test o3-mini (which should be more accessible)
    {
        "name": "o3-mini - Basic test",
        "model": "o3-mini",
        "params": {
            "messages": [{"role": "user", "content": "Say 'test successful'"}],
            "max_tokens": 10
        }
    },
    {
        "name": "o3-mini-2025-01-31 - Date format",
        "model": "o3-mini-2025-01-31",
        "params": {
            "messages": [{"role": "user", "content": "Say 'test successful'"}],
            "max_tokens": 10
        }
    },
    # Test with minimal parameters
    {
        "name": "o3 - Minimal params",
        "model": "o3",
        "params": {
            "messages": [{"role": "user", "content": "Hi"}]
        }
    },
    # Test o1 series for comparison
    {
        "name": "o1-mini - Comparison test",
        "model": "o1-mini",
        "params": {
            "messages": [{"role": "user", "content": "Say 'test successful'"}],
            "max_completion_tokens": 100
        }
    }
]

print(f"🔬 OpenAI o3/o4-mini API Connection Test")
print(f"📅 Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"🔑 API Key: {'Set' if api_key else 'Not Set'} (length: {len(api_key) if api_key else 0})")
print("=" * 80)

# Track results
successful_tests = []
failed_tests = []

# Run tests
for config in test_configs:
    print(f"\n🧪 Testing: {config['name']}")
    print(f"   Model: {config['model']}")
    
    try:
        # Make API call
        response = client.chat.completions.create(
            model=config['model'],
            **config['params']
        )
        
        # Success!
        print(f"   ✅ SUCCESS!")
        print(f"   Response: {response.choices[0].message.content}")
        print(f"   Usage: {response.usage}")
        
        successful_tests.append({
            "test": config['name'],
            "model": config['model'],
            "response": response.choices[0].message.content
        })
        
    except Exception as e:
        error_str = str(e)
        print(f"   ❌ FAILED: {error_str}")
        
        # Analyze error type
        if "does not exist" in error_str:
            print(f"   → Model not found")
        elif "Unsupported" in error_str:
            print(f"   → Model exists but parameters unsupported")
            # Extract unsupported parameter if possible
            if "parameter" in error_str:
                print(f"   → Error details: {error_str[:200]}")
        elif "tier" in error_str.lower() or "access" in error_str.lower():
            print(f"   → Access denied (likely tier restriction)")
        elif "rate" in error_str.lower():
            print(f"   → Rate limit exceeded")
        else:
            print(f"   → Unknown error type")
        
        failed_tests.append({
            "test": config['name'],
            "model": config['model'],
            "error": error_str
        })

# Summary
print("\n" + "=" * 80)
print("📊 TEST SUMMARY")
print("=" * 80)

print(f"\n✅ Successful Tests: {len(successful_tests)}")
for test in successful_tests:
    print(f"   - {test['test']} ({test['model']})")

print(f"\n❌ Failed Tests: {len(failed_tests)}")
for test in failed_tests:
    print(f"   - {test['test']} ({test['model']})")
    print(f"     Error: {test['error'][:100]}...")

# Check API tier
print("\n🔍 CHECKING API TIER...")
print("Visit: https://platform.openai.com/account/limits")
print("Look for 'Usage tier' at the bottom of the page under 'Organization'")

# Recommendations
print("\n💡 RECOMMENDATIONS:")
if len(successful_tests) == 0:
    print("   ⚠️ No models were accessible. This suggests:")
    print("   1. Your API tier is below Tier 3 (required for o3/o4-mini)")
    print("   2. These models may require special access or enrollment")
    print("   3. Try using gpt-4o or gpt-4o-mini instead")
else:
    print("   ✅ Some models are accessible!")
    for test in successful_tests:
        print(f"   - Use '{test['model']}' in your configuration")

# Save detailed results
results_file = f"o3_o4mini_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
with open(results_file, 'w') as f:
    json.dump({
        "test_date": datetime.now().isoformat(),
        "successful_tests": successful_tests,
        "failed_tests": failed_tests,
        "total_tests": len(test_configs)
    }, f, indent=2)

print(f"\n📄 Detailed results saved to: {results_file}")
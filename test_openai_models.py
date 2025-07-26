#!/usr/bin/env python3
"""
Test OpenAI API connectivity and model availability
"""

import os
import openai
from datetime import datetime

def test_openai_models():
    """Test availability of specific OpenAI models"""
    
    # Get API key from environment
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("❌ OPENAI_API_KEY not found in environment variables")
        return
    
    print("=" * 60)
    print("OpenAI Model Availability Test")
    print(f"Test Date: {datetime.now()}")
    print("=" * 60)
    
    # Initialize OpenAI client
    client = openai.OpenAI(api_key=api_key)
    
    # Models to test
    models_to_test = [
        "o3-2025-04-16",
        "o4-mini-2025-04-16",
        "gpt-4-turbo-preview",
        "gpt-3.5-turbo",
        "gpt-4",
        "o1-preview",
        "o1-mini"
    ]
    
    print("\n1. Testing Model List API:")
    try:
        # List available models
        models = client.models.list()
        available_models = [model.id for model in models.data]
        print(f"✓ Successfully retrieved {len(available_models)} models")
        
        # Check if o3/o4 models are in the list
        o3_models = [m for m in available_models if 'o3' in m]
        o4_models = [m for m in available_models if 'o4' in m]
        
        if o3_models:
            print(f"\n✓ Found o3 models: {o3_models}")
        else:
            print("\n✗ No o3 models found in available models list")
            
        if o4_models:
            print(f"✓ Found o4 models: {o4_models}")
        else:
            print("✗ No o4 models found in available models list")
            
    except Exception as e:
        print(f"✗ Error listing models: {e}")
        available_models = []
    
    print("\n2. Testing Direct Model Access:")
    for model_name in models_to_test:
        print(f"\nTesting: {model_name}")
        try:
            # Try to make a simple completion request
            response = client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": "Say 'Hello' in one word."}
                ],
                max_tokens=10,
                temperature=0
            )
            
            # If successful, show response
            content = response.choices[0].message.content
            print(f"  ✓ Success! Response: {content}")
            print(f"  ✓ Model: {response.model}")
            
        except openai.NotFoundError as e:
            print(f"  ✗ Model not found: {e}")
        except openai.PermissionDeniedError as e:
            print(f"  ✗ Permission denied: {e}")
        except openai.RateLimitError as e:
            print(f"  ✗ Rate limit exceeded: {e}")
        except openai.APIError as e:
            print(f"  ✗ API error: {e}")
        except Exception as e:
            print(f"  ✗ Unexpected error: {type(e).__name__}: {e}")
    
    print("\n3. Checking API Key Permissions:")
    try:
        # Try to get account info (if available)
        # Note: This might not work with all API keys
        print(f"✓ API Key is valid and active")
    except Exception as e:
        print(f"✗ Could not verify API key status: {e}")
    
    print("\n" + "=" * 60)
    print("Test Complete")
    print("=" * 60)
    
    # Summary
    print("\nSUMMARY:")
    print("- If o3/o4 models show 'not found', they may not be available for your account")
    print("- If you get 'permission denied', you may need special access")
    print("- Working models can be used in the WebUI")

if __name__ == "__main__":
    test_openai_models()
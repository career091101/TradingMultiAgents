#\!/usr/bin/env python3
"""
Check available OpenAI models using the API
"""

import os
from openai import OpenAI

# Initialize the client
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    print("❌ Error: OPENAI_API_KEY not set")
    exit(1)

client = OpenAI(api_key=api_key)

print("🔍 Fetching available models from OpenAI API...\n")

try:
    # List all available models
    models = client.models.list()
    
    # Organize models by type
    chat_models = []
    o_series_models = []
    embedding_models = []
    other_models = []
    
    for model in models.data:
        model_id = model.id
        
        # Categorize models
        if any(prefix in model_id for prefix in ["gpt-", "davinci", "curie", "babbage", "ada"]):
            if "embedding" not in model_id:
                chat_models.append(model_id)
        elif model_id.startswith("o") and model_id[1].isdigit():  # o1, o3, o4 series
            o_series_models.append(model_id)
        elif "embedding" in model_id:
            embedding_models.append(model_id)
        else:
            other_models.append(model_id)
    
    # Print results
    print("✅ CHAT MODELS (GPT Series):")
    for model in sorted(chat_models):
        print(f"   - {model}")
    
    print(f"\n✅ O-SERIES MODELS (Reasoning Models):")
    if o_series_models:
        for model in sorted(o_series_models):
            print(f"   - {model}")
    else:
        print("   ⚠️ No o-series models found (o1, o3, o4-mini)")
    
    print(f"\n✅ EMBEDDING MODELS:")
    for model in sorted(embedding_models)[:5]:  # Show first 5
        print(f"   - {model}")
    if len(embedding_models) > 5:
        print(f"   ... and {len(embedding_models) - 5} more")
    
    # Test specific models
    print("\n🧪 TESTING SPECIFIC MODELS:")
    test_models = [
        "o3",
        "o4-mini", 
        "o3-2025-04-16",
        "o4-mini-2025-04-16",
        "openai/o3-2025-04-16",
        "openai/o4-mini-2025-04-16",
        "gpt-4o",
        "gpt-4o-mini"
    ]
    
    for model_name in test_models:
        try:
            # Try a simple completion to test access
            response = client.chat.completions.create(
                model=model_name,
                messages=[{"role": "user", "content": "Say 'ok'"}],
                max_tokens=5
            )
            print(f"   ✅ {model_name}: ACCESSIBLE")
        except Exception as e:
            error_msg = str(e)
            if "does not exist" in error_msg:
                print(f"   ❌ {model_name}: MODEL NOT FOUND")
            elif "access" in error_msg.lower():
                print(f"   ⚠️ {model_name}: ACCESS DENIED")
            else:
                print(f"   ❌ {model_name}: ERROR - {error_msg[:50]}...")
    
    # Summary
    print(f"\n📊 SUMMARY:")
    print(f"   Total models available: {len(models.data)}")
    print(f"   Chat models: {len(chat_models)}")
    print(f"   O-series models: {len(o_series_models)}")
    print(f"   Embedding models: {len(embedding_models)}")
    
except Exception as e:
    print(f"❌ Error fetching models: {e}")
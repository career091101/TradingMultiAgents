#!/usr/bin/env python3
"""
Fix for using o3/o4 models with LangChain
Based on the latest documentation and community solutions
"""

from typing import Optional, Dict, Any, List
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

class O3O4CompatibleLLMClient:
    """LLM client that works with both standard models and o3/o4 models"""
    
    def __init__(self, model_name: str, temperature: float = 0.7, max_tokens: Optional[int] = 2000):
        self.model_name = model_name
        self.is_o_series = model_name.startswith(('o1', 'o3', 'o4'))
        
        if self.is_o_series:
            # For o3/o4 models, use max_completion_tokens
            self.llm = ChatOpenAI(
                model=model_name,
                temperature=temperature,
                max_completion_tokens=max_tokens,  # Use this for o-series
                reasoning={
                    "effort": "medium",
                    "summary": "auto"
                }
            )
        else:
            # For standard models
            self.llm = ChatOpenAI(
                model=model_name,
                temperature=temperature,
                max_tokens=max_tokens
            )
    
    def convert_system_message(self, system_content: str, user_content: str) -> str:
        """Convert system message to user message format for o-series models"""
        return f"Instructions: {system_content}\n\nRequest: {user_content}"
    
    async def generate(self, 
                      prompt: str, 
                      system_message: Optional[str] = None,
                      context: Optional[Dict[str, Any]] = None) -> str:
        """Generate response handling o-series compatibility"""
        
        messages = []
        
        if self.is_o_series and system_message:
            # For o-series: merge system message into user message
            combined_prompt = self.convert_system_message(system_message, prompt)
            if context:
                combined_prompt += f"\n\nContext: {context}"
            messages = [HumanMessage(content=combined_prompt)]
        else:
            # For standard models: use normal message structure
            if system_message:
                messages.append(SystemMessage(content=system_message))
            
            full_prompt = prompt
            if context:
                full_prompt += f"\n\nContext: {context}"
            messages.append(HumanMessage(content=full_prompt))
        
        # Invoke the model
        response = await self.llm.ainvoke(messages)
        
        # Handle response based on model type
        if self.is_o_series and hasattr(response, 'text'):
            return response.text()
        else:
            return response.content


# Example usage function
async def test_o3_o4_compatibility():
    """Test function to verify o3/o4 compatibility"""
    
    # Test with different models
    models_to_test = [
        "o3-2025-04-16",
        "o4-mini-2025-04-16", 
        "gpt-4-turbo-preview",
        "gpt-3.5-turbo"
    ]
    
    for model in models_to_test:
        print(f"\nTesting {model}...")
        try:
            client = O3O4CompatibleLLMClient(model, temperature=0)
            
            # Test with system message
            response = await client.generate(
                prompt="What is 2+2?",
                system_message="You are a helpful math tutor. Always explain your reasoning.",
                context={"subject": "basic arithmetic"}
            )
            
            print(f"✓ Success: {response[:100]}...")
            
        except Exception as e:
            print(f"✗ Error: {e}")


# Patch for existing LLMClient
def create_patched_llm_client(config):
    """Create a patched LLM client that works with o3/o4"""
    
    # Detect model type
    is_o_series = config.deep_think_model.startswith(('o1', 'o3', 'o4'))
    
    if is_o_series:
        # Use max_completion_tokens for o-series
        deep_llm = ChatOpenAI(
            model=config.deep_think_model,
            temperature=config.temperature,
            max_completion_tokens=config.max_tokens,  # Changed parameter
            timeout=config.timeout,
            reasoning={"effort": "medium", "summary": "auto"}
        )
        
        fast_llm = ChatOpenAI(
            model=config.quick_think_model,
            temperature=config.temperature,
            max_completion_tokens=config.max_tokens,  # Changed parameter
            timeout=config.timeout,
            reasoning={"effort": "low", "summary": "auto"}
        )
    else:
        # Standard initialization
        deep_llm = ChatOpenAI(
            model=config.deep_think_model,
            temperature=config.temperature,
            max_tokens=config.max_tokens,
            timeout=config.timeout
        )
        
        fast_llm = ChatOpenAI(
            model=config.quick_think_model,
            temperature=config.temperature,
            max_tokens=config.max_tokens,
            timeout=config.timeout
        )
    
    return deep_llm, fast_llm


if __name__ == "__main__":
    import asyncio
    
    print("O3/O4 LangChain Compatibility Solution")
    print("=" * 50)
    print("\nThis shows how to properly use o3/o4 models with LangChain")
    print("\nKey changes:")
    print("1. Use max_completion_tokens instead of max_tokens")
    print("2. Convert system messages to user messages")
    print("3. Add reasoning parameters for o-series models")
    
    # Run test if desired
    # asyncio.run(test_o3_o4_compatibility())
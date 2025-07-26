"""LLM client for actual agent integration"""

import os
import asyncio
import json
import logging
import re  # Fix: Import re module for regex operations
from typing import Dict, Any, Optional, List
from datetime import datetime
from decimal import Decimal
from pathlib import Path

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from ..core.config import LLMConfig
from ..utils.retry_handler import LLMRetryHandler
from ..utils.cache_manager import LLMCacheManager


class BacktestJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder for backtest objects"""
    
    def default(self, obj):
        # Handle datetime
        if isinstance(obj, datetime):
            return obj.isoformat()
        
        # Handle Decimal
        if isinstance(obj, Decimal):
            return float(obj)
            
        # Handle Enum (including TradeAction)
        if hasattr(obj, 'value') and hasattr(obj, 'name'):
            return obj.value
            
        # Handle objects with to_dict method
        if hasattr(obj, 'to_dict'):
            return obj.to_dict()
            
        # Handle dataclasses (including MarketData, AgentOutput, etc.)
        if hasattr(obj, '__dataclass_fields__'):
            result = {}
            for field in obj.__dataclass_fields__:
                value = getattr(obj, field)
                # Recursively handle nested objects
                if isinstance(value, datetime):
                    result[field] = value.isoformat()
                elif isinstance(value, Decimal):
                    result[field] = float(value)
                elif hasattr(value, '__dataclass_fields__'):
                    result[field] = self.default(value)
                elif isinstance(value, dict):
                    # Handle dictionaries with non-serializable values
                    result[field] = {k: self.default(v) if not isinstance(v, (str, int, float, bool, type(None))) else v 
                                   for k, v in value.items()}
                elif isinstance(value, list):
                    # Handle lists with non-serializable values
                    result[field] = [self.default(item) if not isinstance(item, (str, int, float, bool, type(None))) else item 
                                   for item in value]
                else:
                    result[field] = value
            return result
            
        # Handle any other object by converting to string
        return str(obj)


class OpenAILLMClient:
    """OpenAI LLM client for agent integration"""
    
    def __init__(self, config: LLMConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Initialize retry handler
        self.retry_handler = LLMRetryHandler()
        
        # Initialize cache manager
        self.cache_manager = LLMCacheManager()
        self._cache_started = False
        
        # Setup debug directory for LLM responses
        self.debug_dir = Path("logs/llm_debug")
        self.debug_dir.mkdir(parents=True, exist_ok=True)
        self.response_counter = 0
        
        # Check if using mock mode
        self.logger.info(f"Initializing LLM client with models: deep={config.deep_think_model}, quick={config.quick_think_model}")
        if config.deep_think_model == "mock" or config.quick_think_model == "mock":
            self.logger.info("Mock mode detected - skipping OpenAI initialization")
            self.deep_llm = None
            self.fast_llm = None
            self.is_mock = True
            return
        
        self.is_mock = False
        
        # Initialize OpenAI clients for deep and fast thinking
        # Check if using o-series models (including date-versioned models)
        deep_model = config.deep_think_model.lower()
        fast_model = config.quick_think_model.lower()
        
        is_o_series_deep = (deep_model.startswith(('o1', 'o3', 'o4')) or 
                           '-o1-' in deep_model or '-o3-' in deep_model or '-o4-' in deep_model)
        is_o_series_fast = (fast_model.startswith(('o1', 'o3', 'o4')) or 
                           '-o1-' in fast_model or '-o3-' in fast_model or '-o4-' in fast_model)
        
        # Store config for agent-specific settings
        self.agent_max_tokens = getattr(config, 'agent_max_tokens', {})
        
        # Deep thinking model
        if is_o_series_deep:
            self.deep_llm = ChatOpenAI(
                model=config.deep_think_model,
                temperature=1.0,  # o3/o4 models only support temperature=1.0
                max_completion_tokens=config.max_tokens,  # Use max_completion_tokens for o-series
                timeout=config.timeout
            )
        else:
            self.deep_llm = ChatOpenAI(
                model=config.deep_think_model,
                temperature=config.temperature,
                max_tokens=config.max_tokens,
                timeout=config.timeout
            )
        
        # Fast thinking model
        if is_o_series_fast:
            self.fast_llm = ChatOpenAI(
                model=config.quick_think_model,
                temperature=1.0,  # o3/o4 models only support temperature=1.0
                max_completion_tokens=config.max_tokens,  # Use max_completion_tokens for o-series
                timeout=config.timeout
            )
        else:
            self.fast_llm = ChatOpenAI(
                model=config.quick_think_model,
                temperature=config.temperature,
                max_tokens=config.max_tokens,
                timeout=config.timeout
            )
        
    async def generate(
        self,
        prompt: str,
        context: Dict[str, Any],
        use_deep_thinking: bool = False,
        system_message: Optional[str] = None,
        agent_name: Optional[str] = None,
        use_cache: bool = True
    ) -> str:
        """Generate response from LLM with retry logic and caching"""
        
        # Mock mode
        if self.is_mock:
            return self._generate_mock_response(prompt, context, agent_name)
        
        # Ensure cache is started
        if use_cache and not self._cache_started:
            await self.cache_manager.start()
            self._cache_started = True
        
        # Try to get from cache if enabled
        if use_cache and agent_name:
            cached_result = await self.cache_manager.get_llm_result(
                agent_name,
                prompt,
                context,
                use_deep_thinking
            )
            if cached_result is not None:
                self.logger.debug(f"Cache hit for {agent_name}")
                return cached_result
        
        async def _generate():
            llm = self.deep_llm if use_deep_thinking else self.fast_llm
            model_name = self.config.deep_think_model if use_deep_thinking else self.config.quick_think_model
            is_o_series = model_name.startswith(('o1', 'o3', 'o4'))
            
            # Get agent-specific max_tokens if available
            agent_tokens = self.agent_max_tokens.get(agent_name, self.config.max_tokens) if agent_name else self.config.max_tokens
            
            # Create a new LLM instance with agent-specific tokens if different
            if agent_tokens != self.config.max_tokens:
                if is_o_series:
                    llm = ChatOpenAI(
                        model=model_name,
                        temperature=1.0,
                        max_completion_tokens=agent_tokens,
                        timeout=self.config.timeout
                    )
                else:
                    llm = ChatOpenAI(
                        model=model_name,
                        temperature=self.config.temperature,
                        max_tokens=agent_tokens,
                        timeout=self.config.timeout
                    )
                self.logger.debug(f"Using agent-specific max_tokens for {agent_name}: {agent_tokens}")
            
            messages = []
            # Initialize prompt variables to ensure they're in scope
            combined_prompt = ""
            full_prompt = ""
            
            # Handle o-series models differently
            if is_o_series and system_message:
                # For o-series: merge system message into user message
                # Convert objects to dict if they have to_dict method
                def convert_to_dict(obj):
                    if hasattr(obj, 'to_dict'):
                        return obj.to_dict()
                    elif isinstance(obj, dict):
                        return {k: convert_to_dict(v) for k, v in obj.items()}
                    elif isinstance(obj, list):
                        return [convert_to_dict(item) for item in obj]
                    return obj
                
                converted_context = convert_to_dict(context)
                context_str = json.dumps(converted_context, ensure_ascii=False, indent=2, cls=BacktestJSONEncoder)
                combined_prompt = f"Instructions: {system_message}\n\nRequest: {prompt}\n\nContext:\n{context_str}"
                messages.append(HumanMessage(content=combined_prompt))
            else:
                # For standard models: use normal structure
                if system_message:
                    messages.append(SystemMessage(content=system_message))
                
                # Add context as part of the prompt
                context_str = json.dumps(context, ensure_ascii=False, indent=2, cls=BacktestJSONEncoder)
                full_prompt = f"{prompt}\n\nContext:\n{context_str}"
                messages.append(HumanMessage(content=full_prompt))
            
            response = await llm.ainvoke(messages)
            result = response.content if hasattr(response, 'content') else str(response)
            
            # Save raw response to file for debugging
            self._save_debug_response(agent_name, prompt, result, context)
            
            # Debug logging
            self.logger.info(f"[LLM DEBUG] Response for {agent_name}: {len(result)} chars")
            self.logger.debug(f"[LLM DEBUG] First 500 chars: {result[:500]}")
            self.logger.debug(f"[LLM DEBUG] Model: {model_name}, Agent: {agent_name}")
            self.logger.debug(f"[LLM DEBUG] Prompt length: {len(prompt)}, Context keys: {list(context.keys()) if context else 'None'}")
            
            # Handle empty responses (o3/o4-mini sometimes return empty)
            if not result or len(result.strip()) == 0:
                self.logger.warning(f"Empty response from LLM for {agent_name}, retrying...")
                # Retry once with a slight modification to the prompt
                # Use the appropriate prompt variable based on model type
                retry_prompt = combined_prompt if is_o_series else full_prompt
                messages[-1] = HumanMessage(content=retry_prompt + "\n\nPlease provide a detailed response.")
                response = await llm.ainvoke(messages)
                result = response.content if hasattr(response, 'content') else str(response)
                
            return result
        
        try:
            # Execute with retry handler
            result = await self.retry_handler.execute_with_retry(_generate)
            
            # Cache the result if enabled
            if use_cache and agent_name:
                await self.cache_manager.cache_llm_result(
                    agent_name,
                    prompt,
                    context,
                    result,
                    use_deep_thinking
                )
                
            return result
        except Exception as e:
            self.logger.error(f"LLM generation failed after retries: {e}")
            self.logger.error(f"Failed for agent: {agent_name}")
            self.logger.error(f"Model config: deep={self.config.deep_think_model}, quick={self.config.quick_think_model}")
            self.logger.error(f"Use deep thinking: {use_deep_thinking}")
            self.logger.error(f"Prompt preview: {prompt[:200]}...")
            # Log circuit breaker state
            cb_state = self.retry_handler.get_circuit_state()
            self.logger.error(f"Circuit breaker state: {cb_state}")
            raise
    
    def _generate_mock_response(self, prompt: str, context: Dict[str, Any], agent_name: Optional[str] = None) -> str:
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
            
    async def generate_structured(
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
        
        # Convert context to JSON-serializable format using our custom encoder
        try:
            # First convert the context to JSON string using our custom encoder
            context_json = json.dumps(context, cls=BacktestJSONEncoder)
            # Then parse it back to get a clean serializable dict
            serializable_context = json.loads(context_json)
        except Exception as e:
            self.logger.error(f"Failed to serialize context: {e}")
            # Fallback to manual conversion
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
                elif hasattr(obj, 'value') and hasattr(obj, 'name'):  # Enum
                    return obj.value
                return obj
            
            serializable_context = convert_to_dict(context)
        
        # Solution 1: Use OpenAI Function Calling for structured outputs
        try:
            # Check if we're using function calling (available for non-o-series models)
            model_name = self.config.deep_think_model if use_deep_thinking else self.config.quick_think_model
            is_o_series = model_name.lower().startswith(('o1', 'o3', 'o4'))
            
            # Use function calling for GPT models (not available for o-series)
            if not is_o_series and not self.is_mock:
                return await self._generate_with_function_calling(
                    prompt, serializable_context, output_schema, 
                    use_deep_thinking, system_message, agent_name, use_cache
                )
        except Exception as e:
            self.logger.warning(f"Function calling failed, falling back to prompt-based: {e}")
        
        # Fallback to improved prompt-based approach
        return await self._generate_with_improved_prompt(
            prompt, serializable_context, output_schema,
            use_deep_thinking, system_message, agent_name, use_cache
        )
    
    async def _generate_with_function_calling(
        self,
        prompt: str,
        context: Dict[str, Any],
        output_schema: Dict[str, Any],
        use_deep_thinking: bool,
        system_message: Optional[str],
        agent_name: Optional[str],
        use_cache: bool
    ) -> Dict[str, Any]:
        """Use OpenAI Function Calling for guaranteed structured output"""
        try:
            from langchain_core.utils.function_calling import convert_to_openai_function
            from langchain_core.output_parsers.openai_functions import JsonOutputFunctionsParser
        except ImportError:
            # Fallback if langchain version doesn't have these imports
            raise ImportError("Function calling not available in this langchain version")
        
        # Create a function definition from the schema
        function_name = f"{agent_name or 'response'}_output".replace(" ", "_").lower()
        
        # Convert schema to OpenAI function format
        function_def = {
            "name": function_name,
            "description": f"Output for {agent_name or 'agent'}",
            "parameters": {
                "type": "object",
                "properties": output_schema,
                "required": list(output_schema.keys())
            }
        }
        
        # Setup LLM with function
        llm = self.deep_llm if use_deep_thinking else self.fast_llm
        llm_with_functions = llm.bind(
            functions=[function_def],
            function_call={"name": function_name}
        )
        
        # Create parser
        parser = JsonOutputFunctionsParser()
        
        # Build messages
        messages = []
        if system_message:
            messages.append(SystemMessage(content=system_message))
        
        # Add context to prompt
        context_str = json.dumps(context, ensure_ascii=False, indent=2)
        full_prompt = f"{prompt}\n\nContext:\n{context_str}"
        messages.append(HumanMessage(content=full_prompt))
        
        # Generate with function calling
        response = await llm_with_functions.ainvoke(messages)
        
        # Parse the function call
        result = parser.parse(response)
        
        # Log success
        self.logger.info(f"Function calling successful for {agent_name}")
        self._save_debug_response(f"{agent_name}_function", prompt, json.dumps(result), context)
        
        return result
    
    async def _generate_with_improved_prompt(
        self,
        prompt: str,
        context: Dict[str, Any],
        output_schema: Dict[str, Any],
        use_deep_thinking: bool,
        system_message: Optional[str],
        agent_name: Optional[str],
        use_cache: bool
    ) -> Dict[str, Any]:
        """Generate with improved prompting strategy (Solution 2)"""
        
        # Solution 2: Use concrete examples instead of schema
        example_response = self._create_example_response(output_schema, agent_name)
        
        # Build improved prompt with examples
        improved_prompt = f"""{prompt}

IMPORTANT: You must respond with valid JSON only. No explanations, no markdown, just JSON.

Example of the EXACT format you must use:
{json.dumps(example_response, ensure_ascii=False, indent=2)}

Your response must follow this exact structure with appropriate values based on the context.
"""
        
        try:
            # Use serializable_context instead of raw context
            response = await self.generate(
                improved_prompt,
                context,
                use_deep_thinking,
                system_message,
                agent_name,
                use_cache
            )
            
            # Solution 3: Multi-layer validation strategy
            return await self._parse_with_validation(response, output_schema, agent_name)
            
        except Exception as e:
            self.logger.error(f"Failed to generate structured response: {e}")
            return self._create_default_response(output_schema)
    
    def _create_example_response(self, schema: Dict[str, Any], agent_name: Optional[str]) -> Dict[str, Any]:
        """Create a concrete example response based on schema and agent type"""
        example = {}
        
        # Customize examples based on agent name
        if agent_name:
            agent_lower = agent_name.lower()
            
            if "risk" in agent_lower and "manager" in agent_lower:
                # Risk Manager specific example
                example = {
                    "action": "BUY",
                    "quantity": 100,
                    "position_size_pct": 0.1,
                    "stop_loss": 95.0,
                    "take_profit": 110.0,
                    "risk_assessment": {
                        "risk_level": "medium",
                        "risk_score": 0.4
                    },
                    "confidence": 0.7,
                    "rationale": "Strong technical indicators support entry"
                }
            elif "trader" in agent_lower:
                example = {
                    "action": "BUY",
                    "confidence": 0.75,
                    "entry_strategy": "limit_order",
                    "rationale": "Bullish momentum confirmed"
                }
            elif "bull" in agent_lower:
                example = {
                    "recommendation": "BUY",
                    "confidence": 0.8,
                    "rationale": "Strong growth potential identified"
                }
            elif "bear" in agent_lower:
                example = {
                    "recommendation": "SELL",
                    "confidence": 0.7,
                    "rationale": "Overvaluation concerns"
                }
            else:
                # Generic example based on schema
                for key, value in schema.items():
                    if isinstance(value, dict):
                        if value.get("enum") and "action" in key.lower():
                            example[key] = "HOLD"
                        elif value.get("type") == "string":
                            example[key] = "Analysis result"
                        elif value.get("type") == "number":
                            example[key] = 0.5
                        elif value.get("type") == "boolean":
                            example[key] = True
                        elif value.get("type") == "array":
                            example[key] = ["item1", "item2"]
                        elif value.get("type") == "object":
                            example[key] = {"sub_field": "value"}
        
        return example
    
    async def _parse_with_validation(self, response: str, schema: Dict[str, Any], agent_name: str) -> Dict[str, Any]:
        """Parse response with multi-layer validation (Solution 3)"""
        
        # Layer 1: Try direct JSON parsing
        try:
            # First, try to parse the entire response as JSON
            result = json.loads(response.strip())
            if self._validate_against_schema(result, schema):
                return result
        except json.JSONDecodeError:
            pass
        
        # Layer 2: Extract JSON from text
        json_patterns = [
            r'```json\s*(\{.*?\})\s*```',  # JSON in code blocks
            r'```\s*(\{.*?\})\s*```',       # Code blocks without json tag
            r'(\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\})',  # Nested JSON
            r'(\{.*\})',                    # Any JSON object
        ]
        
        for pattern in json_patterns:
            matches = re.findall(pattern, response, re.DOTALL | re.IGNORECASE)
            for match in matches:
                try:
                    json_text = match.strip()
                    result = json.loads(json_text)
                    if self._validate_against_schema(result, schema):
                        self.logger.info(f"Successfully extracted valid JSON for {agent_name}")
                        return result
                except json.JSONDecodeError:
                    continue
        
        # Layer 3: Try to fix common JSON issues
        cleaned = self._clean_json_response(response)
        if cleaned:
            try:
                result = json.loads(cleaned)
                if self._validate_against_schema(result, schema):
                    return result
            except json.JSONDecodeError:
                pass
        
        # Layer 4: Parse from text with improved logic
        return self._parse_text_response(response, schema)
    
    def _validate_against_schema(self, data: Dict[str, Any], schema: Dict[str, Any]) -> bool:
        """Validate that data matches expected schema structure"""
        # Check if all required fields are present
        for key in schema.keys():
            if key not in data:
                return False
        
        # Additional validation for action fields
        action_fields = ["action", "recommendation", "final_decision", "investment_decision"]
        for field in action_fields:
            if field in data and data[field] not in ["BUY", "SELL", "HOLD", None]:
                return False
        
        return True
    
    def _clean_json_response(self, response: str) -> Optional[str]:
        """Clean common JSON formatting issues and attempt to recover truncated JSON"""
        # Remove any text before the first {
        start = response.find('{')
        if start == -1:
            return None
        
        # Find the matching closing brace
        depth = 0
        end = -1
        for i in range(start, len(response)):
            if response[i] == '{':
                depth += 1
            elif response[i] == '}':
                depth -= 1
                if depth == 0:
                    end = i + 1
                    break
        
        if end == -1:
            # Try to recover truncated JSON
            json_text = response[start:]
            return self._attempt_json_recovery(json_text)
        
        json_text = response[start:end]
        
        # Fix common issues
        # Remove type annotations that LLMs sometimes add
        json_text = re.sub(r'"type":\s*"(string|number|boolean)"', '', json_text)
        # Fix nested type definitions
        json_text = re.sub(r':\s*\{\s*"type":\s*"([^"]+)"\s*\}', r': "\1"', json_text)
        
        return json_text
    
    def _attempt_json_recovery(self, truncated_json: str) -> Optional[str]:
        """Attempt to recover data from truncated JSON"""
        try:
            # Common patterns for closing truncated JSON
            # Count open braces and brackets
            brace_count = truncated_json.count('{') - truncated_json.count('}')
            bracket_count = truncated_json.count('[') - truncated_json.count(']')
            
            # Check if we're in the middle of a string
            in_string = False
            escape_next = False
            for char in truncated_json:
                if escape_next:
                    escape_next = False
                    continue
                if char == '\\':
                    escape_next = True
                    continue
                if char == '"':
                    in_string = not in_string
            
            # Build closing sequence
            closing = ''
            if in_string:
                closing += '"'
            closing += ']' * bracket_count
            closing += '}' * brace_count
            
            # Try to parse the recovered JSON
            recovered = truncated_json + closing
            test_parse = json.loads(recovered)
            
            self.logger.warning(f"Successfully recovered truncated JSON with {len(closing)} closing characters")
            return recovered
            
        except Exception as e:
            self.logger.debug(f"JSON recovery failed: {e}")
            return None

    def _parse_text_response(self, response: str, schema: Dict[str, Any]) -> Dict[str, Any]:
        """Try to parse a text response into the expected schema"""
        result = self._create_default_response(schema)
        
        # Log the raw response for debugging
        self.logger.debug(f"Parsing text response: {response[:500]}...")
        
        # Look for common patterns in text
        response_lower = response.lower()
        
        # Improved action extraction with more patterns
        buy_patterns = ["買い", "buy", "購入", "買う", "bullish", "long", "買付", "買い推奨"]
        sell_patterns = ["売り", "sell", "売却", "売る", "bearish", "short", "売付", "売り推奨"]
        hold_patterns = ["保有", "hold", "維持", "ホールド", "中立", "待機", "様子見"]
        
        # Count occurrences and determine action
        buy_count = sum(1 for pattern in buy_patterns if pattern in response_lower)
        sell_count = sum(1 for pattern in sell_patterns if pattern in response_lower)
        hold_count = sum(1 for pattern in hold_patterns if pattern in response_lower)
        
        # Determine action based on highest count
        if buy_count > sell_count and buy_count > hold_count:
            action = "BUY"
        elif sell_count > buy_count and sell_count > hold_count:
            action = "SELL"
        else:
            action = "HOLD"
        
        # Set all action-related fields
        action_fields = ["action", "recommendation", "investment_decision", "final_decision", "decision"]
        for field in action_fields:
            if field in result:
                result[field] = action
        
        # Extract confidence with improved patterns
        confidence_patterns = [
            r'confidence[:\s]+([0-9.]+)',
            r'確信度[:\s]+([0-9.]+)',
            r'信頼度[:\s]+([0-9.]+)',
            r'([0-9.]+)%?\s*(?:confidence|確信|信頼)',
            r'(?:confidence|確信度|信頼度)[:\s]*([0-9.]+)',
        ]
        
        confidence_found = False
        for pattern in confidence_patterns:
            match = re.search(pattern, response, re.IGNORECASE)
            if match:
                try:
                    conf = float(match.group(1))
                    if conf > 1:  # Percentage
                        conf = conf / 100
                    conf = min(1.0, max(0.0, conf))
                    
                    # Set all confidence-related fields
                    confidence_fields = ["confidence", "confidence_level", "confidence_score"]
                    for field in confidence_fields:
                        if field in result:
                            result[field] = conf
                    confidence_found = True
                    break
                except:
                    pass
        
        # If no confidence found, set based on action strength
        if not confidence_found:
            if action in ["BUY", "SELL"]:
                default_conf = 0.6  # Moderate confidence for actions
            else:
                default_conf = 0.5  # Lower confidence for HOLD
            
            confidence_fields = ["confidence", "confidence_level", "confidence_score"]
            for field in confidence_fields:
                if field in result:
                    result[field] = default_conf
        
        # Extract numeric values for specific fields
        numeric_fields = {
            "quantity": [r'quantity[:\s]+([0-9.]+)', r'数量[:\s]+([0-9.]+)', r'([0-9.]+)\s*(?:shares|株)'],
            "position_size_pct": [r'position[:\s]+([0-9.]+)%?', r'ポジション[:\s]+([0-9.]+)%?'],
            "stop_loss": [r'stop\s*loss[:\s]+([0-9.]+)', r'ストップロス[:\s]+([0-9.]+)'],
            "take_profit": [r'take\s*profit[:\s]+([0-9.]+)', r'利益確定[:\s]+([0-9.]+)'],
        }
        
        for field, patterns in numeric_fields.items():
            if field in result:
                for pattern in patterns:
                    match = re.search(pattern, response, re.IGNORECASE)
                    if match:
                        try:
                            value = float(match.group(1))
                            if field == "position_size_pct" and value > 1:
                                value = value / 100
                            result[field] = value
                            break
                        except:
                            pass
        
        # Set rationale to meaningful excerpt
        if "rationale" in result:
            # Try to extract a sentence containing the decision
            sentences = re.split(r'[。.!?]', response)
            relevant_sentence = ""
            for sentence in sentences:
                if any(word in sentence.lower() for word in buy_patterns + sell_patterns + hold_patterns):
                    relevant_sentence = sentence.strip()
                    break
            
            result["rationale"] = relevant_sentence[:500] if relevant_sentence else response[:500]
        
        # Handle nested objects in schema
        if "risk_assessment" in result and isinstance(result["risk_assessment"], dict):
            result["risk_assessment"]["risk_level"] = "medium"
            result["risk_assessment"]["risk_score"] = 0.5
        
        self.logger.warning(f"Parsed text response to: {result}")
        return result
    def _create_default_response(self, schema: Dict[str, Any]) -> Dict[str, Any]:
        """Create a default response based on the expected schema"""
        default = {}
        
        # Enhanced schema interpretation
        for key, value in schema.items():
            if isinstance(value, dict):
                if "properties" in value:
                    # Nested object with properties
                    default[key] = self._create_default_response(value["properties"])
                elif value.get("type") == "string":
                    # Check for enum values
                    if "enum" in value:
                        # Default to HOLD for action fields, first enum value for others
                        if "action" in key.lower() or "decision" in key.lower():
                            default[key] = "HOLD"
                        else:
                            default[key] = value["enum"][0]
                    else:
                        default[key] = ""
                elif value.get("type") == "number":
                    # Use minimum value if specified, otherwise 0
                    if "minimum" in value:
                        default[key] = value["minimum"]
                    else:
                        default[key] = 0.0
                elif value.get("type") == "boolean":
                    default[key] = False
                elif value.get("type") == "array":
                    default[key] = []
                elif value.get("type") == "object":
                    # Empty object unless it has properties
                    default[key] = {}
                else:
                    # Handle cases where type might be missing
                    if "enum" in value:
                        default[key] = value["enum"][0]
                    else:
                        default[key] = ""
            else:
                # If value is not a dict, use it as default
                default[key] = value
        
        # Ensure critical fields have sensible defaults
        if "action" in default:
            default["action"] = "HOLD"
        if "confidence" in default:
            default["confidence"] = 0.5
        if "rationale" in default:
            default["rationale"] = "Unable to parse response"
                
        return default
        
    def get_retry_stats(self) -> Dict[str, Any]:
        """Get retry handler statistics"""
        return self.retry_handler.get_circuit_state()
        
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        return self.cache_manager.get_stats()
        
    async def cleanup(self) -> None:
        """Cleanup resources"""
        if self._cache_started:
            await self.cache_manager.stop()
            self._cache_started = False
            
    def _save_debug_response(self, agent_name: str, prompt: str, response: str, context: Dict[str, Any]) -> None:
        """Save LLM response to debug file"""
        try:
            self.response_counter += 1
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{timestamp}_{self.response_counter:04d}_{agent_name}.json"
            filepath = self.debug_dir / filename
            
            debug_data = {
                "timestamp": timestamp,
                "agent": agent_name,
                "prompt": prompt,
                "response": response,
                "response_length": len(response),
                "context_keys": list(context.keys()) if context else [],
                "use_japanese": getattr(self.config, 'use_japanese_prompts', False)
            }
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(debug_data, f, ensure_ascii=False, indent=2)
                
            self.logger.info(f"Saved LLM response to: {filepath}")
            
        except Exception as e:
            self.logger.error(f"Failed to save debug response: {e}")


class AgentPrompts:
    """Japanese prompts from the main TradingAgents implementation"""
    
    MARKET_ANALYST_SYSTEM = """あなたは金融市場を分析するトレーディングアシスタントです。あなたの役割は、与えられた市場状況やトレーディング戦略に対して、以下のリストから**最も関連性の高い指標**を選択することです。目標は、重複を避けて補完的な洞察を提供する**最大8つの指標**を選択することです。

技術指標の分析：
- 価格トレンド（上昇/下降/横ばい）
- 移動平均線の状態（SMA、EMA）
- MACD、RSI、ボリンジャーバンドなどの指標
- 出来高分析
- サポート/レジスタンスレベル

分析結果をJSON形式で返してください。"""

    NEWS_ANALYST_SYSTEM = """あなたはニュースと市場センチメントを分析するアナリストです。

分析内容：
- ニュースの重要度評価
- センチメント分析（ポジティブ/ネガティブ/ニュートラル）
- 市場への影響予測
- 関連トピックの抽出

分析結果をJSON形式で返してください。"""

    SOCIAL_MEDIA_ANALYST_SYSTEM = """あなたはソーシャルメディアの動向を分析するアナリストです。

分析内容：
- Reddit、Twitter等のセンチメント
- トレンドスコア
- コミュニティの関心度
- 異常な活動の検出

分析結果をJSON形式で返してください。"""

    FUNDAMENTALS_ANALYST_SYSTEM = """あなたは企業のファンダメンタルズを分析するアナリストです。

分析内容：
- 財務指標（PER、PBR、ROE等）
- 収益成長性
- 負債比率
- バリュエーション評価

分析結果をJSON形式で返してください。"""

    BULL_RESEARCHER_SYSTEM = """あなたは強気派の投資リサーチャーです。深い分析に基づいて、投資機会を見出します。

あなたの役割：
- 成長要因の特定
- 上昇シナリオの構築
- 目標株価の設定
- 投資機会の説明

他のアナリストのレポートを参考に、説得力のある強気論を展開してください。"""

    BEAR_RESEARCHER_SYSTEM = """あなたは慎重派の投資リサーチャーです。リスク要因を詳細に分析します。

あなたの役割：
- リスク要因の特定
- 下落シナリオの構築
- 下値目処の設定
- 警戒すべき点の説明

他のアナリストのレポートを参考に、リスクを重視した分析を行ってください。"""

    RESEARCH_MANAGER_SYSTEM = """あなたは投資調査部門のマネージャーです。Bull研究者とBear研究者の意見を調整し、最終的な投資判断を下します。

あなたの役割：
- 両者の議論を公平に評価
- 投資判断（買い/保有/売り）の決定
- 確信度の設定
- 投資戦略の策定

バランスの取れた判断を行ってください。"""

    TRADER_SYSTEM = """あなたは経験豊富なトレーダーです。投資判断に基づいて具体的な取引計画を立案します。

あなたの役割：
- エントリー戦略の決定
- ポジションサイズの提案
- ストップロス/利益確定レベルの設定
- 取引タイミングの判断

リスク管理を重視した実践的な取引計画を立ててください。"""

    AGGRESSIVE_DEBATOR_SYSTEM = """あなたは積極的なリスクテイクを推奨するリスクアドバイザーです。

あなたの役割：
- 高リターンの機会を強調
- 積極的なポジションサイズを提案
- リスクを取る理由を説明

ただし、無謀ではなく、計算されたリスクテイクを推奨してください。"""

    CONSERVATIVE_DEBATOR_SYSTEM = """あなたは慎重なリスク管理を推奨するリスクアドバイザーです。

あなたの役割：
- 潜在的なリスクを強調
- 保守的なポジションサイズを提案
- 資本保全の重要性を説明

過度に悲観的にならず、バランスの取れた助言を行ってください。"""

    NEUTRAL_DEBATOR_SYSTEM = """あなたは中立的な立場のリスクアドバイザーです。

あなたの役割：
- リスクとリターンのバランスを評価
- 中庸なポジションサイズを提案
- 両面からの視点を提供

客観的で実践的な助言を行ってください。"""

    RISK_MANAGER_SYSTEM = """あなたはリスク管理の最高責任者です。すべての意見を総合し、最終的なリスク調整を行います。

あなたの役割：
- 最終的な取引承認/却下
- リスクパラメータの設定
- ポジションサイズの最終決定
- リスク管理ルールの適用

組織全体のリスクを考慮した決定を行ってください。"""
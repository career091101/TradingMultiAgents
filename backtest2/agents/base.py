"""Base agent class"""

import time
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, Any, Optional
import logging

from ..core.config import LLMConfig
from ..core.types import AgentOutput
from ..memory.agent_memory import AgentMemory


class LLM:
    """Base LLM interface"""
    
    def __init__(self, config: LLMConfig):
        self.config = config
        
    async def generate(self, prompt: str, context: Dict[str, Any]) -> str:
        """Generate response from LLM"""
        raise NotImplementedError


class MockLLM(LLM):
    """Mock LLM for testing"""
    
    async def generate(self, prompt: str, context: Dict[str, Any]) -> str:
        """Generate mock response"""
        # Simple mock response based on agent type
        if "market" in prompt.lower():
            return "Technical indicators suggest neutral market conditions."
        elif "news" in prompt.lower():
            return "Recent news sentiment is slightly positive."
        elif "bull" in prompt.lower():
            return "Strong growth potential based on fundamentals."
        elif "bear" in prompt.lower():
            return "Risk factors suggest caution."
        else:
            return "Analysis complete."


class BaseAgent(ABC):
    """Base class for all agents"""
    
    def __init__(
        self,
        name: str,
        llm_config: LLMConfig,
        memory: AgentMemory,
        use_deep_thinking: bool = False
    ):
        self.name = name
        self.llm_config = llm_config
        self.memory = memory
        self.use_deep_thinking = use_deep_thinking
        self.logger = logging.getLogger(f"Agent.{name}")
        
        # Create LLM instance
        self.llm = self._create_llm(llm_config)
        
    @abstractmethod
    async def process(self, input_data: Dict[str, Any]) -> AgentOutput:
        """Process input and generate output"""
        pass
        
    async def reflect(self, outcome: Dict[str, Any]) -> None:
        """Reflect on outcome for learning"""
        reflection = await self._generate_reflection(outcome)
        if self.memory:
            await self.memory.add_reflection(reflection)
            
    def _create_llm(self, config: LLMConfig) -> LLM:
        """Create LLM instance based on config"""
        # For now, return mock LLM
        # In full implementation, this would create actual LLM clients
        return MockLLM(config)
        
    async def _generate_reflection(self, outcome: Dict[str, Any]) -> Dict[str, Any]:
        """Generate reflection from outcome"""
        prompt = f"""
        Reflect on the following trading outcome:
        {outcome}
        
        What went well? What could be improved?
        """
        
        response = await self.llm.generate(prompt, outcome)
        
        return {
            'timestamp': datetime.now(),
            'outcome': outcome,
            'reflection': response
        }
        
    def _create_output(
        self,
        content: Any,
        confidence: float,
        processing_time: float,
        rationale: Optional[str] = None
    ) -> AgentOutput:
        """Create standardized agent output"""
        return AgentOutput(
            agent_name=self.name,
            timestamp=datetime.now(),
            output_type=self.__class__.__name__,
            content=content,
            confidence=confidence,
            processing_time=processing_time,
            rationale=rationale
        )
"""Agent memory system"""

from typing import Dict, List, Any, Optional
from datetime import datetime


class AgentMemory:
    """Memory system for individual agents"""
    
    def __init__(self, agent_name: str, memory_store: Optional['MemoryStore'] = None):
        self.agent_name = agent_name
        self.memory_store = memory_store
        
    async def add_memory(self, memory: Dict[str, Any]) -> None:
        """Add a memory"""
        memory_data = {
            'timestamp': datetime.now().isoformat(),
            'type': 'general',
            **memory
        }
        
        if self.memory_store:
            await self.memory_store.add(self.agent_name, memory_data)
    
    async def get_recent_memories(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent memories"""
        if self.memory_store:
            return await self.memory_store.get_recent(self.agent_name, limit)
        return []
    
    async def add_reflection(self, reflection: Dict[str, Any]) -> None:
        """Add a reflection"""
        reflection_data = {
            'type': 'reflection',
            'timestamp': datetime.now().isoformat(),
            **reflection
        }
        
        if self.memory_store:
            await self.memory_store.add(self.agent_name, reflection_data)
    
    async def add_trading_outcome(self, outcome: Dict[str, Any]) -> None:
        """Add trading outcome for learning"""
        outcome_data = {
            'type': 'trading_outcome',
            'timestamp': datetime.now().isoformat(),
            **outcome
        }
        
        if self.memory_store:
            await self.memory_store.add(self.agent_name, outcome_data)
    
    async def get_similar_situations(self, situation: Dict[str, Any], limit: int = 5) -> List[Dict[str, Any]]:
        """Get memories of similar situations"""
        if self.memory_store:
            # Simple similarity search based on market conditions
            query = {
                'type': 'trading_outcome',
                'symbol': situation.get('symbol')
            }
            return await self.memory_store.search(self.agent_name, query, limit)
        return []
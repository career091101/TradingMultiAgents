"""Simple in-memory store for agent memories"""

from typing import Dict, List, Any, Optional
from datetime import datetime
from collections import defaultdict
import json
import logging
from pathlib import Path


class MemoryStore:
    """Simple in-memory storage for agent memories"""
    
    def __init__(self, persistence_path: Optional[Path] = None, max_memories_per_agent: int = 1000):
        self.persistence_path = persistence_path
        self.memories: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        self.logger = logging.getLogger("MemoryStore")
        self.max_memories_per_agent = max_memories_per_agent
        
        # Load existing memories if persistence is enabled
        if persistence_path and persistence_path.exists():
            self.load()
    
    async def add(self, agent_name: str, memory: Dict[str, Any]) -> None:
        """Add a memory for an agent"""
        memory['stored_at'] = datetime.now().isoformat()
        self.memories[agent_name].append(memory)
        
        # Limit memory size to prevent unbounded growth
        if len(self.memories[agent_name]) > self.max_memories_per_agent:
            # Keep only the most recent memories
            self.memories[agent_name] = self.memories[agent_name][-self.max_memories_per_agent:]
        
        # Auto-save if persistence is enabled
        if self.persistence_path:
            self.save()
    
    async def get_recent(
        self, 
        agent_name: str, 
        limit: int = 10,
        memory_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get recent memories for an agent"""
        agent_memories = self.memories.get(agent_name, [])
        
        # Filter by type if specified
        if memory_type:
            agent_memories = [
                m for m in agent_memories 
                if m.get('type') == memory_type
            ]
        
        # Return most recent
        return agent_memories[-limit:]
    
    async def search(
        self,
        agent_name: str,
        query: Dict[str, Any],
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Search memories by criteria"""
        agent_memories = self.memories.get(agent_name, [])
        results = []
        
        for memory in agent_memories:
            match = True
            for key, value in query.items():
                if key not in memory or memory[key] != value:
                    match = False
                    break
            
            if match:
                results.append(memory)
                
            if len(results) >= limit:
                break
        
        return results
    
    async def clear(self, agent_name: Optional[str] = None) -> None:
        """Clear memories"""
        if agent_name:
            self.memories[agent_name] = []
        else:
            self.memories.clear()
            
        if self.persistence_path:
            self.save()
    
    def save(self) -> None:
        """Save memories to disk"""
        if not self.persistence_path:
            return
            
        try:
            self.persistence_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Convert to serializable format
            data = {
                agent: memories
                for agent, memories in self.memories.items()
            }
            
            with open(self.persistence_path, 'w') as f:
                json.dump(data, f, indent=2, default=str)
                
            self.logger.info(f"Saved memories to {self.persistence_path}")
            
        except Exception as e:
            self.logger.error(f"Failed to save memories: {e}")
    
    def load(self) -> None:
        """Load memories from disk"""
        if not self.persistence_path or not self.persistence_path.exists():
            return
            
        try:
            with open(self.persistence_path, 'r') as f:
                data = json.load(f)
                
            self.memories = defaultdict(list, data)
            self.logger.info(f"Loaded memories from {self.persistence_path}")
            
        except Exception as e:
            self.logger.error(f"Failed to load memories: {e}")
            self.memories = defaultdict(list)
    
    def get_agent_memory(self, agent_name: str) -> 'AgentMemory':
        """Get or create an AgentMemory instance for an agent"""
        from .agent_memory import AgentMemory
        return AgentMemory(agent_name, self)
    
    async def get_recent_performance(self, symbol: str) -> Dict[str, float]:
        """Get recent performance metrics for a symbol
        
        Returns performance metrics based on recent memories related to the symbol.
        """
        # Search for recent trades and outcomes for this symbol
        performance_metrics = {
            'win_rate': 0.0,
            'avg_return': 0.0,
            'recent_pnl': 0.0,
            'trade_count': 0,
            'success_rate': 0.0
        }
        
        # Get recent memories from engine about this symbol
        engine_memories = await self.get_recent('engine', limit=50)
        
        # Filter for position closed events for this symbol
        closed_positions = []
        for memory in engine_memories:
            if (memory.get('type') == 'position_closed' and 
                memory.get('outcome', {}).get('position', {}).get('symbol') == symbol):
                closed_positions.append(memory['outcome'])
        
        if not closed_positions:
            return performance_metrics
        
        # Calculate metrics from closed positions
        total_trades = len(closed_positions)
        winning_trades = sum(1 for p in closed_positions if p.get('pnl', 0) > 0)
        total_pnl = sum(p.get('pnl', 0) for p in closed_positions)
        total_return_pct = sum(p.get('return_pct', 0) for p in closed_positions)
        
        performance_metrics.update({
            'win_rate': winning_trades / total_trades if total_trades > 0 else 0.0,
            'avg_return': total_return_pct / total_trades if total_trades > 0 else 0.0,
            'recent_pnl': total_pnl,
            'trade_count': total_trades,
            'success_rate': winning_trades / total_trades if total_trades > 0 else 0.0
        })
        
        return performance_metrics
    
    async def store_decision(self, decision: Any, context: Any) -> None:
        """Store a trading decision with its context
        
        Args:
            decision: TradingDecision object
            context: DecisionContext object
        """
        memory = {
            'type': 'trading_decision',
            'symbol': decision.symbol,
            'action': decision.action.value,
            'confidence': decision.confidence,
            'reasoning': decision.reasoning,
            'context': {
                'timestamp': context.timestamp.isoformat() if hasattr(context.timestamp, 'isoformat') else str(context.timestamp),
                'portfolio_value': context.portfolio_state.total_value,
                'risk_metrics': context.risk_metrics,
                'recent_performance': context.recent_performance
            }
        }
        
        await self.add('decision_store', memory)
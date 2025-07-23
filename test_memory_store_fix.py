"""Quick test to verify MemoryStore fix"""

import asyncio
from backtest2.memory import MemoryStore, AgentMemory


async def test_memory_store_fix():
    """Test that get_agent_memory method works correctly"""
    print("Testing MemoryStore.get_agent_memory() fix...")
    
    # Create memory store
    memory_store = MemoryStore()
    
    # Test get_agent_memory method
    agent_memory = memory_store.get_agent_memory("test_agent")
    
    assert isinstance(agent_memory, AgentMemory)
    assert agent_memory.agent_name == "test_agent"
    assert agent_memory.memory_store == memory_store
    
    print("✅ get_agent_memory() method working correctly")
    
    # Test adding and retrieving memories
    await agent_memory.add_memory({"test": "data"})
    memories = await agent_memory.get_recent_memories()
    
    assert len(memories) == 1
    assert memories[0]["test"] == "data"
    
    print("✅ Memory storage and retrieval working correctly")
    
    print("\n✅ All tests passed! MemoryStore fix is working.")


if __name__ == "__main__":
    asyncio.run(test_memory_store_fix())
"""Memory management utilities to prevent memory leaks"""

from collections import deque
from typing import Any, Deque, Dict, Optional
import logging

logger = logging.getLogger(__name__)


class CircularBuffer:
    """A circular buffer with a fixed maximum size"""
    
    def __init__(self, max_size: int = 10000):
        """
        Initialize circular buffer
        
        Args:
            max_size: Maximum number of items to store
        """
        if max_size <= 0:
            raise ValueError(f"max_size must be positive, got {max_size}")
        self.max_size = max_size
        self.buffer: Deque[Any] = deque(maxlen=max_size)
        
    def append(self, item: Any) -> None:
        """Add item to buffer, removing oldest if at capacity"""
        self.buffer.append(item)
        
    def get_all(self) -> list:
        """Get all items in buffer"""
        return list(self.buffer)
        
    def get_last(self, n: int) -> list:
        """Get last n items from buffer"""
        if n == 0:
            return []
        return list(self.buffer)[-n:] if n <= len(self.buffer) else list(self.buffer)
        
    def clear(self) -> None:
        """Clear all items from buffer"""
        self.buffer.clear()
        
    def __len__(self) -> int:
        return len(self.buffer)


class MemoryLimitedDict:
    """Dictionary with limited history per key"""
    
    def __init__(self, max_items_per_key: int = 1000):
        """
        Initialize memory limited dictionary
        
        Args:
            max_items_per_key: Maximum items to store per key
        """
        self.max_items = max_items_per_key
        self.data: Dict[str, Deque[Any]] = {}
        
    def add(self, key: str, value: Any) -> None:
        """Add value to key's history"""
        if key not in self.data:
            self.data[key] = deque(maxlen=self.max_items)
        self.data[key].append(value)
        
    def get(self, key: str) -> Optional[Deque[Any]]:
        """Get all values for a key"""
        return self.data.get(key)
        
    def get_latest(self, key: str) -> Optional[Any]:
        """Get most recent value for a key"""
        if key in self.data and self.data[key]:
            return self.data[key][-1]
        return None
        
    def clear(self, key: Optional[str] = None) -> None:
        """Clear data for specific key or all keys"""
        if key:
            if key in self.data:
                self.data[key].clear()
        else:
            self.data.clear()
            
    def get_memory_usage(self) -> Dict[str, int]:
        """Get memory usage statistics"""
        return {key: len(values) for key, values in self.data.items()}
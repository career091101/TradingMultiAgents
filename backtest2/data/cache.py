"""Cache management for data"""

import json
import os
import pickle
from datetime import datetime, timedelta
from typing import Any, Optional
import logging
import aiofiles
import asyncio


class CacheManager:
    """Manages caching of market data"""
    
    def __init__(self, enabled: bool = True, ttl: int = 86400, cache_dir: str = "./cache"):
        self.enabled = enabled
        self.ttl = ttl  # Time to live in seconds
        self.cache_dir = cache_dir
        self.logger = logging.getLogger(__name__)
        
        # Create cache directory if needed
        if self.enabled:
            os.makedirs(self.cache_dir, exist_ok=True)
            
    async def initialize(self):
        """Initialize cache manager"""
        if self.enabled:
            self.logger.info(f"Cache initialized at {self.cache_dir}")
            
    async def get(self, key: str) -> Optional[Any]:
        """Get item from cache"""
        if not self.enabled:
            return None
            
        file_path = self._get_file_path(key)
        
        if not os.path.exists(file_path):
            return None
            
        # Check if cache is expired
        file_age = datetime.now() - datetime.fromtimestamp(os.path.getmtime(file_path))
        if file_age.total_seconds() > self.ttl:
            self.logger.debug(f"Cache expired for {key}")
            return None
            
        try:
            # Read cache file
            async with aiofiles.open(file_path, 'rb') as f:
                data = await f.read()
                return pickle.loads(data)
        except Exception as e:
            self.logger.error(f"Error reading cache {key}: {e}")
            return None
            
    async def set(self, key: str, value: Any) -> None:
        """Set item in cache"""
        if not self.enabled:
            return
            
        file_path = self._get_file_path(key)
        
        try:
            # Write cache file
            async with aiofiles.open(file_path, 'wb') as f:
                await f.write(pickle.dumps(value))
            self.logger.debug(f"Cached {key}")
        except Exception as e:
            self.logger.error(f"Error writing cache {key}: {e}")
            
    async def clear(self) -> None:
        """Clear all cache"""
        if not self.enabled:
            return
            
        try:
            for filename in os.listdir(self.cache_dir):
                file_path = os.path.join(self.cache_dir, filename)
                if os.path.isfile(file_path):
                    os.remove(file_path)
            self.logger.info("Cache cleared")
        except Exception as e:
            self.logger.error(f"Error clearing cache: {e}")
            
    async def close(self) -> None:
        """Close cache manager"""
        # Nothing to close for file-based cache
        pass
        
    def _get_file_path(self, key: str) -> str:
        """Get file path for cache key"""
        # Replace invalid characters
        safe_key = key.replace('/', '_').replace('\\', '_')
        return os.path.join(self.cache_dir, f"{safe_key}.pkl")
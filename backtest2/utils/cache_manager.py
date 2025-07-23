"""Cache management for LLM results and market data"""

import asyncio
import hashlib
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Any, Dict, Optional, Callable, Union
from dataclasses import dataclass, field
from enum import Enum


logger = logging.getLogger(__name__)


class CacheType(Enum):
    """Types of cache entries"""
    LLM_RESULT = "llm_result"
    MARKET_DATA = "market_data"
    ANALYSIS_RESULT = "analysis_result"
    DECISION = "decision"


@dataclass
class CacheEntry:
    """Single cache entry"""
    key: str
    value: Any
    cache_type: CacheType
    timestamp: datetime
    ttl: timedelta
    access_count: int = 0
    last_accessed: datetime = field(default_factory=datetime.now)
    
    def is_expired(self) -> bool:
        """Check if cache entry has expired"""
        return datetime.now() > self.timestamp + self.ttl
        
    def access(self) -> Any:
        """Access the cache entry and update stats"""
        self.access_count += 1
        self.last_accessed = datetime.now()
        return self.value


class CacheStats:
    """Cache statistics"""
    def __init__(self):
        self.hits = 0
        self.misses = 0
        self.evictions = 0
        self.expirations = 0
        
    @property
    def hit_rate(self) -> float:
        """Calculate cache hit rate"""
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "hits": self.hits,
            "misses": self.misses,
            "evictions": self.evictions,
            "expirations": self.expirations,
            "hit_rate": self.hit_rate
        }


class CacheManager:
    """Manages caching for various data types"""
    
    def __init__(
        self,
        max_entries: int = 10000,
        default_ttl: timedelta = timedelta(minutes=30),
        cleanup_interval: timedelta = timedelta(minutes=5)
    ):
        self.max_entries = max_entries
        self.default_ttl = default_ttl
        self.cleanup_interval = cleanup_interval
        
        self.cache: Dict[str, CacheEntry] = {}
        self.stats = CacheStats()
        self.logger = logging.getLogger(__name__)
        
        # TTL overrides by cache type
        self.ttl_overrides = {
            CacheType.LLM_RESULT: timedelta(hours=1),
            CacheType.MARKET_DATA: timedelta(minutes=5),
            CacheType.ANALYSIS_RESULT: timedelta(minutes=30),
            CacheType.DECISION: timedelta(hours=2)
        }
        
        # Start cleanup task
        self._cleanup_task = None
        self._lock = asyncio.Lock()
        
    async def start(self) -> None:
        """Start the cache cleanup task"""
        if self._cleanup_task is None:
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())
            
    async def stop(self) -> None:
        """Stop the cache cleanup task"""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
            self._cleanup_task = None
            
    async def _cleanup_loop(self) -> None:
        """Periodically clean up expired entries"""
        while True:
            try:
                await asyncio.sleep(self.cleanup_interval.total_seconds())
                await self._cleanup_expired()
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in cache cleanup: {e}")
                
    async def _cleanup_expired(self) -> None:
        """Remove expired entries"""
        async with self._lock:
            expired_keys = [
                key for key, entry in self.cache.items()
                if entry.is_expired()
            ]
            
            for key in expired_keys:
                del self.cache[key]
                self.stats.expirations += 1
                
            if expired_keys:
                self.logger.info(f"Cleaned up {len(expired_keys)} expired cache entries")
                
    def _generate_key(
        self,
        cache_type: CacheType,
        identifier: str,
        params: Optional[Dict[str, Any]] = None
    ) -> str:
        """Generate a cache key"""
        key_parts = [cache_type.value, identifier]
        
        if params:
            # Sort params for consistent key generation
            sorted_params = json.dumps(params, sort_keys=True)
            param_hash = hashlib.md5(sorted_params.encode()).hexdigest()[:8]
            key_parts.append(param_hash)
            
        return ":".join(key_parts)
        
    async def get(
        self,
        cache_type: CacheType,
        identifier: str,
        params: Optional[Dict[str, Any]] = None
    ) -> Optional[Any]:
        """Get value from cache"""
        key = self._generate_key(cache_type, identifier, params)
        
        async with self._lock:
            entry = self.cache.get(key)
            
            if entry is None:
                self.stats.misses += 1
                return None
                
            if entry.is_expired():
                del self.cache[key]
                self.stats.expirations += 1
                self.stats.misses += 1
                return None
                
            self.stats.hits += 1
            return entry.access()
            
    async def set(
        self,
        cache_type: CacheType,
        identifier: str,
        value: Any,
        params: Optional[Dict[str, Any]] = None,
        ttl: Optional[timedelta] = None
    ) -> None:
        """Set value in cache"""
        key = self._generate_key(cache_type, identifier, params)
        
        if ttl is None:
            ttl = self.ttl_overrides.get(cache_type, self.default_ttl)
            
        async with self._lock:
            # Check if we need to evict entries
            if len(self.cache) >= self.max_entries:
                await self._evict_lru()
                
            entry = CacheEntry(
                key=key,
                value=value,
                cache_type=cache_type,
                timestamp=datetime.now(),
                ttl=ttl
            )
            
            self.cache[key] = entry
            
    async def _evict_lru(self) -> None:
        """Evict least recently used entry"""
        if not self.cache:
            return
            
        # Find LRU entry
        lru_key = min(
            self.cache.keys(),
            key=lambda k: self.cache[k].last_accessed
        )
        
        del self.cache[lru_key]
        self.stats.evictions += 1
        
    async def get_or_compute(
        self,
        cache_type: CacheType,
        identifier: str,
        compute_func: Callable,
        params: Optional[Dict[str, Any]] = None,
        ttl: Optional[timedelta] = None
    ) -> Any:
        """Get from cache or compute if missing"""
        # Try to get from cache
        cached_value = await self.get(cache_type, identifier, params)
        if cached_value is not None:
            return cached_value
            
        # Compute value
        if asyncio.iscoroutinefunction(compute_func):
            value = await compute_func()
        else:
            value = compute_func()
            
        # Cache the result
        await self.set(cache_type, identifier, value, params, ttl)
        
        return value
        
    async def invalidate(
        self,
        cache_type: Optional[CacheType] = None,
        identifier: Optional[str] = None
    ) -> int:
        """Invalidate cache entries"""
        async with self._lock:
            invalidated = 0
            
            if cache_type is None and identifier is None:
                # Clear all
                invalidated = len(self.cache)
                self.cache.clear()
            else:
                # Selective invalidation
                keys_to_remove = []
                
                for key, entry in self.cache.items():
                    if cache_type and entry.cache_type != cache_type:
                        continue
                    if identifier and identifier not in key:
                        continue
                    keys_to_remove.append(key)
                    
                for key in keys_to_remove:
                    del self.cache[key]
                    invalidated += 1
                    
            return invalidated
            
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        stats = self.stats.to_dict()
        stats.update({
            "entries": len(self.cache),
            "max_entries": self.max_entries,
            "memory_usage_mb": self._estimate_memory_usage() / 1024 / 1024
        })
        
        # Stats by cache type
        type_stats = {}
        for cache_type in CacheType:
            entries = [e for e in self.cache.values() if e.cache_type == cache_type]
            type_stats[cache_type.value] = {
                "count": len(entries),
                "avg_access_count": sum(e.access_count for e in entries) / len(entries)
                                   if entries else 0
            }
        stats["by_type"] = type_stats
        
        return stats
        
    def _estimate_memory_usage(self) -> int:
        """Estimate memory usage in bytes"""
        # Rough estimation
        import sys
        total = 0
        for entry in self.cache.values():
            total += sys.getsizeof(entry.key)
            total += sys.getsizeof(entry.value)
            total += 200  # Overhead for CacheEntry object
        return total


class LLMCacheManager(CacheManager):
    """Specialized cache manager for LLM results"""
    
    def __init__(self):
        super().__init__(
            max_entries=5000,
            default_ttl=timedelta(hours=1)
        )
        
    async def cache_llm_result(
        self,
        agent_name: str,
        prompt: str,
        context: Dict[str, Any],
        result: str,
        use_deep_thinking: bool = False
    ) -> None:
        """Cache an LLM result"""
        params = {
            "prompt_hash": hashlib.md5(prompt.encode()).hexdigest()[:16],
            "context_hash": hashlib.md5(
                json.dumps(context, sort_keys=True).encode()
            ).hexdigest()[:16],
            "deep_thinking": use_deep_thinking
        }
        
        await self.set(
            CacheType.LLM_RESULT,
            agent_name,
            result,
            params
        )
        
    async def get_llm_result(
        self,
        agent_name: str,
        prompt: str,
        context: Dict[str, Any],
        use_deep_thinking: bool = False
    ) -> Optional[str]:
        """Get cached LLM result"""
        params = {
            "prompt_hash": hashlib.md5(prompt.encode()).hexdigest()[:16],
            "context_hash": hashlib.md5(
                json.dumps(context, sort_keys=True).encode()
            ).hexdigest()[:16],
            "deep_thinking": use_deep_thinking
        }
        
        return await self.get(
            CacheType.LLM_RESULT,
            agent_name,
            params
        )
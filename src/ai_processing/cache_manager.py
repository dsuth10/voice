"""
Cache Manager for AI Text Enhancement

This module provides caching functionality and token usage tracking
for the AI text enhancement system.
"""

import json
import time
import hashlib
from typing import Dict, Optional, Any, List
from dataclasses import dataclass, asdict
from pathlib import Path
import os

from ..utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class CacheEntry:
    """Represents a cached enhancement result."""
    key: str
    original_text: str
    enhanced_text: str
    model_used: str
    tokens_used: int
    processing_time: float
    context: Optional[str] = None
    custom_instructions: Optional[str] = None
    template_name: Optional[str] = None
    timestamp: float = None
    
    def __post_init__(self):
        """Set timestamp if not provided."""
        if self.timestamp is None:
            self.timestamp = time.time()


@dataclass
class TokenUsage:
    """Represents token usage statistics."""
    model: str
    total_tokens: int
    total_requests: int
    average_tokens_per_request: float
    last_used: float
    
    def __post_init__(self):
        """Calculate average tokens per request."""
        if self.total_requests > 0:
            self.average_tokens_per_request = self.total_tokens / self.total_requests
        else:
            self.average_tokens_per_request = 0.0


class CacheManager:
    """
    Manages caching for AI text enhancement results and token usage tracking.
    """
    
    def __init__(self, cache_dir: Optional[str] = None, max_cache_size: int = 1000):
        """
        Initialize the cache manager.
        
        Args:
            cache_dir: Directory to store cache files (optional)
            max_cache_size: Maximum number of cache entries to keep in memory
        """
        self.cache_dir = cache_dir or ".cache"
        self.max_cache_size = max_cache_size
        self.cache: Dict[str, CacheEntry] = {}
        self.token_usage: Dict[str, TokenUsage] = {}
        self.cache_stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0
        }
        
        self._load_cache()
        self._load_token_usage()
    
    def _load_cache(self):
        """Load cache from disk if available."""
        cache_file = Path(self.cache_dir) / "enhancement_cache.json"
        if cache_file.exists():
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    cache_data = json.load(f)
                    for entry_data in cache_data.values():
                        entry = CacheEntry(**entry_data)
                        self.cache[entry.key] = entry
                logger.info(f"Loaded {len(self.cache)} cache entries from disk")
            except Exception as e:
                logger.error(f"Failed to load cache: {e}")
    
    def _save_cache(self):
        """Save cache to disk."""
        os.makedirs(self.cache_dir, exist_ok=True)
        cache_file = Path(self.cache_dir) / "enhancement_cache.json"
        
        try:
            cache_data = {key: asdict(entry) for key, entry in self.cache.items()}
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to save cache: {e}")
    
    def _load_token_usage(self):
        """Load token usage statistics from disk."""
        usage_file = Path(self.cache_dir) / "token_usage.json"
        if usage_file.exists():
            try:
                with open(usage_file, 'r', encoding='utf-8') as f:
                    usage_data = json.load(f)
                    for model, data in usage_data.items():
                        self.token_usage[model] = TokenUsage(**data)
                logger.info(f"Loaded token usage for {len(self.token_usage)} models")
            except Exception as e:
                logger.error(f"Failed to load token usage: {e}")
    
    def _save_token_usage(self):
        """Save token usage statistics to disk."""
        os.makedirs(self.cache_dir, exist_ok=True)
        usage_file = Path(self.cache_dir) / "token_usage.json"
        
        try:
            usage_data = {model: asdict(usage) for model, usage in self.token_usage.items()}
            with open(usage_file, 'w', encoding='utf-8') as f:
                json.dump(usage_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to save token usage: {e}")
    
    def generate_cache_key(self, text: str, context: Optional[str] = None,
                          custom_instructions: Optional[str] = None,
                          template_name: Optional[str] = None) -> str:
        """
        Generate a cache key for the given parameters.
        
        Args:
            text: Input text
            context: Optional context
            custom_instructions: Optional custom instructions
            template_name: Optional template name
            
        Returns:
            Cache key string
        """
        content = f"{text}:{context}:{custom_instructions}:{template_name}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def get(self, key: str) -> Optional[CacheEntry]:
        """
        Get a cache entry by key.
        
        Args:
            key: Cache key
            
        Returns:
            CacheEntry if found, None otherwise
        """
        if key in self.cache:
            self.cache_stats["hits"] += 1
            logger.debug(f"Cache hit for key: {key}")
            return self.cache[key]
        else:
            self.cache_stats["misses"] += 1
            logger.debug(f"Cache miss for key: {key}")
            return None
    
    def put(self, entry: CacheEntry):
        """
        Store a cache entry.
        
        Args:
            entry: CacheEntry to store
        """
        # Check if cache is full
        if len(self.cache) >= self.max_cache_size:
            self._evict_oldest()
        
        self.cache[entry.key] = entry
        self._save_cache()
        logger.debug(f"Cached result for key: {entry.key}")
    
    def _evict_oldest(self):
        """Evict the oldest cache entry."""
        if not self.cache:
            return
        
        oldest_key = min(self.cache.keys(), 
                        key=lambda k: self.cache[k].timestamp)
        del self.cache[oldest_key]
        self.cache_stats["evictions"] += 1
        logger.debug(f"Evicted oldest cache entry: {oldest_key}")
    
    def update_token_usage(self, model: str, tokens_used: int):
        """
        Update token usage statistics for a model.
        
        Args:
            model: Model name
            tokens_used: Number of tokens used
        """
        if model not in self.token_usage:
            self.token_usage[model] = TokenUsage(
                model=model,
                total_tokens=0,
                total_requests=0,
                average_tokens_per_request=0.0,
                last_used=time.time()
            )
        
        usage = self.token_usage[model]
        usage.total_tokens += tokens_used
        usage.total_requests += 1
        usage.last_used = time.time()
        
        self._save_token_usage()
        logger.debug(f"Updated token usage for {model}: {tokens_used} tokens")
    
    def get_token_usage(self, model: Optional[str] = None) -> Dict[str, Any]:
        """
        Get token usage statistics.
        
        Args:
            model: Optional model name to filter by
            
        Returns:
            Token usage statistics
        """
        if model:
            usage = self.token_usage.get(model)
            if usage:
                return asdict(usage)
            return {}
        
        return {model: asdict(usage) for model, usage in self.token_usage.items()}
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Cache statistics dictionary
        """
        total_requests = self.cache_stats["hits"] + self.cache_stats["misses"]
        hit_rate = (self.cache_stats["hits"] / total_requests * 100) if total_requests > 0 else 0
        
        return {
            "cache_size": len(self.cache),
            "max_cache_size": self.max_cache_size,
            "hits": self.cache_stats["hits"],
            "misses": self.cache_stats["misses"],
            "evictions": self.cache_stats["evictions"],
            "hit_rate_percent": round(hit_rate, 2),
            "total_requests": total_requests
        }
    
    def clear_cache(self):
        """Clear all cache entries."""
        self.cache.clear()
        self.cache_stats = {"hits": 0, "misses": 0, "evictions": 0}
        self._save_cache()
        logger.info("Cache cleared")
    
    def clear_token_usage(self):
        """Clear token usage statistics."""
        self.token_usage.clear()
        self._save_token_usage()
        logger.info("Token usage statistics cleared")
    
    def get_cache_entries(self, limit: Optional[int] = None) -> List[CacheEntry]:
        """
        Get cache entries, optionally limited by count.
        
        Args:
            limit: Maximum number of entries to return
            
        Returns:
            List of cache entries
        """
        entries = list(self.cache.values())
        entries.sort(key=lambda e: e.timestamp, reverse=True)
        
        if limit:
            entries = entries[:limit]
        
        return entries
    
    def estimate_cost(self, model: str, tokens_used: int) -> float:
        """
        Estimate the cost for token usage (approximate).
        
        Args:
            model: Model name
            tokens_used: Number of tokens used
            
        Returns:
            Estimated cost in USD
        """
        # Approximate costs per 1K tokens (as of 2025)
        cost_per_1k = {
            "gpt-4o-mini": 0.15,
            "gpt-4o": 0.50,
            "gpt-3.5-turbo": 0.002,
            "gpt-4-turbo": 0.30
        }
        
        cost_per_token = cost_per_1k.get(model, 0.15) / 1000
        return tokens_used * cost_per_token
    
    def get_total_cost(self, model: Optional[str] = None) -> float:
        """
        Get total estimated cost for token usage.
        
        Args:
            model: Optional model name to filter by
            
        Returns:
            Total estimated cost in USD
        """
        total_cost = 0.0
        
        if model:
            usage = self.token_usage.get(model)
            if usage:
                total_cost = self.estimate_cost(model, usage.total_tokens)
        else:
            for model_name, usage in self.token_usage.items():
                total_cost += self.estimate_cost(model_name, usage.total_tokens)
        
        return total_cost 
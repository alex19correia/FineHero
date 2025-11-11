"""
Redis Caching Implementation for FineHero Phase 3.
Simple and effective caching for legal documents and frequently accessed data.
"""
import os
import json
import logging
import pickle
from typing import Any, Optional, Dict, List
from datetime import datetime, timedelta
import redis
from functools import wraps

logger = logging.getLogger(__name__)

class RedisCache:
    """
    Simple Redis caching implementation for FineHero.
    Caches legal documents, fines data, and API responses.
    """
    
    def __init__(self):
        self.redis_host = os.getenv("REDIS_HOST", "localhost")
        self.redis_port = int(os.getenv("REDIS_PORT", "6379"))
        self.redis_password = os.getenv("REDIS_PASSWORD", "")
        self.redis_db = int(os.getenv("REDIS_DB", "0"))
        self.redis_url = os.getenv("REDIS_URL", "")
        
        # Cache configuration
        self.default_ttl = int(os.getenv("CACHE_DEFAULT_TTL", "3600"))  # 1 hour
        self.document_cache_ttl = int(os.getenv("DOCUMENT_CACHE_TTL", "7200"))  # 2 hours
        self.fines_cache_ttl = int(os.getenv("FINES_CACHE_TTL", "1800"))  # 30 minutes
        
        self._client = None
        self._connect()
    
    def _connect(self):
        """Connect to Redis."""
        try:
            if self.redis_url:
                # Use URL for cloud Redis services
                self._client = redis.from_url(
                    self.redis_url,
                    encoding='utf-8',
                    decode_responses=True
                )
            else:
                # Use individual connection parameters
                self._client = redis.Redis(
                    host=self.redis_host,
                    port=self.redis_port,
                    password=self.redis_password if self.redis_password else None,
                    db=self.redis_db,
                    decode_responses=True,
                    socket_connect_timeout=5,
                    socket_timeout=5
                )
            
            # Test connection
            self._client.ping()
            logger.info("Redis connection established successfully")
            
        except redis.ConnectionError:
            logger.warning("Redis connection failed - caching disabled")
            self._client = None
        except Exception as e:
            logger.error(f"Redis connection error: {e}")
            self._client = None
    
    def is_connected(self) -> bool:
        """Check if Redis is connected."""
        if not self._client:
            return False
        
        try:
            self._client.ping()
            return True
        except:
            return False
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        if not self.is_connected():
            return None
        
        try:
            value = self._client.get(key)
            if value is None:
                return None
            
            # Try to deserialize as JSON first, then pickle
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                try:
                    return pickle.loads(value.encode('latin-1'))
                except:
                    return value
                    
        except Exception as e:
            logger.error(f"Cache get error for key {key}: {e}")
            return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache."""
        if not self.is_connected():
            return False
        
        try:
            # Serialize value
            if isinstance(value, (dict, list)):
                serialized_value = json.dumps(value, default=str)
            else:
                serialized_value = pickle.dumps(value)
            
            # Set with TTL
            if ttl:
                result = self._client.setex(key, ttl, serialized_value)
            else:
                result = self._client.set(key, serialized_value)
            
            return result
            
        except Exception as e:
            logger.error(f"Cache set error for key {key}: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """Delete value from cache."""
        if not self.is_connected():
            return False
        
        try:
            return bool(self._client.delete(key))
        except Exception as e:
            logger.error(f"Cache delete error for key {key}: {e}")
            return False
    
    def delete_pattern(self, pattern: str) -> int:
        """Delete all keys matching pattern."""
        if not self.is_connected():
            return 0
        
        try:
            keys = self._client.keys(pattern)
            if keys:
                return self._client.delete(*keys)
            return 0
        except Exception as e:
            logger.error(f"Cache pattern delete error for pattern {pattern}: {e}")
            return 0
    
    def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        if not self.is_connected():
            return False
        
        try:
            return bool(self._client.exists(key))
        except Exception as e:
            logger.error(f"Cache exists error for key {key}: {e}")
            return False
    
    def clear_all(self) -> bool:
        """Clear all cache data."""
        if not self.is_connected():
            return False
        
        try:
            return bool(self._client.flushdb())
        except Exception as e:
            logger.error(f"Cache clear error: {e}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        if not self.is_connected():
            return {"status": "disconnected"}
        
        try:
            info = self._client.info()
            return {
                "status": "connected",
                "connected_clients": info.get('connected_clients', 0),
                "used_memory": info.get('used_memory_human', '0B'),
                "total_commands_processed": info.get('total_commands_processed', 0),
                "keyspace_hits": info.get('keyspace_hits', 0),
                "keyspace_misses": info.get('keyspace_misses', 0),
                "hit_rate": self._calculate_hit_rate(info)
            }
        except Exception as e:
            logger.error(f"Cache stats error: {e}")
            return {"status": "error", "error": str(e)}
    
    def _calculate_hit_rate(self, info: Dict) -> float:
        """Calculate cache hit rate."""
        hits = info.get('keyspace_hits', 0)
        misses = info.get('keyspace_misses', 0)
        total = hits + misses
        
        if total == 0:
            return 0.0
        
        return round((hits / total) * 100, 2)

# Cache key generators
class CacheKeys:
    """Generate consistent cache keys."""
    
    @staticmethod
    def legal_document(doc_id: str) -> str:
        return f"legal_doc:{doc_id}"
    
    @staticmethod
    def legal_documents_list(page: int = 1, per_page: int = 20) -> str:
        return f"legal_docs:list:{page}:{per_page}"
    
    @staticmethod
    def fine(fine_id: str) -> str:
        return f"fine:{fine_id}"
    
    @staticmethod
    def fines_list(page: int = 1, per_page: int = 20) -> str:
        return f"fines:list:{page}:{per_page}"
    
    @staticmethod
    def defense(defense_id: str) -> str:
        return f"defense:{defense_id}"
    
    @staticmethod
    def user_fines(user_hash: str, page: int = 1) -> str:
        return f"user:{user_hash}:fines:{page}"
    
    @staticmethod
    def search_results(query_hash: str) -> str:
        return f"search:{query_hash}"
    
    @staticmethod
    def knowledge_base_articles() -> str:
        return "kb:articles"
    
    @staticmethod
    def api_response(endpoint: str, params_hash: str) -> str:
        return f"api:{endpoint}:{params_hash}"

# Global cache instance
cache = RedisCache()

# Cache decorator for functions
def cached(ttl: int = None, key_func=None):
    """
    Decorator to cache function results.
    
    Args:
        ttl: Time to live in seconds
        key_func: Function to generate cache key from function args
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                # Default key generation
                key_parts = [func.__name__]
                key_parts.extend([str(arg) for arg in args])
                if kwargs:
                    sorted_kwargs = sorted(kwargs.items())
                    key_parts.extend([f"{k}={v}" for k, v in sorted_kwargs])
                cache_key = ":".join(key_parts)
            
            # Try to get from cache
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                logger.debug(f"Cache hit for {cache_key}")
                return cached_result
            
            # Execute function and cache result
            try:
                result = func(*args, **kwargs)
                if result is not None:
                    cache.set(cache_key, result, ttl)
                    logger.debug(f"Cached result for {cache_key}")
                return result
            except Exception as e:
                logger.error(f"Function {func.__name__} failed: {e}")
                raise
        
        return wrapper
    return decorator

# Cache management functions for specific entities
class FineHeroCache:
    """
    Specialized cache management for FineHero entities.
    """
    
    @staticmethod
    def cache_legal_document(document_data: Dict[str, Any], doc_id: str) -> bool:
        """Cache legal document data."""
        key = CacheKeys.legal_document(doc_id)
        return cache.set(key, document_data, cache.document_cache_ttl)
    
    @staticmethod
    def get_legal_document(doc_id: str) -> Optional[Dict[str, Any]]:
        """Get cached legal document."""
        key = CacheKeys.legal_document(doc_id)
        return cache.get(key)
    
    @staticmethod
    def cache_fine_data(fine_data: Dict[str, Any], fine_id: str) -> bool:
        """Cache fine data."""
        key = CacheKeys.fine(fine_id)
        return cache.set(key, fine_data, cache.fines_cache_ttl)
    
    @staticmethod
    def get_fine_data(fine_id: str) -> Optional[Dict[str, Any]]:
        """Get cached fine data."""
        key = CacheKeys.fine(fine_id)
        return cache.get(key)
    
    @staticmethod
    def invalidate_user_fines(user_hash: str) -> int:
        """Invalidate all cached fines for a user."""
        pattern = f"user:{user_hash}:*"
        return cache.delete_pattern(pattern)
    
    @staticmethod
    def invalidate_legal_document(doc_id: str) -> bool:
        """Invalidate specific legal document cache."""
        key = CacheKeys.legal_document(doc_id)
        return cache.delete(key)
    
    @staticmethod
    def invalidate_legal_documents() -> int:
        """Invalidate all legal documents cache."""
        pattern = "legal_doc:*"
        return cache.delete_pattern(pattern)
    
    @staticmethod
    def invalidate_fines() -> int:
        """Invalidate all fines cache."""
        pattern = "fines:*"
        return cache.delete_pattern(pattern)
    
    @staticmethod
    def warm_cache_legal_documents(documents: List[Dict[str, Any]]) -> int:
        """Pre-warm cache with legal documents."""
        if not documents:
            return 0
        
        count = 0
        for doc in documents:
            if 'id' in doc:
                if FineHeroCache.cache_legal_document(doc, str(doc['id'])):
                    count += 1
        
        logger.info(f"Warmed cache with {count} legal documents")
        return count
    
    @staticmethod
    def get_cache_status() -> Dict[str, Any]:
        """Get comprehensive cache status."""
        stats = cache.get_stats()
        
        # Add cache patterns information
        patterns = {
            "legal_documents": cache.delete_pattern("legal_doc:*"),
            "fines": cache.delete_pattern("fines:*"),
            "user_data": cache.delete_pattern("user:*"),
            "search_results": cache.delete_pattern("search:*")
        }
        
        return {
            "redis_connection": stats,
            "cache_patterns": patterns,
            "default_ttl": cache.default_ttl,
            "document_ttl": cache.document_cache_ttl,
            "fines_ttl": cache.fines_cache_ttl
        }

# Export for use in other modules
__all__ = [
    "RedisCache",
    "CacheKeys", 
    "FineHeroCache",
    "cached",
    "cache"
]
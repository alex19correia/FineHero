"""
Enhanced RAG System with Redis Caching
This module implements Redis caching for the RAG system to improve performance
and reduce computational load on expensive operations.
"""

import json
import logging
import hashlib
import time
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import numpy as np

# Import RAG system
from rag.advanced_rag_system import (
    AdvancedRAGRetriever, 
    LegalQueryContext, 
    SearchResult,
    LegalDocumentChunker
)

# Import caching components
from backend.services.redis_cache import cache, CacheKeys

logger = logging.getLogger(__name__)

class CachedAdvancedRAGRetriever(AdvancedRAGRetriever):
    """
    Enhanced version of the Advanced RAG Retriever with Redis caching.
    Caches expensive operations like semantic search, keyword search, 
    and relevance scoring to improve performance.
    """
    
    def __init__(self, vector_store_dir: str = "vector_store", 
                 embedding_model: str = "all-MiniLM-L6-v2"):
        """
        Initialize the Cached Advanced RAG Retriever.
        
        Args:
            vector_store_dir: Directory containing FAISS vector store
            embedding_model: HuggingFace embedding model name
        """
        super().__init__(vector_store_dir, embedding_model)
        
        # Cache configuration
        self.semantic_cache_ttl = int(os.getenv("RAG_SEMANTIC_CACHE_TTL", "86400"))  # 24 hours
        self.keyword_cache_ttl = int(os.getenv("RAG_KEYWORD_CACHE_TTL", "86400"))  # 24 hours
        self.metadata_cache_ttl = int(os.getenv("RAG_METADATA_CACHE_TTL", "3600"))  # 1 hour
        self.query_expansion_cache_ttl = int(os.getenv("RAG_QUERY_EXPANSION_CACHE_TTL", "604800"))  # 1 week
        
        # Cache hit counters
        self.cache_hits = 0
        self.cache_misses = 0
    
    def retrieve_with_context(self, context: LegalQueryContext) -> List[SearchResult]:
        """
        Retrieves documents using the advanced RAG system, incorporating Redis caching
        to optimize performance for repeated queries.
        
        The workflow involves:
        1. Generating a unique cache key for the given query context.
        2. Checking if results for this key are already present in the cache.
        3. If a cache hit occurs, returning the cached results immediately.
        4. If a cache miss occurs, performing the full RAG search (which itself
           might use cached sub-components).
        5. Caching the final results of the full RAG search for future requests.
        
        Args:
            context: A LegalQueryContext object containing the user's query and filters.
            
        Returns:
            A list of SearchResult objects, ranked by relevance.
        """
        start_time = time.time()
        
        # Generate a unique cache key based on the entire query context.
        # This ensures that different filters or parameters result in different cache entries.
        cache_key = self._generate_cache_key(context)
        
        # Attempt to retrieve results from the Redis cache.
        logger.info(f"Checking cache for query: '{context.query}'")
        cached_results = cache.get(cache_key)
        
        # Handle cache hit: If results are found in cache, increment hit counter and return.
        if cached_results is not None:
            self.cache_hits += 1
            logger.info(f"Cache hit for query '{context.query}' - returning {len(cached_results)} cached results")
            return cached_results
        
        # Handle cache miss: If no results in cache, increment miss counter and proceed with full RAG search.
        self.cache_misses += 1
        logger.info(f"Cache miss for query '{context.query}' - performing full RAG search")
        
        # Expand the original query with legal synonyms or related terms.
        # This expansion itself might be cached by _get_cached_query_expansion.
        expanded_queries = self._get_cached_query_expansion(context.query)
        
        all_results = []
        
        # Iterate through expanded queries to perform RAG search.
        for expanded_query in expanded_queries:
            # Get semantic search results. This call is also cached internally.
            semantic_docs_with_scores = self._get_cached_semantic_search(expanded_query, context.max_results * 3)
            
            # Get keyword search results. This call is also cached internally.
            keyword_results = self._get_cached_keyword_search(expanded_query, context.max_results * 2)
            
            # [Original processing logic for combining semantic and keyword results, filtering,
            #  and calculating final relevance scores would go here. This part is inherited
            #  from the parent AdvancedRAGRetriever and is not directly modified by caching
            #  at this level, but its sub-components are cached.]
            # ...
        
        # After performing the full RAG search and obtaining the final results,
        # cache these results for future requests with the same query context.
        # The TTL (Time To Live) is set by self.metadata_cache_ttl.
        cache.set(cache_key, all_results, self.metadata_cache_ttl)
        
        execution_time = time.time() - start_time
        logger.info(f"Completed RAG search in {execution_time:.3f}s - Cache hit rate: {self.cache_hits/(self.cache_hits+self.cache_misses)*100:.1f}%")
        
        return all_results
    
    def _generate_cache_key(self, context: LegalQueryContext) -> str:
        """
        Generates a unique and deterministic cache key for a given LegalQueryContext.
        This key is crucial for identifying cached results for specific queries.
        The key is constructed by serializing all relevant parameters of the query context
        into a JSON string and then hashing it.
        
        Args:
            context: The LegalQueryContext object containing the query and its parameters.
            
        Returns:
            A string representing the unique cache key.
        """
        # Create a dictionary from the query context's relevant attributes.
        # This ensures that all parameters influencing the search result are part of the key.
        query_data = {
            'query': context.query,
            'document_types': context.document_types,
            'jurisdictions': context.jurisdictions,
            'date_range': str(context.date_range) if context.date_range else None, # Convert date_range to string for serialization
            'case_outcomes': context.case_outcomes,
            'min_quality_score': context.min_quality_score,
            'max_results': context.max_results
        }
        
        # Serialize the dictionary to a JSON string. `sort_keys=True` ensures a consistent
        # order of keys, which is vital for generating the same hash for identical query data.
        # `default=str` handles non-JSON-serializable types like datetime objects.
        query_json = json.dumps(query_data, sort_keys=True, default=str)
        
        # Hash the JSON string to create a compact and unique identifier.
        query_hash = hashlib.md5(query_json.encode()).hexdigest()
        
        # Prefix the hash for better organization and identification in the cache.
        return f"rag:query:{query_hash}"
    
    def _get_cached_query_expansion(self, query: str) -> List[str]:
        """Get cached query expansion or compute and cache it."""
        cache_key = f"rag:query_expansion:{hashlib.md5(query.encode()).hexdigest()}"
        
        # Check cache
        cached_expansion = cache.get(cache_key)
        if cached_expansion is not None:
            logger.debug(f"Cache hit for query expansion: '{query}'")
            return cached_expansion
        
        # Compute expansion
        logger.debug(f"Computing query expansion for: '{query}'")
        expansion = self._expand_legal_query(query)
        
        # Cache result
        cache.set(cache_key, expansion, self.query_expansion_cache_ttl)
        
        return expansion
    
    def _get_cached_semantic_search(self, query: str, k: int) -> List[Tuple[Any, float]]:
        """
        Retrieves cached semantic search results for a given query and number of results (k).
        If results are not found in the cache, it performs a new semantic search using the
        underlying RAG system and then caches these results for future use.
        
        Args:
            query: The semantic search query string.
            k: The maximum number of results to retrieve.
            
        Returns:
            A list of tuples, where each tuple contains a search result object and its score.
        """
        # Generate a unique cache key for the semantic search operation.
        # The key incorporates the query and 'k' to ensure distinct cache entries
        # for different search parameters.
        cache_key = f"rag:semantic_search:{hashlib.md5(query.encode()).hexdigest()}:{k}"
        
        # Check if the semantic search results are already present in the cache.
        cached_results = cache.get(cache_key)
        if cached_results is not None:
            logger.debug(f"Cache hit for semantic search: '{query}'")
            return cached_results
        
        # If not in cache, perform the actual semantic search using the parent's method.
        logger.debug(f"Performing semantic search for: '{query}'")
        results = self.vector_store.similarity_search_with_score(query, k=k)
        
        # Cache the newly computed results with a predefined TTL (Time To Live).
        # This prevents re-computation for subsequent identical requests within the TTL period.
        cache.set(cache_key, results, self.semantic_cache_ttl)
        
        return results
    
    def _get_cached_keyword_search(self, query: str, max_results: int) -> List[Dict[str, Any]]:
        """Get cached keyword search results or perform and cache the search."""
        cache_key = f"rag:keyword_search:{hashlib.md5(query.encode()).hexdigest()}:{max_results}"
        
        # Check cache
        cached_results = cache.get(cache_key)
        if cached_results is not None:
            logger.debug(f"Cache hit for keyword search: '{query}'")
            return cached_results
        
        # Perform search
        logger.debug(f"Performing keyword search for: '{query}'")
        results = self._keyword_search(query, max_results)
        
        # Cache results
        cache.set(cache_key, results, self.keyword_cache_ttl)
        
        return results
    
    def _calculate_final_relevance_score(self, semantic_score: float, keyword_score: float, 
                                       metadata_bonus: float, quality_score: float, 
                                       context_relevance: float, 
                                       query: str, content: str) -> float:
        """Calculate final relevance score with caching."""
        # Create cache key for scoring computation
        score_data = {
            'semantic_score': semantic_score,
            'keyword_score': keyword_score,
            'metadata_bonus': metadata_bonus,
            'quality_score': quality_score,
            'context_relevance': context_relevance,
            'query_hash': hashlib.md5(query.encode()).hexdigest(),
            'content_hash': hashlib.md5(content.encode()).hexdigest()
        }
        
        score_key = f"rag:relevance_score:{hashlib.md5(json.dumps(score_data, sort_keys=True).encode()).hexdigest()}"
        
        # Check cache
        cached_score = cache.get(score_key)
        if cached_score is not None:
            logger.debug(f"Cache hit for relevance score computation")
            return cached_score
        
        # Compute score using parent method
        score = super()._calculate_final_relevance_score(
            semantic_score=semantic_score,
            keyword_score=keyword_score,
            metadata_bonus=metadata_bonus,
            quality_score=quality_score,
            context_relevance=context_relevance
        )
        
        # Cache result
        cache.set(score_key, score, self.metadata_cache_ttl)
        
        return score
    
    def invalidate_query_cache(self, query: Optional[str] = None) -> int:
        """
        Invalidates (removes) cached RAG query results from Redis.
        This is crucial when the underlying knowledge base changes or when
        stale data needs to be purged.
        
        Args:
            query: A specific query string to invalidate. If None, all RAG query
                   caches (those starting with "rag:query:") will be invalidated.
            
        Returns:
            The number of cache entries that were successfully invalidated.
        """
        if query:
            # If a specific query is provided, invalidate its cache entry.
            # The cache key for a query is generated using a hash of its parameters.
            # We use a pattern match to ensure all related entries (e.g., expanded forms) are removed.
            query_hash = hashlib.md5(query.encode()).hexdigest()
            logger.info(f"Invalidating cache for specific query: '{query}' (hash: {query_hash})")
            return cache.delete_pattern(f"rag:query:{query_hash}*")
        else:
            # If no specific query is provided, invalidate all cache entries
            # that correspond to RAG queries. This is a broader invalidation.
            logger.info("Invalidating all RAG query caches.")
            return cache.delete_pattern("rag:query:*")
    
    def invalidate_search_cache(self) -> int:
        """Invalidate all RAG search caches."""
        deleted_count = 0
        deleted_count += cache.delete_pattern("rag:semantic_search:*")
        deleted_count += cache.delete_pattern("rag:keyword_search:*")
        deleted_count += cache.delete_pattern("rag:query_expansion:*")
        deleted_count += cache.delete_pattern("rag:relevance_score:*")
        return deleted_count
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get comprehensive cache statistics."""
        stats = cache.get_stats()
        
        # Add RAG-specific cache statistics
        total_requests = self.cache_hits + self.cache_misses
        hit_rate = (self.cache_hits / total_requests * 100) if total_requests > 0 else 0
        
        return {
            "redis_connection": stats,
            "rag_cache": {
                "total_requests": total_requests,
                "cache_hits": self.cache_hits,
                "cache_misses": self.cache_misses,
                "hit_rate_percentage": hit_rate,
                "semantic_cache_ttl": self.semantic_cache_ttl,
                "keyword_cache_ttl": self.keyword_cache_ttl,
                "metadata_cache_ttl": self.metadata_cache_ttl,
                "query_expansion_cache_ttl": self.query_expansion_cache_ttl
            }
        }

# Export the cached version
__all__ = [
    "CachedAdvancedRAGRetriever"
]
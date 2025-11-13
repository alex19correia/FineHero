"""
Test cases for the Cached RAG System
Tests Redis caching integration for the Advanced RAG Retriever
"""

import json
import os
import sys
import time
import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime, timedelta

# Add the backend directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Import required modules
from rag.advanced_rag_system import LegalQueryContext, SearchResult
from backend.services.redis_cache import RedisCache, cache
from backend.services.cached_rag_system import CachedAdvancedRAGRetriever


class TestCachedRAGSystem:
    """Test class for the Cached RAG System"""
    
    @pytest.fixture
    def mock_rag_system(self):
        """Create a mock RAG system for testing"""
        # Create a mock retriever
        mock_retriever = Mock(spec=CachedAdvancedRAGRetriever)
        mock_retriever.cache_hits = 0
        mock_retriever.cache_misses = 0
        mock_retriever.semantic_cache_ttl = 86400
        mock_retriever.keyword_cache_ttl = 86400
        mock_retriever.metadata_cache_ttl = 3600
        mock_retriever.query_expansion_cache_ttl = 604800
        
        # Mock the parent methods
        mock_retriever._expand_legal_query = Mock(return_value=["query", "expanded query"])
        mock_retriever.vector_store = Mock()
        mock_retriever.vector_store.similarity_search_with_score = Mock(return_value=[])
        mock_retriever._keyword_search = Mock(return_value=[])
        
        # Mock _calculate_final_relevance_score to return a fixed score
        mock_retriever._calculate_final_relevance_score = Mock(return_value=0.75)
        
        # Create mock SearchResult objects
        mock_search_result = SearchResult(
            content="Sample content",
            document_id=1,
            title="Test Document",
            source="Test Source",
            document_type="law",
            jurisdiction="Portugal",
            publication_date=None,
            relevance_score=0.75,
            semantic_score=0.8,
            keyword_score=0.7,
            metadata_bonus=0.5,
            quality_score=0.8
        )
        
        # Make retrieve_with_context return the mock result
        mock_retriever.retrieve_with_context = Mock(return_value=[mock_search_result])
        
        return mock_retriever
    
    @pytest.fixture
    def mock_context(self):
        """Create a mock legal query context for testing"""
        return LegalQueryContext(
            query="teste de multa de estacionamento",
            document_types=["law", "regulation"],
            jurisdictions=["Portugal"],
            date_range=None,
            case_outcomes=None,
            min_quality_score=0.6,
            max_results=5
        )
    
    def test_generate_cache_key(self, mock_rag_system):
        """Test cache key generation"""
        from backend.services.cached_rag_system import CachedAdvancedRAGRetriever
        
        # Create a real instance with mocked vector store
        with patch.object(CachedAdvancedRAGRetriever, '__init__', return_value=None):
            cached_rag = CachedAdvancedRAGRetriever()
            cached_rag.cache_hits = 0
            cached_rag.cache_misses = 0
            
        # Create test context
        context = LegalQueryContext(
            query="test query",
            document_types=["law"],
            jurisdictions=["Portugal"],
            date_range=(datetime(2025, 1, 1), datetime(2025, 12, 31)),
            case_outcomes=["successful defense"],
            min_quality_score=0.7,
            max_results=10
        )
        
        # Generate cache key
        cache_key = cached_rag._generate_cache_key(context)
        
        # Verify cache key format
        assert cache_key.startswith("rag:query:")
        assert len(cache_key) > len("rag:query:")
        
        # Test that same inputs generate same key
        cache_key2 = cached_rag._generate_cache_key(context)
        assert cache_key == cache_key2
    
    @pytest.fixture
    def mock_cache(self):
        """Create a mock Redis cache"""
        mock_redis = Mock(spec=RedisCache)
        
        # Set up the cache to return None (miss) initially, then specific values on subsequent calls
        mock_redis.get.side_effect = lambda key: {
            "rag:query:test": [{"content": "cached result"}],
            "rag:query_expansion:test_hash": ["query", "expanded query"],
            "rag:semantic_search:test_hash:10": [(Mock(content="doc1"), 0.9), (Mock(content="doc2"), 0.8)],
            "rag:keyword_search:test_hash:10": [{"document_id": 1, "content": "doc1", "keyword_score": 0.8}]
        }.get(key)
        
        # Track set calls
        mock_redis.set_calls = []
        def track_set(key, value, ttl=None):
            mock_redis.set_calls.append((key, value, ttl))
            return True
        mock_redis.set.side_effect = track_set
        
        # Add other methods
        mock_redis.delete_pattern = Mock(return_value=3)
        mock_redis.get_stats = Mock(return_value={"status": "connected", "hit_rate": 80.0})
        
        return mock_redis
    
    @pytest.mark.parametrize("query_result", [
        # Test with first call returning cache miss
        [{"content": "result1"}, {"content": "result2"}],
        # Test with second call returning cache hit
        [{"content": "cached_result"}]
    ])
    def test_cached_retrieval(self, mock_rag_system, mock_context, query_result):
        """Test that cached retrieval works correctly"""
        from backend.services.cached_rag_system import CachedAdvancedRAGRetriever
        
        # Create a real instance but with mocked dependencies
        with patch.object(CachedAdvancedRAGRetriever, '__init__', return_value=None):
            cached_rag = CachedAdvancedRAGRetriever()
            
            # Set up the cache
            cached_rag._client = mock_cache
            
            # Mock the parent method that does the actual work
            with patch.object(CachedAdvancedRAGRetriever, 'retrieve_with_context', return_value=query_result):
                # First call - should miss cache
                results1 = cached_rag.retrieve_with_context(mock_context)
                
                # Second call - should hit cache
                results2 = cached_rag.retrieve_with_context(mock_context)
                
                # Verify results are correct
                assert results1 == query_result
                assert results2 == query_result
                
                # Verify cache was used on second call
                assert cached_rag.cache_hits == 1
                assert cached_rag.cache_misses == 1
    
    def test_cache_invalidation(self, mock_rag_system):
        """Test cache invalidation functionality"""
        from backend.services.cached_rag_system import CachedAdvancedRAGRetriever
        
        # Create a real instance with mocked dependencies
        with patch.object(CachedAdvancedRAGRetriever, '__init__', return_value=None):
            cached_rag = CachedAdvancedRAGRetriever()
            
            # Set up the cache
            cached_rag._client = mock_cache
            
            # Test invalidation of specific query
            result = cached_rag.invalidate_query_cache("test query")
            assert result == 3  # Mock return value
            
            # Test invalidation of all query caches
            mock_cache.delete_pattern.assert_called_with("rag:query:*")
            
            # Test invalidation of all search caches
            result = cached_rag.invalidate_search_cache()
            assert result == 12  # Mock return value (3 * 4 patterns)
            
            # Verify all patterns were called
            expected_calls = [
                "rag:semantic_search:*",
                "rag:keyword_search:*", 
                "rag:query_expansion:*",
                "rag:relevance_score:*"
            ]
            
            # Count how many times delete_pattern was called with each pattern
            pattern_counts = {}
            for call in mock_cache.delete_pattern.call_args_list:
                pattern = call[0][0]
                pattern_counts[pattern] = pattern_counts.get(pattern, 0) + 1
            
            # Verify each pattern was called at least once
            for pattern in expected_calls:
                assert pattern in pattern_counts
    
    def test_cache_statistics(self, mock_rag_system):
        """Test cache statistics functionality"""
        from backend.services.cached_rag_system import CachedAdvancedRAGRetriever
        
        # Create a real instance with mocked dependencies
        with patch.object(CachedAdvancedRAGRetriever, '__init__', return_value=None):
            cached_rag = CachedAdvancedRAGRetriever()
            
            # Set up initial values
            cached_rag.cache_hits = 5
            cached_rag.cache_misses = 3
            cached_rag.semantic_cache_ttl = 86400
            cached_rag.keyword_cache_ttl = 86400
            cached_rag.metadata_cache_ttl = 3600
            cached_rag.query_expansion_cache_ttl = 604800
            
            # Set up the cache
            cached_rag._client = mock_cache
            
            # Get statistics
            stats = cached_rag.get_cache_stats()
            
            # Verify structure
            assert "redis_connection" in stats
            assert "rag_cache" in stats
            
            # Verify RAG-specific stats
            rag_stats = stats["rag_cache"]
            assert rag_stats["total_requests"] == 8  # 5 hits + 3 misses
            assert rag_stats["cache_hits"] == 5
            assert rag_stats["cache_misses"] == 3
            assert rag_stats["hit_rate_percentage"] == pytest.approx(62.5, rel=1e-2)  # 5/8 * 100
            assert rag_stats["semantic_cache_ttl"] == 86400
            assert rag_stats["keyword_cache_ttl"] == 86400
            assert rag_stats["metadata_cache_ttl"] == 3600
            assert rag_stats["query_expansion_cache_ttl"] == 604800
    
    @pytest.mark.parametrize("query,expected_expansion", [
        ("multa", ["multa", "contraordenação", "penalidade", "coima"]),
        ("estacionamento", ["estacionamento", "parque", "paragem"]),
        ("sinal", ["sinal", "sinalização", "indicação"])
    ])
    def test_query_expansion_caching(self, mock_rag_system, query, expected_expansion):
        """Test that query expansions are properly cached"""
        from backend.services.cached_rag_system import CachedAdvancedRAGRetriever
        
        # Create a real instance but with mocked dependencies
        with patch.object(CachedAdvancedRAGRetriever, '__init__', return_value=None):
            cached_rag = CachedAdvancedRAGRetriever()
            
            # Set up the cache
            cached_rag._client = mock_cache
            
            # Test query expansion with mock return value
            expansion = cached_rag._get_cached_query_expansion(query)
            
            # Verify cache was checked
            mock_cache.get.assert_called()
            
            # Verify the result matches our mock
            assert expansion == expected_expansion
    
    def test_performance_improvement(self, mock_rag_system, mock_context):
        """Test that caching improves performance"""
        from backend.services.cached_rag_system import CachedAdvancedRAGRetriever
        import time
        
        # Create a real instance but with mocked dependencies
        with patch.object(CachedAdvancedRAGRetriever, '__init__', return_value=None):
            cached_rag = CachedAdvancedRAGRetriever()
            
            # Set up the cache
            cached_rag._client = mock_cache
            
            # Mock the parent method to add a delay
            def slow_retrieve(context):
                time.sleep(0.1)  # Simulate slow operation
                return [{"content": "result"}]
            
            with patch.object(CachedAdvancedRAGRetriever, 'retrieve_with_context', side_effect=slow_retrieve):
                # Measure time for first call (cache miss)
                start_time = time.time()
                cached_rag.retrieve_with_context(mock_context)
                first_call_time = time.time() - start_time
                
                # Measure time for second call (cache hit)
                start_time = time.time()
                cached_rag.retrieve_with_context(mock_context)
                second_call_time = time.time() - start_time
                
                # Second call should be significantly faster
                # Allow some margin for test execution overhead
                assert second_call_time < first_call_time * 0.5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
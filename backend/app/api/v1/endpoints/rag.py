from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))

from rag.advanced_rag_system import AdvancedRAGRetriever, LegalQueryContext
from ..fines import get_db

router = APIRouter()

@router.post("/rag/search", response_model=List[Dict[str, Any]])
def search_legal_documents(
    query: str,
    document_types: Optional[List[str]] = Query(None, description="Filter by document types"),
    jurisdictions: Optional[List[str]] = Query(None, description="Filter by jurisdictions"),
    case_outcomes: Optional[List[str]] = Query(None, description="Filter by case outcomes"),
    min_quality_score: float = Query(0.0, description="Minimum quality score (0-1)"),
    max_results: int = Query(5, description="Maximum number of results", ge=1, le=20),
    db: Session = Depends(get_db)
):
    """
    Search legal documents using advanced RAG system with semantic and keyword search.
    
    Provides:
    - Semantic similarity search
    - Keyword-based filtering
    - Legal-specific query expansion
    - Metadata filtering
    - Multi-factor relevance scoring
    """
    try:
        # Initialize RAG retriever
        retriever = AdvancedRAGRetriever()
        
        # Create query context
        context = LegalQueryContext(
            query=query,
            document_types=document_types,
            jurisdictions=jurisdictions,
            case_outcomes=case_outcomes,
            min_quality_score=min_quality_score,
            max_results=max_results
        )
        
        # Perform search
        results = retriever.retrieve_with_context(context)
        
        # Format results
        formatted_results = []
        for result in results:
            formatted_results.append({
                "content": result.content,
                "document_id": result.document_id,
                "title": result.title,
                "source": result.source,
                "document_type": result.document_type,
                "jurisdiction": result.jurisdiction,
                "publication_date": result.publication_date.isoformat() if result.publication_date else None,
                "relevance_score": result.relevance_score,
                "semantic_score": result.semantic_score,
                "keyword_score": result.keyword_score,
                "metadata_bonus": result.metadata_bonus,
                "quality_score": result.quality_score
            })
        
        return formatted_results
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"RAG search failed: {str(e)}")

@router.get("/rag/knowledge-base/stats")
def get_knowledge_base_stats(db: Session = Depends(get_db)):
    """
    Get comprehensive knowledge base statistics and coverage information.
    """
    try:
        retriever = AdvancedRAGRetriever()
        stats = retriever.get_knowledge_base_stats()
        return stats
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get knowledge base stats: {str(e)}")
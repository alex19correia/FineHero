from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))

from backend.services.knowledge_base_automation import KnowledgeBaseAutomation, KnowledgeBaseStats
from backend.app.models import LegalDocument
from ..fines import get_db

router = APIRouter()

@router.get("/knowledge-base/status")
def get_knowledge_base_status(db: Session = Depends(get_db)):
    """
    Get comprehensive knowledge base status and statistics.
    
    Returns:
    - Total document count
    - Document distribution by source, type, jurisdiction
    - Quality distribution
    - Growth metrics
    - Maintenance statistics
    """
    try:
        automation = KnowledgeBaseAutomation()
        stats = automation.generate_comprehensive_stats()
        
        return {
            "total_documents": stats.total_documents,
            "documents_by_source": stats.documents_by_source,
            "documents_by_type": stats.documents_by_type,
            "documents_by_jurisdiction": stats.documents_by_jurisdiction,
            "quality_distribution": stats.quality_distribution,
            "growth_rate": stats.growth_rate,
            "average_quality_score": stats.average_quality_score,
            "recent_additions": stats.recent_additions,
            "maintenance_metrics": stats.maintenance_metrics,
            "status_date": "2025-11-11T22:14:30Z"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get knowledge base status: {str(e)}")

@router.get("/knowledge-base/documents")
def list_documents(
    skip: int = Query(0, description="Number of documents to skip"),
    limit: int = Query(50, description="Maximum number of documents to return", ge=1, le=200),
    document_type: Optional[str] = Query(None, description="Filter by document type"),
    jurisdiction: Optional[str] = Query(None, description="Filter by jurisdiction"),
    min_quality_score: Optional[float] = Query(None, description="Minimum quality score"),
    db: Session = Depends(get_db)
):
    """
    List legal documents with optional filtering and pagination.
    
    Returns paginated list of documents with metadata.
    """
    try:
        query = db.query(LegalDocument)
        
        # Apply filters
        if document_type:
            query = query.filter(LegalDocument.document_type == document_type)
        
        if jurisdiction:
            query = query.filter(LegalDocument.jurisdiction == jurisdiction)
        
        if min_quality_score is not None:
            query = query.filter(LegalDocument.quality_score >= min_quality_score)
        
        # Get total count
        total_count = query.count()
        
        # Apply pagination
        documents = query.order_by(LegalDocument.retrieval_date.desc()).offset(skip).limit(limit).all()
        
        # Format response
        document_list = []
        for doc in documents:
            document_list.append({
                "id": doc.id,
                "title": doc.title,
                "document_type": doc.document_type,
                "jurisdiction": doc.jurisdiction,
                "source": doc.source,
                "source_url": doc.source_url,
                "publication_date": doc.publication_date.isoformat() if doc.publication_date else None,
                "retrieval_date": doc.retrieval_date.isoformat() if doc.retrieval_date else None,
                "quality_score": doc.quality_score,
                "relevance_score": doc.relevance_score,
                "freshness_score": doc.freshness_score,
                "authority_score": doc.authority_score,
                "content_preview": doc.extracted_text[:200] + "..." if doc.extracted_text and len(doc.extracted_text) > 200 else doc.extracted_text
            })
        
        return {
            "documents": document_list,
            "total_count": total_count,
            "skip": skip,
            "limit": limit,
            "has_more": skip + limit < total_count
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list documents: {str(e)}")

@router.post("/knowledge-base/maintenance/manual")
def run_manual_maintenance_cycle(db: Session = Depends(get_db)):
    """
    Run a complete manual maintenance cycle for the knowledge base.
    
    Performs:
    1. Document scraping
    2. Quality assessment
    3. Duplicate cleanup
    4. Statistics update
    """
    try:
        automation = KnowledgeBaseAutomation()
        stats = automation.run_manual_maintenance_cycle()
        
        return {
            "success": True,
            "maintenance_completed": True,
            "statistics": {
                "total_documents": stats.total_documents,
                "growth_rate": stats.growth_rate,
                "average_quality_score": stats.average_quality_score,
                "documents_by_source": stats.documents_by_source,
                "quality_distribution": stats.quality_distribution
            },
            "maintenance_date": "2025-11-11T22:14:30Z"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Manual maintenance cycle failed: {str(e)}")

@router.get("/knowledge-base/maintenance/stats")
def get_maintenance_statistics(db: Session = Depends(get_db)):
    """
    Get maintenance operation statistics and scheduling information.
    """
    try:
        automation = KnowledgeBaseAutomation()
        
        # Get maintenance statistics
        stats = automation.maintenance_stats
        
        return {
            "last_scrape": stats.get('last_scrape'),
            "last_quality_assessment": stats.get('last_quality_assessment'),
            "last_duplicate_cleanup": stats.get('last_duplicate_cleanup'),
            "documents_scraped": stats['documents_scraped'],
            "documents_quality_checked": stats['documents_quality_checked'],
            "duplicates_removed": stats['duplicates_removed'],
            "errors_encountered": stats['errors_encountered'],
            "maintenance_date": "2025-11-11T22:14:30Z"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get maintenance statistics: {str(e)}")

@router.get("/knowledge-base/sources")
def get_document_sources(db: Session = Depends(get_db)):
    """
    Get list of all document sources and their statistics.
    """
    try:
        from collections import Counter
        
        # Get source distribution
        source_results = db.query(LegalDocument.source).all()
        sources = [source for source, in source_results]
        source_counts = Counter(sources)
        
        # Get statistics per source
        source_stats = []
        for source, count in source_counts.items():
            # Get recent additions for this source
            recent_docs = db.query(LegalDocument).filter(
                LegalDocument.source == source,
                LegalDocument.retrieval_date >= db.query(LegalDocument.retrieval_date).order_by(LegalDocument.retrieval_date.desc()).first()[0]  # Last 30 days
            ).count()
            
            # Get average quality score for this source
            avg_quality = db.query(LegalDocument.quality_score).filter(
                LegalDocument.source == source
            ).all()
            
            avg_quality_score = sum(score for score, in avg_quality) / len(avg_quality) if avg_quality else 0.0
            
            source_stats.append({
                "source": source,
                "total_documents": count,
                "recent_additions": recent_docs,
                "average_quality_score": avg_quality_score
            })
        
        return {
            "sources": sorted(source_stats, key=lambda x: x['total_documents'], reverse=True),
            "total_sources": len(source_stats),
            "query_date": "2025-11-11T22:14:30Z"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get document sources: {str(e)}")

@router.get("/knowledge-base/coverage")
def get_knowledge_base_coverage(db: Session = Depends(get_db)):
    """
    Get knowledge base coverage analysis and gaps.
    
    Returns information about what legal areas are well-covered
    and what might be missing.
    """
    try:
        from collections import Counter
        from datetime import datetime, timedelta
        
        # Get document type distribution
        type_results = db.query(LegalDocument.document_type).all()
        types = [doc_type for doc_type, in type_results]
        type_counts = Counter(types)
        
        # Get jurisdiction distribution
        jurisdiction_results = db.query(LegalDocument.jurisdiction).all()
        jurisdictions = [jurisdiction for jurisdiction, in jurisdiction_results]
        jurisdiction_counts = Counter(jurisdictions)
        
        # Get recent coverage (last 6 months)
        six_months_ago = datetime.now() - timedelta(days=180)
        recent_docs = db.query(LegalDocument).filter(
            LegalDocument.publication_date >= six_months_ago
        ).all()
        
        recent_coverage = {
            "total_recent_documents": len(recent_docs),
            "recent_by_type": Counter(doc.document_type for doc in recent_docs),
            "recent_by_jurisdiction": Counter(doc.jurisdiction for doc in recent_docs)
        }
        
        # Calculate coverage gaps
        expected_types = ["law", "regulation", "court_decision", "precedent", "guideline"]
        missing_types = [t for t in expected_types if t not in type_counts]
        
        return {
            "document_types": dict(type_counts),
            "jurisdictions": dict(jurisdiction_counts),
            "recent_coverage": {
                "total_recent_documents": recent_coverage["total_recent_documents"],
                "recent_by_type": dict(recent_coverage["recent_by_type"]),
                "recent_by_jurisdiction": dict(recent_coverage["recent_by_jurisdiction"])
            },
            "coverage_gaps": {
                "missing_document_types": missing_types,
                "type_recommendations": [
                    "court_decisions", "legal_precedents", "regulatory_guidelines"
                ]
            },
            "coverage_percentage": (len(recent_docs) / max(1, len(recent_docs) + 50)) * 100,  # Estimated total target
            "analysis_date": "2025-11-11T22:14:30Z"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get knowledge base coverage: {str(e)}")

@router.delete("/knowledge-base/documents/{document_id}")
def delete_document(
    document_id: int,
    db: Session = Depends(get_db)
):
    """
    Delete a specific document from the knowledge base.
    
    Note: This should typically be done through the duplicate cleanup process
    rather than manual deletion.
    """
    try:
        document = db.query(LegalDocument).filter(LegalDocument.id == document_id).first()
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Delete the document
        db.delete(document)
        db.commit()
        
        return {
            "success": True,
            "message": f"Document {document_id} has been deleted",
            "deleted_document": {
                "id": document_id,
                "title": document.title,
                "source": document.source
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete document: {str(e)}")
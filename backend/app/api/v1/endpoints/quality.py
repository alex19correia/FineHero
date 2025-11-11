from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))

from backend.services.quality_scoring_system import QualityScoringEngine, QualityMetrics
from backend.app.models import LegalDocument
from ..fines import get_db

router = APIRouter()

@router.post("/documents/{document_id}/quality", response_model=Dict[str, Any])
def assess_document_quality(
    document_id: int,
    db: Session = Depends(get_db)
):
    """
    Assess quality metrics for a specific document.
    
    Returns comprehensive quality scores including:
    - Overall quality score
    - Content quality assessment
    - Legal relevance scoring
    - Authority scoring
    - Freshness scoring
    - Completeness scoring
    - Legal accuracy scoring
    - Source reliability
    """
    try:
        # Get document from database
        document = db.query(LegalDocument).filter(LegalDocument.id == document_id).first()
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Initialize quality scoring engine
        engine = QualityScoringEngine()
        
        # Calculate comprehensive quality score
        metrics = engine.calculate_comprehensive_quality_score(document)
        
        # Format response
        return {
            "document_id": document_id,
            "overall_score": metrics.overall_score,
            "content_quality": metrics.content_quality,
            "relevance_score": metrics.relevance_score,
            "authority_score": metrics.authority_score,
            "freshness_score": metrics.freshness_score,
            "completeness_score": metrics.completeness_score,
            "legal_accuracy_score": metrics.legal_accuracy_score,
            "source_reliability": metrics.source_reliability,
            "assessment_date": metrics.__dict__ if hasattr(metrics, '__dict__') else {}
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Quality assessment failed: {str(e)}")

@router.post("/documents/quality/batch")
def batch_quality_assessment(
    document_ids: Optional[List[int]] = Query(None, description="List of document IDs to assess"),
    limit: int = Query(100, description="Maximum number of documents to process", ge=1, le=500),
    db: Session = Depends(get_db)
):
    """
    Perform batch quality assessment on multiple documents.
    
    If no document_ids provided, assesses the most recent documents.
    Returns filtering results and quality distribution statistics.
    """
    try:
        engine = QualityScoringEngine()
        
        # Get documents to assess
        if document_ids:
            documents = db.query(LegalDocument).filter(LegalDocument.id.in_(document_ids)).all()
        else:
            documents = db.query(LegalDocument).order_by(LegalDocument.retrieval_date.desc()).limit(limit).all()
        
        if not documents:
            raise HTTPException(status_code=404, detail="No documents found for assessment")
        
        # Perform quality filtering
        filtering_result = engine.filter_documents_by_quality(documents, threshold=0.6)
        
        # Format response
        return {
            "total_documents_assessed": filtering_result.total_documents,
            "high_quality_documents": filtering_result.high_quality_documents,
            "medium_quality_documents": filtering_result.medium_quality_documents,
            "low_quality_documents": filtering_result.low_quality_documents,
            "filtered_out_documents": filtering_result.filtered_out_documents,
            "quality_distribution": filtering_result.quality_distribution,
            "average_quality_scores": filtering_result.average_quality_scores,
            "assessment_date": "2025-11-11T22:12:00Z"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Batch quality assessment failed: {str(e)}")

@router.get("/documents/quality/statistics")
def get_quality_statistics(
    db: Session = Depends(get_db)
):
    """
    Get comprehensive quality statistics for all documents in the knowledge base.
    """
    try:
        engine = QualityScoringEngine()
        
        # Get all documents
        documents = db.query(LegalDocument).all()
        
        if not documents:
            return {
                "total_documents": 0,
                "quality_distribution": {},
                "average_quality_score": 0.0,
                "quality_trends": {}
            }
        
        # Analyze quality distribution
        quality_distribution = engine._analyze_quality_distribution(documents)
        
        return {
            "total_documents": len(documents),
            "quality_distribution": quality_distribution,
            "average_quality_score": quality_distribution.get('statistics', {}).get('mean', 0.0),
            "quality_trends": {
                "high_quality_percentage": (quality_distribution.get('high_quality', 0) / len(documents)) * 100,
                "medium_quality_percentage": (quality_distribution.get('medium_quality', 0) / len(documents)) * 100,
                "low_quality_percentage": (quality_distribution.get('low_quality', 0) / len(documents)) * 100
            },
            "statistics": quality_distribution.get('statistics', {})
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get quality statistics: {str(e)}")

@router.post("/quality/continuous-learning")
def continuous_learning_update(
    feedback_data: List[Dict[str, Any]],
    db: Session = Depends(get_db)
):
    """
    Update quality scoring model based on user feedback.
    
    Expects feedback_data in format:
    [
        {
            "document_id": 123,
            "rating": 1-5,
            "reason": "explanation"
        }
    ]
    """
    try:
        engine = QualityScoringEngine()
        
        # Validate feedback data
        for feedback in feedback_data:
            if not all(key in feedback for key in ['document_id', 'rating']):
                raise HTTPException(status_code=400, detail="Each feedback must include document_id and rating")
            if not isinstance(feedback['rating'], int) or not (1 <= feedback['rating'] <= 5):
                raise HTTPException(status_code=400, detail="Rating must be an integer between 1 and 5")
        
        # Update quality scoring model
        learning_stats = engine.continuous_learning_update(feedback_data)
        
        return {
            "success": True,
            "feedback_entries_processed": learning_stats['feedback_entries_processed'],
            "quality_distribution_feedback": learning_stats['quality_distribution_feedback'],
            "updated_thresholds": learning_stats['updated_thresholds'],
            "updated_feature_weights": learning_stats['updated_feature_weights'],
            "learning_date": learning_stats['learning_date']
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Continuous learning update failed: {str(e)}")
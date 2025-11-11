from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy.orm import SessionLocal
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))

from backend.services.analytics_service import AnalyticsService, EventData
from ..fines import get_db

router = APIRouter()

@router.get("/analytics/user/{user_id}/dashboard")
def get_user_dashboard_data(
    user_id: str,
    days: int = Query(30, description="Number of days to analyze", ge=1, le=365),
    db: Session = Depends(get_db)
):
    """
    Get comprehensive dashboard data for a specific user.
    
    Returns:
    - Summary statistics (PDFs uploaded, defenses generated, etc.)
    - Daily activity breakdown
    - Feature usage statistics
    - Recent events
    """
    try:
        analytics_service = AnalyticsService(db)
        dashboard_data = analytics_service.get_user_dashboard_data(user_id, days)
        
        return dashboard_data
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get user dashboard data: {str(e)}")

@router.get("/analytics/system/overview")
def get_system_overview(
    hours: int = Query(24, description="Number of hours to analyze", ge=1, le=168),
    db: Session = Depends(get_db)
):
    """
    Get system-wide analytics overview.
    
    Returns:
    - Summary metrics (total events, unique users, etc.)
    - Hourly breakdown of activity
    - Top event types
    - System health indicators
    """
    try:
        analytics_service = AnalyticsService(db)
        overview_data = analytics_service.get_system_overview(hours)
        return overview_data
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get system overview: {str(e)}")

@router.post("/analytics/events")
def track_event(
    event: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """
    Track an analytics event.
    
    Expected event format:
    {
        "event_type": "pdf_upload",
        "user_id": "user123",
        "data": {
            "file_size": 1024,
            "processing_time": 2.5
        },
        "response_time": 1.2,
        "success": true
    }
    """
    try:
        analytics_service = AnalyticsService(db)
        
        # Validate event data
        required_fields = ['event_type']
        if not all(field in event for field in required_fields):
            raise HTTPException(status_code=400, detail="Event must include event_type")
        
        # Create EventData object
        event_data = EventData(
            event_type=event['event_type'],
            user_id=event.get('user_id'),
            session_id=event.get('session_id'),
            data=event.get('data'),
            response_time=event.get('response_time'),
            success=event.get('success', True),
            error_message=event.get('error_message')
        )
        
        result = analytics_service.track_event(event_data)
        
        if result['success']:
            return {
                "success": True,
                "event_id": result['event_id'],
                "timestamp": result['timestamp']
            }
        else:
            raise HTTPException(status_code=500, detail=f"Failed to track event: {result['error']}")
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Event tracking failed: {str(e)}")

@router.post("/analytics/pdf-upload")
def track_pdf_upload(
    user_id: str,
    file_size: int,
    processing_time: float,
    success: bool = True,
    db: Session = Depends(get_db)
):
    """
    Track PDF upload events with standardized metrics.
    """
    try:
        analytics_service = AnalyticsService(db)
        result = analytics_service.track_pdf_upload(user_id, file_size, processing_time, success)
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF upload tracking failed: {str(e)}")

@router.post("/analytics/defense-generation")
def track_defense_generation(
    user_id: str,
    fine_data: Dict[str, Any],
    processing_time: float,
    success: bool = True,
    db: Session = Depends(get_db)
):
    """
    Track defense generation events with fine-specific metrics.
    
    Expected fine_data format:
    {
        "fine_amount": 120.50,
        "infraction_code": "ART-048",
        "location": "Lisboa"
    }
    """
    try:
        analytics_service = AnalyticsService(db)
        result = analytics_service.track_defense_generation(user_id, fine_data, processing_time, success)
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Defense generation tracking failed: {str(e)}")

@router.get("/analytics/metrics/summary")
def get_analytics_summary(
    days: int = Query(30, description="Number of days to analyze", ge=1, le=365),
    db: Session = Depends(get_db)
):
    """
    Get high-level analytics summary for admin dashboard.
    """
    try:
        analytics_service = AnalyticsService(db)
        
        # Get system overview
        system_overview = analytics_service.get_system_overview(hours=days*24)
        
        # Get key metrics
        summary = {
            "period_days": days,
            "total_events": system_overview.get('summary', {}).get('total_events', 0),
            "unique_users": system_overview.get('summary', {}).get('unique_users', 0),
            "pdfs_processed": system_overview.get('summary', {}).get('pdfs_processed', 0),
            "defenses_generated": system_overview.get('summary', {}).get('defenses_generated', 0),
            "avg_response_time": system_overview.get('summary', {}).get('avg_response_time', 0),
            "error_rate": system_overview.get('summary', {}).get('error_rate', 0),
            "top_events": system_overview.get('top_events', []),
            "generation_date": "2025-11-11T22:13:00Z"
        }
        
        return summary
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get analytics summary: {str(e)}")
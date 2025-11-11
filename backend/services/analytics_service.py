"""
Analytics and KPI Tracking System
Comprehensive tracking for business metrics, user behavior, and system performance
"""

import os
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union, Any
from dataclasses import dataclass, asdict
from sqlalchemy.orm import Session
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

Base = declarative_base()


class AnalyticsEvent(Base):
    """
    Database model for tracking analytics events
    """
    __tablename__ = "analytics_events"
    
    id = Column(Integer, primary_key=True, index=True)
    event_type = Column(String, index=True)  # 'page_view', 'pdf_upload', 'defense_generated', etc.
    user_id = Column(String, index=True)
    session_id = Column(String, index=True)
    event_data = Column(JSON)  # Store event-specific data as JSON
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    ip_address = Column(String)
    user_agent = Column(Text)
    referrer = Column(String)
    
    # Performance metrics
    response_time = Column(Float)  # in seconds
    success = Column(Boolean, default=True)
    error_message = Column(Text)
    
    def to_dict(self):
        return {
            'id': self.id,
            'event_type': self.event_type,
            'user_id': self.user_id,
            'session_id': self.session_id,
            'event_data': self.event_data,
            'timestamp': self.timestamp.isoformat(),
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'referrer': self.referrer,
            'response_time': self.response_time,
            'success': self.success,
            'error_message': self.error_message
        }


class UserKPI(Base):
    """
    Database model for tracking user KPIs over time
    """
    __tablename__ = "user_kpis"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True)
    date = Column(DateTime, index=True)
    
    # Usage metrics
    pdfs_uploaded = Column(Integer, default=0)
    defenses_generated = Column(Integer, default=0)
    successful_defenses = Column(Integer, default=0)
    avg_processing_time = Column(Float, default=0.0)
    
    # Business metrics
    total_fine_amount = Column(Float, default=0.0)
    total_potential_savings = Column(Float, default=0.0)  # Estimated savings from successful defenses
    subscription_tier = Column(String)  # free, premium, enterprise
    
    # Engagement metrics
    session_count = Column(Integer, default=0)
    avg_session_duration = Column(Float, default=0.0)  # in minutes
    feature_usage = Column(JSON)  # JSON object tracking feature usage
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'date': self.date.isoformat(),
            'pdfs_uploaded': self.pdfs_uploaded,
            'defenses_generated': self.defenses_generated,
            'successful_defenses': self.successful_defenses,
            'avg_processing_time': self.avg_processing_time,
            'total_fine_amount': self.total_fine_amount,
            'total_potential_savings': self.total_potential_savings,
            'subscription_tier': self.subscription_tier,
            'session_count': self.session_count,
            'avg_session_duration': self.avg_session_duration,
            'feature_usage': self.feature_usage
        }


class SystemKPI(Base):
    """
    Database model for tracking system-level KPIs
    """
    __tablename__ = "system_kpis"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Performance metrics
    avg_response_time = Column(Float)  # seconds
    request_count = Column(Integer)
    error_rate = Column(Float)  # percentage
    success_rate = Column(Float)  # percentage
    
    # Resource metrics
    cpu_usage = Column(Float)  # percentage
    memory_usage = Column(Float)  # MB
    disk_usage = Column(Float)  # percentage
    
    # Business metrics
    total_pdfs_processed = Column(Integer)
    total_defenses_generated = Column(Integer)
    active_users_24h = Column(Integer)
    active_users_7d = Column(Integer)
    active_users_30d = Column(Integer)
    
    def to_dict(self):
        return {
            'id': self.id,
            'timestamp': self.timestamp.isoformat(),
            'avg_response_time': self.avg_response_time,
            'request_count': self.request_count,
            'error_rate': self.error_rate,
            'success_rate': self.success_rate,
            'cpu_usage': self.cpu_usage,
            'memory_usage': self.memory_usage,
            'disk_usage': self.disk_usage,
            'total_pdfs_processed': self.total_pdfs_processed,
            'total_defenses_generated': self.total_defenses_generated,
            'active_users_24h': self.active_users_24h,
            'active_users_7d': self.active_users_7d,
            'active_users_30d': self.active_users_30d
        }


@dataclass
class EventData:
    """
    Standardized event data structure
    """
    event_type: str
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    response_time: Optional[float] = None
    success: bool = True
    error_message: Optional[str] = None


class AnalyticsService:
    """
    Comprehensive analytics tracking service
    """
    
    def __init__(self, db_session: Session):
        self.db = db_session
        self.session_id = self._generate_session_id()
    
    def track_event(self, event: EventData) -> Dict[str, Any]:
        """
        Track a single analytics event
        """
        try:
            event_record = AnalyticsEvent(
                event_type=event.event_type,
                user_id=event.user_id,
                session_id=event.session_id or self.session_id,
                event_data=event.data or {},
                response_time=event.response_time,
                success=event.success,
                error_message=event.error_message,
                timestamp=datetime.utcnow()
            )
            
            self.db.add(event_record)
            self.db.commit()
            self.db.refresh(event_record)
            
            return {
                'success': True,
                'event_id': event_record.id,
                'timestamp': event_record.timestamp.isoformat()
            }
            
        except Exception as e:
            self.db.rollback()
            return {
                'success': False,
                'error': str(e)
            }
    
    def track_pdf_upload(self, user_id: str, file_size: int, processing_time: float, success: bool = True) -> Dict[str, Any]:
        """
        Track PDF upload events
        """
        event_data = EventData(
            event_type='pdf_upload',
            user_id=user_id,
            data={
                'file_size': file_size,
                'upload_method': 'web_interface'  # or 'api', 'cli'
            },
            response_time=processing_time,
            success=success
        )
        
        return self.track_event(event_data)
    
    def track_defense_generation(self, user_id: str, fine_data: Dict, processing_time: float, success: bool = True) -> Dict[str, Any]:
        """
        Track defense generation events
        """
        event_data = EventData(
            event_type='defense_generated',
            user_id=user_id,
            data={
                'fine_amount': fine_data.get('fine_amount'),
                'infraction_code': fine_data.get('infraction_code'),
                'template_used': 'standard',  # This would be dynamic in real implementation
                'success_probability': 0.75  # This would come from the AI model
            },
            response_time=processing_time,
            success=success
        )
        
        return self.track_event(event_data)
    
    def track_user_engagement(self, user_id: str, action: str, additional_data: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Track user engagement events
        """
        event_data = EventData(
            event_type='user_engagement',
            user_id=user_id,
            data={
                'action': action,
                'page': additional_data.get('page') if additional_data else None,
                'duration': additional_data.get('duration') if additional_data else None
            }
        )
        
        return self.track_event(event_data)
    
    def update_user_kpis(self, user_id: str, date: datetime, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update or create user KPI record
        """
        try:
            kpi_record = self.db.query(UserKPI).filter(
                UserKPI.user_id == user_id,
                UserKPI.date >= date.date(),
                UserKPI.date < date.date() + timedelta(days=1)
            ).first()
            
            if not kpi_record:
                kpi_record = UserKPI(user_id=user_id, date=date.date())
                self.db.add(kpi_record)
            
            # Update metrics
            for key, value in metrics.items():
                if hasattr(kpi_record, key):
                    setattr(kpi_record, key, value)
            
            self.db.commit()
            self.db.refresh(kpi_record)
            
            return {
                'success': True,
                'kpi_id': kpi_record.id
            }
            
        except Exception as e:
            self.db.rollback()
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_user_dashboard_data(self, user_id: str, days: int = 30) -> Dict[str, Any]:
        """
        Get comprehensive dashboard data for a user
        """
        try:
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)
            
            # Get user events
            events = self.db.query(AnalyticsEvent).filter(
                AnalyticsEvent.user_id == user_id,
                AnalyticsEvent.timestamp >= start_date,
                AnalyticsEvent.timestamp <= end_date
            ).all()
            
            # Get user KPIs
            kpis = self.db.query(UserKPI).filter(
                UserKPI.user_id == user_id,
                UserKPI.date >= start_date.date(),
                UserKPI.date <= end_date.date()
            ).all()
            
            # Aggregate data
            dashboard_data = {
                'user_id': user_id,
                'period_days': days,
                'summary': {
                    'total_pdfs_uploaded': sum(event.event_data.get('file_size', 0) for event in events if event.event_type == 'pdf_upload'),
                    'total_defenses_generated': len([e for e in events if e.event_type == 'defense_generated']),
                    'avg_processing_time': sum(e.response_time or 0 for e in events if e.response_time) / len(events) if events else 0,
                    'success_rate': len([e for e in events if e.success]) / len(events) * 100 if events else 0
                },
                'daily_activity': self._aggregate_daily_activity(events),
                'feature_usage': self._get_feature_usage(events),
                'recent_events': [event.to_dict() for event in sorted(events, key=lambda x: x.timestamp, reverse=True)[:10]]
            }
            
            return dashboard_data
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_system_overview(self, hours: int = 24) -> Dict[str, Any]:
        """
        Get system-wide analytics overview
        """
        try:
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(hours=hours)
            
            # Get recent events
            events = self.db.query(AnalyticsEvent).filter(
                AnalyticsEvent.timestamp >= start_time,
                AnalyticsEvent.timestamp <= end_time
            ).all()
            
            # Get recent system KPIs
            system_kpis = self.db.query(SystemKPI).filter(
                SystemKPI.timestamp >= start_time
            ).order_by(SystemKPI.timestamp.desc()).limit(24).all()
            
            overview_data = {
                'period_hours': hours,
                'summary': {
                    'total_events': len(events),
                    'unique_users': len(set(event.user_id for event in events if event.user_id)),
                    'pdfs_processed': len([e for e in events if e.event_type == 'pdf_upload']),
                    'defenses_generated': len([e for e in events if e.event_type == 'defense_generated']),
                    'avg_response_time': sum(e.response_time or 0 for e in events if e.response_time) / len(events) if events else 0,
                    'error_rate': len([e for e in events if not e.success]) / len(events) * 100 if events else 0
                },
                'hourly_breakdown': self._get_hourly_breakdown(events),
                'top_events': self._get_top_events(events),
                'system_health': system_kpis[0].to_dict() if system_kpis else None
            }
            
            return overview_data
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _generate_session_id(self) -> str:
        """
        Generate unique session ID
        """
        import uuid
        return str(uuid.uuid4())
    
    def _aggregate_daily_activity(self, events: List[AnalyticsEvent]) -> List[Dict[str, Any]]:
        """
        Aggregate events by day
        """
        daily_data = {}
        
        for event in events:
            day = event.timestamp.date().isoformat()
            
            if day not in daily_data:
                daily_data[day] = {
                    'date': day,
                    'pdfs_uploaded': 0,
                    'defenses_generated': 0,
                    'total_events': 0,
                    'unique_sessions': set()
                }
            
            daily_data[day]['total_events'] += 1
            daily_data[day]['unique_sessions'].add(event.session_id)
            
            if event.event_type == 'pdf_upload':
                daily_data[day]['pdfs_uploaded'] += 1
            elif event.event_type == 'defense_generated':
                daily_data[day]['defenses_generated'] += 1
        
        # Convert sets to counts
        for day_data in daily_data.values():
            day_data['unique_sessions'] = len(day_data['unique_sessions'])
            del day_data['unique_sessions']  # Remove the set, keep the count as 'unique_sessions_count'
        
        return sorted(daily_data.values(), key=lambda x: x['date'])
    
    def _get_feature_usage(self, events: List[AnalyticsEvent]) -> Dict[str, int]:
        """
        Get feature usage statistics
        """
        feature_usage = {}
        
        for event in events:
            if event.event_type == 'user_engagement':
                action = event.event_data.get('action', 'unknown')
                feature_usage[action] = feature_usage.get(action, 0) + 1
        
        return feature_usage
    
    def _get_hourly_breakdown(self, events: List[AnalyticsEvent]) -> List[Dict[str, Any]]:
        """
        Get hourly breakdown of events
        """
        hourly_data = {}
        
        for event in events:
            hour = event.timestamp.replace(minute=0, second=0, microsecond=0).isoformat()
            
            if hour not in hourly_data:
                hourly_data[hour] = {
                    'hour': hour,
                    'total_events': 0,
                    'unique_users': set(),
                    'avg_response_time': 0,
                    'response_times': []
                }
            
            hourly_data[hour]['total_events'] += 1
            if event.user_id:
                hourly_data[hour]['unique_users'].add(event.user_id)
            if event.response_time:
                hourly_data[hour]['response_times'].append(event.response_time)
        
        # Process hourly data
        result = []
        for hour_data in hourly_data.values():
            avg_time = sum(hour_data['response_times']) / len(hour_data['response_times']) if hour_data['response_times'] else 0
            result.append({
                'hour': hour_data['hour'],
                'total_events': hour_data['total_events'],
                'unique_users': len(hour_data['unique_users']),
                'avg_response_time': avg_time
            })
        
        return sorted(result, key=lambda x: x['hour'])
    
    def _get_top_events(self, events: List[AnalyticsEvent]) -> List[Dict[str, int]]:
        """
        Get top event types by frequency
        """
        event_counts = {}
        
        for event in events:
            event_type = event.event_type
            event_counts[event_type] = event_counts.get(event_type, 0) + 1
        
        return sorted(event_counts.items(), key=lambda x: x[1], reverse=True)
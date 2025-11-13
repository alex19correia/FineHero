"""
Secure Analytics and KPI Tracking System
Comprehensive tracking with SQL injection protection and input validation
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union, Any
from dataclasses import dataclass, asdict
from sqlalchemy.orm import Session
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from .security_validator import SecurityValidator

Base = declarative_base()

# Security logging setup
security_logger = logging.getLogger('analytics_security')
logger = logging.getLogger(__name__)


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
    Validated event data structure with security checks
    """
    event_type: str
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    response_time: Optional[float] = None
    success: bool = True
    error_message: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    referrer: Optional[str] = None
    
    def __post_init__(self):
        """Validate and sanitize event data after initialization"""
        validator = SecurityValidator()
        
        # Validate event type
        if not self.event_type or not isinstance(self.event_type, str):
            raise ValueError("Event type must be a non-empty string")
        
        # Sanitize and validate event type
        safe_event_type = re.sub(r'[^a-zA-Z0-9_]', '', self.event_type.strip())
        if safe_event_type != self.event_type:
            security_logger.warning(f"Event type sanitized: {self.event_type} -> {safe_event_type}")
        self.event_type = safe_event_type
        
        # Validate user_id if provided
        if self.user_id:
            self.user_id = validator.validate_user_id(self.user_id)
        
        # Validate session_id if provided
        if self.session_id:
            self.session_id = validator.validate_session_id(self.session_id)
        
        # Validate and sanitize event data
        if self.data:
            self.data = validator.validate_event_data(self.data)
        
        # Validate response time
        if self.response_time is not None:
            if not isinstance(self.response_time, (int, float)) or self.response_time < 0 or self.response_time > 300:
                raise ValueError("Response time must be a number between 0 and 300 seconds")
        
        # Validate error message length
        if self.error_message and len(self.error_message) > 500:
            self.error_message = self.error_message[:500]
        
        # Validate and sanitize IP address
        if self.ip_address:
            self.ip_address = validator.validate_ip_address(self.ip_address)
        
        # Validate and sanitize URL fields
        if self.referrer:
            self.referrer = validator.validate_url(self.referrer)


class AnalyticsService:
    """
    Secure analytics tracking service with SQL injection protection
    """
    
    def __init__(self, db_session: Session):
        self.db = db_session
        self.validator = SecurityValidator()
        self.session_id = self._generate_session_id()
        self._rate_limits = {}  # Simple in-memory rate limiting
        self._rate_limit_window = 60  # seconds
        self._max_requests_per_window = 100
    
    def track_event(self, event: EventData) -> Dict[str, Any]:
        """
        Securely track a single analytics event with validation
        """
        try:
            # Validate event data
            validated_event = EventData(
                event_type=event.event_type,
                user_id=event.user_id,
                session_id=event.session_id,
                data=event.data,
                response_time=event.response_time,
                success=event.success,
                error_message=event.error_message,
                ip_address=event.ip_address,
                user_agent=event.user_agent,
                referrer=event.referrer
            )
            
            # Check rate limiting
            if not self._check_rate_limit(validated_event.user_id or "anonymous"):
                return self.validator.handle_secure_error(ValueError("Rate limit exceeded"))
            
            # Create database record using ORM (SQL injection safe)
            event_record = AnalyticsEvent(
                event_type=validated_event.event_type,
                user_id=validated_event.user_id,
                session_id=validated_event.session_id or self.session_id,
                event_data=validated_event.data or {},
                response_time=validated_event.response_time,
                success=validated_event.success,
                error_message=validated_event.error_message,
                ip_address=validated_event.ip_address,
                user_agent=validated_event.user_agent,
                referrer=validated_event.referrer,
                timestamp=datetime.utcnow()
            )
            
            # Save to database with error handling
            self.db.add(event_record)
            self.db.commit()
            self.db.refresh(event_record)
            
            # Log successful event tracking
            security_logger.info(f"Event tracked successfully: {validated_event.event_type}", extra={
                "event_id": event_record.id,
                "user_id": validated_event.user_id,
                "event_type": validated_event.event_type
            })
            
            return {
                'success': True,
                'event_id': event_record.id,
                'timestamp': event_record.timestamp.isoformat()
            }
            
        except SQLAlchemyError as e:
            self.db.rollback()
            security_logger.error(f"Database error in track_event: {type(e).__name__}")
            return self.validator.handle_secure_error(e)
        except Exception as e:
            self.db.rollback()
            security_logger.error(f"Unexpected error in track_event: {type(e).__name__}")
            return self.validator.handle_secure_error(e)
    
    def track_pdf_upload(self, user_id: str, file_size: int, processing_time: float, success: bool = True, 
                        upload_method: str = "web_interface") -> Dict[str, Any]:
        """
        Securely track PDF upload events
        """
        try:
            # Validate all parameters
            validated_user_id = self.validator.validate_user_id(user_id)
            
            if not isinstance(file_size, int) or file_size <= 0 or file_size > 100000000:  # 100MB limit
                raise ValueError("File size must be a positive integer under 100MB")
            
            if not isinstance(processing_time, (int, float)) or processing_time < 0 or processing_time > 300:
                raise ValueError("Processing time must be between 0 and 300 seconds")
            
            if upload_method not in ['web_interface', 'api', 'cli']:
                upload_method = 'web_interface'  # Default fallback
            
            event_data = EventData(
                event_type='pdf_upload',
                user_id=validated_user_id,
                data={
                    'file_size': file_size,
                    'upload_method': upload_method,
                    'processing_success': success
                },
                response_time=processing_time,
                success=success
            )
            
            return self.track_event(event_data)
            
        except Exception as e:
            security_logger.error(f"Error tracking PDF upload: {type(e).__name__}", extra={
                "user_id": user_id,
                "file_size": file_size
            })
            return self.validator.handle_secure_error(e)
    
    def track_defense_generation(self, user_id: str, fine_data: Dict, processing_time: float, 
                               success: bool = True) -> Dict[str, Any]:
        """
        Securely track defense generation events
        """
        try:
            # Validate parameters
            validated_user_id = self.validator.validate_user_id(user_id)
            
            if not isinstance(fine_data, dict):
                raise ValueError("Fine data must be a dictionary")
            
            # Validate and sanitize fine data
            sanitized_fine_data = {}
            if 'fine_amount' in fine_data:
                amount = fine_data.get('fine_amount')
                if isinstance(amount, (int, float)) and 0 <= amount <= 100000:
                    sanitized_fine_data['fine_amount'] = amount
                else:
                    security_logger.warning(f"Invalid fine amount: {amount}")
            
            if 'infraction_code' in fine_data:
                code = fine_data.get('infraction_code')
                if isinstance(code, str) and len(code) <= 20:
                    sanitized_fine_data['infraction_code'] = re.sub(r'[^A-Za-z0-9\-_]', '', code)
            
            event_data = EventData(
                event_type='defense_generated',
                user_id=validated_user_id,
                data={
                    **sanitized_fine_data,
                    'template_used': 'standard',
                    'success_probability': 0.75
                },
                response_time=processing_time,
                success=success
            )
            
            return self.track_event(event_data)
            
        except Exception as e:
            security_logger.error(f"Error tracking defense generation: {type(e).__name__}", extra={
                "user_id": user_id,
                "fine_data_keys": list(fine_data.keys()) if isinstance(fine_data, dict) else None
            })
            return self.validator.handle_secure_error(e)
    
    def track_user_engagement(self, user_id: str, action: str, additional_data: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Securely track user engagement events
        """
        try:
            # Validate parameters
            validated_user_id = self.validator.validate_user_id(user_id)
            
            if not isinstance(action, str) or not action.strip():
                raise ValueError("Action must be a non-empty string")
            
            # Sanitize action
            safe_action = re.sub(r'[^a-zA-Z0-9_]', '', action.strip())
            if not safe_action:
                raise ValueError("Action contains no valid characters")
            
            event_data = EventData(
                event_type='user_engagement',
                user_id=validated_user_id,
                data={
                    'action': safe_action,
                    'page': additional_data.get('page') if additional_data else None,
                    'duration': additional_data.get('duration') if additional_data else None
                }
            )
            
            return self.track_event(event_data)
            
        except Exception as e:
            security_logger.error(f"Error tracking user engagement: {type(e).__name__}", extra={
                "user_id": user_id,
                "action": action
            })
            return self.validator.handle_secure_error(e)
    
    def update_user_kpis(self, user_id: str, date: datetime, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """
        Securely update user KPI records
        """
        try:
            # Validate parameters
            validated_user_id = self.validator.validate_user_id(user_id)
            
            if not isinstance(date, datetime):
                raise ValueError("Date must be a datetime object")
            
            # Check date range
            self.validator.validate_date_range(date, date)
            
            # Validate and sanitize metrics
            if not isinstance(metrics, dict):
                raise ValueError("Metrics must be a dictionary")
            
            sanitized_metrics = {}
            for key, value in metrics.items():
                # Only allow specific metric fields
                if key in ['pdfs_uploaded', 'defenses_generated', 'successful_defenses', 
                          'avg_processing_time', 'total_fine_amount', 'total_potential_savings',
                          'subscription_tier', 'session_count', 'avg_session_duration', 'feature_usage']:
                    
                    if key == 'subscription_tier' and isinstance(value, str):
                        # Validate subscription tier
                        if value in ['free', 'premium', 'enterprise']:
                            sanitized_metrics[key] = value
                    elif key == 'feature_usage' and isinstance(value, dict):
                        # Validate feature usage (must be JSON serializable)
                        sanitized_metrics[key] = self.validator.validate_event_data(value)
                    elif isinstance(value, (int, float)) and -1000000 <= value <= 1000000:
                        sanitized_metrics[key] = value
                    elif isinstance(value, int) and 0 <= value <= 1000000:
                        sanitized_metrics[key] = value
            
            # Use ORM query (SQL injection safe)
            kpi_record = self.db.query(UserKPI).filter(
                UserKPI.user_id == validated_user_id,
                UserKPI.date >= date.date(),
                UserKPI.date < date.date() + timedelta(days=1)
            ).first()
            
            if not kpi_record:
                kpi_record = UserKPI(user_id=validated_user_id, date=date.date())
                self.db.add(kpi_record)
            
            # Update metrics (only validated fields)
            for key, value in sanitized_metrics.items():
                setattr(kpi_record, key, value)
            
            self.db.commit()
            self.db.refresh(kpi_record)
            
            return {
                'success': True,
                'kpi_id': kpi_record.id
            }
            
        except Exception as e:
            self.db.rollback()
            security_logger.error(f"Error updating user KPIs: {type(e).__name__}", extra={
                "user_id": user_id,
                "date": date.isoformat() if isinstance(date, datetime) else None
            })
            return self.validator.handle_secure_error(e)
    
    def get_user_dashboard_data(self, user_id: str, days: int = 30) -> Dict[str, Any]:
        """
        Securely retrieve user dashboard data with input validation
        """
        try:
            # Validate parameters
            validated_user_id = self.validator.validate_user_id(user_id)
            
            if not isinstance(days, int) or days < 1 or days > 365:
                raise ValueError("Days must be an integer between 1 and 365")
            
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)
            
            # Secure date filtering using ORM
            events = self.db.query(AnalyticsEvent).filter(
                AnalyticsEvent.user_id == validated_user_id,
                AnalyticsEvent.timestamp >= start_date,
                AnalyticsEvent.timestamp <= end_date
            ).all()
            
            kpis = self.db.query(UserKPI).filter(
                UserKPI.user_id == validated_user_id,
                UserKPI.date >= start_date.date(),
                UserKPI.date <= end_date.date()
            ).all()
            
            # Aggregate data safely
            dashboard_data = {
                'user_id': validated_user_id,
                'period_days': days,
                'summary': {
                    'total_pdfs_uploaded': sum(
                        event.event_data.get('file_size', 0) 
                        for event in events 
                        if event.event_type == 'pdf_upload' and event.event_data
                    ),
                    'total_defenses_generated': len([e for e in events if e.event_type == 'defense_generated']),
                    'avg_processing_time': self._safe_average([
                        e.response_time for e in events if e.response_time
                    ]),
                    'success_rate': self._calculate_success_rate(events)
                },
                'daily_activity': self._aggregate_daily_activity(events),
                'feature_usage': self._get_feature_usage(events),
                'recent_events': [
                    event.to_dict() for event in sorted(events, key=lambda x: x.timestamp, reverse=True)[:10]
                ]
            }
            
            return dashboard_data
            
        except Exception as e:
            security_logger.error(f"Error getting user dashboard data: {type(e).__name__}", extra={
                "user_id": user_id,
                "days": days
            })
            return self.validator.handle_secure_error(e)
    
    def get_system_overview(self, hours: int = 24) -> Dict[str, Any]:
        """
        Securely retrieve system-wide analytics overview
        """
        try:
            # Validate parameters
            if not isinstance(hours, int) or hours < 1 or hours > 168:  # Max 1 week
                raise ValueError("Hours must be an integer between 1 and 168")
            
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(hours=hours)
            
            # Secure query using ORM
            events = self.db.query(AnalyticsEvent).filter(
                AnalyticsEvent.timestamp >= start_time,
                AnalyticsEvent.timestamp <= end_time
            ).all()
            
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
                    'avg_response_time': self._safe_average([
                        e.response_time for e in events if e.response_time
                    ]),
                    'error_rate': self._calculate_error_rate(events)
                },
                'hourly_breakdown': self._get_hourly_breakdown(events),
                'top_events': self._get_top_events(events),
                'system_health': system_kpis[0].to_dict() if system_kpis else None
            }
            
            return overview_data
            
        except Exception as e:
            security_logger.error(f"Error getting system overview: {type(e).__name__}", extra={
                "hours": hours
            })
            return self.validator.handle_secure_error(e)
    
    def _generate_session_id(self) -> str:
        """
        Generate unique session ID
        """
        import uuid
        return str(uuid.uuid4())
    
    def _check_rate_limit(self, identifier: str) -> bool:
        """
        Simple rate limiting implementation
        """
        now = datetime.utcnow().timestamp()
        window_start = now - self._rate_limit_window
        
        # Clean old entries
        self._rate_limits = {
            k: v for k, v in self._rate_limits.items() 
            if any(timestamp > window_start for timestamp in v)
        }
        
        # Check current user's requests
        user_requests = self._rate_limits.get(identifier, [])
        recent_requests = [timestamp for timestamp in user_requests if timestamp > window_start]
        
        if len(recent_requests) >= self._max_requests_per_window:
            security_logger.warning(f"Rate limit exceeded for {identifier}", extra={
                "requests_count": len(recent_requests),
                "limit": self._max_requests_per_window
            })
            return False
        
        # Add current request
        recent_requests.append(now)
        self._rate_limits[identifier] = recent_requests
        
        return True
    
    def _safe_average(self, values: List[float]) -> float:
        """
        Safely calculate average with empty list handling
        """
        if not values:
            return 0.0
        return sum(values) / len(values)
    
    def _calculate_success_rate(self, events: List[AnalyticsEvent]) -> float:
        """
        Calculate success rate safely
        """
        if not events:
            return 0.0
        successful = sum(1 for event in events if event.success)
        return (successful / len(events)) * 100
    
    def _calculate_error_rate(self, events: List[AnalyticsEvent]) -> float:
        """
        Calculate error rate safely
        """
        if not events:
            return 0.0
        errors = sum(1 for event in events if not event.success)
        return (errors / len(events)) * 100
    
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
            # Note: Not removing the set here to keep the count as 'unique_sessions'
        
        return sorted(daily_data.values(), key=lambda x: x['date'])
    
    def _get_feature_usage(self, events: List[AnalyticsEvent]) -> Dict[str, int]:
        """
        Get feature usage statistics
        """
        feature_usage = {}
        
        for event in events:
            if event.event_type == 'user_engagement' and event.event_data:
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
            avg_time = self._safe_average(hour_data['response_times'])
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
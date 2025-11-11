"""
User Feedback Collection and Analysis Framework
Comprehensive system for collecting, analyzing, and acting on user feedback
"""

import os
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union, Any
from dataclasses import dataclass, asdict
from enum import Enum
from sqlalchemy.orm import Session
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class FeedbackType(Enum):
    """Types of user feedback"""
    GENERAL = "general"
    BUG_REPORT = "bug_report"
    FEATURE_REQUEST = "feature_request"
    DEFENSE_QUALITY = "defense_quality"
    PDF_PROCESSING = "pdf_processing"
    USER_EXPERIENCE = "user_experience"
    PRICING = "pricing"
    PERFORMANCE = "performance"


class FeedbackPriority(Enum):
    """Priority levels for feedback"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class FeedbackStatus(Enum):
    """Status of feedback processing"""
    NEW = "new"
    ACKNOWLEDGED = "acknowledged"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"


class UserFeedback(Base):
    """
    Database model for user feedback
    """
    __tablename__ = "user_feedback"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True)
    feedback_type = Column(String, index=True)  # Using string to store enum
    priority = Column(String, index=True, default="medium")
    status = Column(String, index=True, default="new")
    
    # Content
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    category = Column(String)  # Detailed categorization
    tags = Column(JSON)  # List of tags for categorization
    
    # Context
    page_url = Column(String)
    user_agent = Column(Text)
    session_id = Column(String, index=True)
    browser_info = Column(JSON)
    
    # Related objects
    fine_id = Column(Integer, ForeignKey("fines.id"), nullable=True)
    defense_id = Column(Integer, ForeignKey("defenses.id"), nullable=True)
    
    # Ratings (1-5 scale)
    overall_rating = Column(Integer)  # 1-5 stars
    defense_quality_rating = Column(Integer)  # 1-5 stars
    user_experience_rating = Column(Integer)  # 1-5 stars
    performance_rating = Column(Integer)  # 1-5 stars
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)
    
    # Admin notes
    internal_notes = Column(Text)
    resolution_notes = Column(Text)
    
    # Relationships
    fine = relationship("Fine", foreign_keys=[fine_id])
    defense = relationship("Defense", foreign_keys=[defense_id])
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'feedback_type': self.feedback_type,
            'priority': self.priority,
            'status': self.status,
            'title': self.title,
            'description': self.description,
            'category': self.category,
            'tags': self.tags or [],
            'page_url': self.page_url,
            'session_id': self.session_id,
            'browser_info': self.browser_info,
            'fine_id': self.fine_id,
            'defense_id': self.defense_id,
            'overall_rating': self.overall_rating,
            'defense_quality_rating': self.defense_quality_rating,
            'user_experience_rating': self.user_experience_rating,
            'performance_rating': self.performance_rating,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None,
            'internal_notes': self.internal_notes,
            'resolution_notes': self.resolution_notes
        }


class FeedbackAnalysis(Base):
    """
    Database model for feedback analysis and insights
    """
    __tablename__ = "feedback_analysis"
    
    id = Column(Integer, primary_key=True, index=True)
    analysis_date = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Time period analyzed
    period_start = Column(DateTime)
    period_end = Column(DateTime)
    
    # Summary statistics
    total_feedback_count = Column(Integer)
    feedback_by_type = Column(JSON)  # {feedback_type: count}
    feedback_by_priority = Column(JSON)  # {priority: count}
    feedback_by_status = Column(JSON)  # {status: count}
    
    # Ratings analysis
    avg_overall_rating = Column(Float)
    avg_defense_quality_rating = Column(Float)
    avg_user_experience_rating = Column(Float)
    avg_performance_rating = Column(Float)
    
    # Content analysis
    common_keywords = Column(JSON)  # List of frequent terms
    sentiment_analysis = Column(JSON)  # Sentiment scores
    top_categories = Column(JSON)  # Most common categories
    recurring_issues = Column(JSON)  # Frequently reported issues
    
    # Action items
    action_items = Column(JSON)  # Suggested improvements
    priority_issues = Column(JSON)  # High-priority items requiring attention
    
    # Trends
    improvement_trends = Column(JSON)  # Rating trends over time
    volume_trends = Column(JSON)  # Feedback volume trends
    
    def to_dict(self):
        return {
            'id': self.id,
            'analysis_date': self.analysis_date.isoformat(),
            'period_start': self.period_start.isoformat() if self.period_start else None,
            'period_end': self.period_end.isoformat() if self.period_end else None,
            'total_feedback_count': self.total_feedback_count,
            'feedback_by_type': self.feedback_by_type,
            'feedback_by_priority': self.feedback_by_priority,
            'feedback_by_status': self.feedback_by_status,
            'avg_overall_rating': self.avg_overall_rating,
            'avg_defense_quality_rating': self.avg_defense_quality_rating,
            'avg_user_experience_rating': self.avg_user_experience_rating,
            'avg_performance_rating': self.avg_performance_rating,
            'common_keywords': self.common_keywords,
            'sentiment_analysis': self.sentiment_analysis,
            'top_categories': self.top_categories,
            'recurring_issues': self.recurring_issues,
            'action_items': self.action_items,
            'priority_issues': self.priority_issues,
            'improvement_trends': self.improvement_trends,
            'volume_trends': self.volume_trends
        }


@dataclass
class FeedbackSubmission:
    """
    Standardized feedback submission structure
    """
    user_id: str
    feedback_type: str
    title: str
    description: str
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    page_url: Optional[str] = None
    session_id: Optional[str] = None
    fine_id: Optional[int] = None
    defense_id: Optional[int] = None
    overall_rating: Optional[int] = None
    defense_quality_rating: Optional[int] = None
    user_experience_rating: Optional[int] = None
    performance_rating: Optional[int] = None


class FeedbackService:
    """
    Comprehensive user feedback collection and analysis service
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def submit_feedback(self, feedback: FeedbackSubmission) -> Dict[str, Any]:
        """
        Submit user feedback
        """
        try:
            # Create feedback record
            feedback_record = UserFeedback(
                user_id=feedback.user_id,
                feedback_type=feedback.feedback_type,
                title=feedback.title,
                description=feedback.description,
                category=feedback.category,
                tags=feedback.tags or [],
                page_url=feedback.page_url,
                session_id=feedback.session_id,
                fine_id=feedback.fine_id,
                defense_id=feedback.defense_id,
                overall_rating=feedback.overall_rating,
                defense_quality_rating=feedback.defense_quality_rating,
                user_experience_rating=feedback.user_experience_rating,
                performance_rating=feedback.performance_rating,
                created_at=datetime.utcnow()
            )
            
            self.db.add(feedback_record)
            self.db.commit()
            self.db.refresh(feedback_record)
            
            # Auto-categorize and set priority based on content
            self._auto_categorize_feedback(feedback_record)
            
            # Trigger immediate analysis for high-priority feedback
            if feedback_record.priority in ['high', 'critical']:
                self._trigger_immediate_analysis(feedback_record)
            
            return {
                'success': True,
                'feedback_id': feedback_record.id,
                'priority_assigned': feedback_record.priority,
                'estimated_response_time': self._get_response_time(feedback_record.priority)
            }
            
        except Exception as e:
            self.db.rollback()
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_feedback_dashboard(self, days: int = 30, feedback_type: Optional[str] = None) -> Dict[str, Any]:
        """
        Get comprehensive feedback dashboard data
        """
        try:
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)
            
            # Base query
            query = self.db.query(UserFeedback).filter(
                UserFeedback.created_at >= start_date,
                UserFeedback.created_at <= end_date
            )
            
            if feedback_type:
                query = query.filter(UserFeedback.feedback_type == feedback_type)
            
            feedback_records = query.order_by(UserFeedback.created_at.desc()).all()
            
            # Calculate statistics
            total_feedback = len(feedback_records)
            by_type = {}
            by_priority = {}
            by_status = {}
            
            ratings = {
                'overall': [],
                'defense_quality': [],
                'user_experience': [],
                'performance': []
            }
            
            for feedback in feedback_records:
                # Count by categories
                by_type[feedback.feedback_type] = by_type.get(feedback.feedback_type, 0) + 1
                by_priority[feedback.priority] = by_priority.get(feedback.priority, 0) + 1
                by_status[feedback.status] = by_status.get(feedback.status, 0) + 1
                
                # Collect ratings
                if feedback.overall_rating:
                    ratings['overall'].append(feedback.overall_rating)
                if feedback.defense_quality_rating:
                    ratings['defense_quality'].append(feedback.defense_quality_rating)
                if feedback.user_experience_rating:
                    ratings['user_experience'].append(feedback.user_experience_rating)
                if feedback.performance_rating:
                    ratings['performance'].append(feedback.performance_rating)
            
            # Calculate averages
            avg_ratings = {}
            for rating_type, rating_values in ratings.items():
                avg_ratings[rating_type] = sum(rating_values) / len(rating_values) if rating_values else 0
            
            # Get recent feedback
            recent_feedback = [f.to_dict() for f in feedback_records[:10]]
            
            # Get high-priority items
            high_priority = [f.to_dict() for f in feedback_records if f.priority in ['high', 'critical'] and f.status != 'resolved'][:5]
            
            return {
                'period_days': days,
                'summary': {
                    'total_feedback': total_feedback,
                    'feedback_by_type': by_type,
                    'feedback_by_priority': by_priority,
                    'feedback_by_status': by_status,
                    'avg_ratings': avg_ratings
                },
                'recent_feedback': recent_feedback,
                'high_priority_items': high_priority,
                'trends': self._calculate_feedback_trends(feedback_records, days)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def analyze_feedback(self, days: int = 7) -> Dict[str, Any]:
        """
        Perform comprehensive feedback analysis
        """
        try:
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)
            
            # Get feedback for analysis period
            feedback_records = self.db.query(UserFeedback).filter(
                UserFeedback.created_at >= start_date,
                UserFeedback.created_at <= end_date
            ).all()
            
            # Create analysis record
            analysis = FeedbackAnalysis(
                analysis_date=datetime.utcnow(),
                period_start=start_date,
                period_end=end_date,
                total_feedback_count=len(feedback_records)
            )
            
            # Analyze by type
            by_type = {}
            for feedback in feedback_records:
                feedback_type = feedback.feedback_type
                by_type[feedback_type] = by_type.get(feedback_type, 0) + 1
            analysis.feedback_by_type = by_type
            
            # Analyze ratings
            ratings = {
                'overall': [],
                'defense_quality': [],
                'user_experience': [],
                'performance': []
            }
            
            for feedback in feedback_records:
                if feedback.overall_rating:
                    ratings['overall'].append(feedback.overall_rating)
                if feedback.defense_quality_rating:
                    ratings['defense_quality'].append(feedback.defense_quality_rating)
                if feedback.user_experience_rating:
                    ratings['user_experience'].append(feedback.user_experience_rating)
                if feedback.performance_rating:
                    ratings['performance'].append(feedback.performance_rating)
            
            # Calculate averages
            analysis.avg_overall_rating = sum(ratings['overall']) / len(ratings['overall']) if ratings['overall'] else 0
            analysis.avg_defense_quality_rating = sum(ratings['defense_quality']) / len(ratings['defense_quality']) if ratings['defense_quality'] else 0
            analysis.avg_user_experience_rating = sum(ratings['user_experience']) / len(ratings['user_experience']) if ratings['user_experience'] else 0
            analysis.avg_performance_rating = sum(ratings['performance']) / len(ratings['performance']) if ratings['performance'] else 0
            
            # Extract keywords (simplified)
            keywords = self._extract_keywords([f.description for f in feedback_records])
            analysis.common_keywords = keywords
            
            # Identify recurring issues
            analysis.recurring_issues = self._identify_recurring_issues(feedback_records)
            
            # Generate action items
            analysis.action_items = self._generate_action_items(feedback_records)
            
            # Identify priority issues
            analysis.priority_issues = [f.title for f in feedback_records if f.priority in ['high', 'critical'] and f.status != 'resolved'][:10]
            
            # Save analysis
            self.db.add(analysis)
            self.db.commit()
            self.db.refresh(analysis)
            
            return {
                'success': True,
                'analysis_id': analysis.id,
                'analysis': analysis.to_dict()
            }
            
        except Exception as e:
            self.db.rollback()
            return {
                'success': False,
                'error': str(e)
            }
    
    def update_feedback_status(self, feedback_id: int, status: str, notes: Optional[str] = None) -> Dict[str, Any]:
        """
        Update feedback status and add notes
        """
        try:
            feedback = self.db.query(UserFeedback).filter(UserFeedback.id == feedback_id).first()
            
            if not feedback:
                return {
                    'success': False,
                    'error': 'Feedback not found'
                }
            
            feedback.status = status
            feedback.updated_at = datetime.utcnow()
            
            if notes:
                if status == 'resolved':
                    feedback.resolution_notes = notes
                else:
                    feedback.internal_notes = notes
            
            if status == 'resolved':
                feedback.resolved_at = datetime.utcnow()
            
            self.db.commit()
            
            return {
                'success': True,
                'feedback_id': feedback_id,
                'new_status': status,
                'updated_at': feedback.updated_at.isoformat()
            }
            
        except Exception as e:
            self.db.rollback()
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_user_feedback_history(self, user_id: str, limit: int = 20) -> Dict[str, Any]:
        """
        Get user's feedback history
        """
        try:
            feedback_records = self.db.query(UserFeedback).filter(
                UserFeedback.user_id == user_id
            ).order_by(UserFeedback.created_at.desc()).limit(limit).all()
            
            return {
                'success': True,
                'user_id': user_id,
                'total_feedback': len(feedback_records),
                'feedback_history': [f.to_dict() for f in feedback_records],
                'avg_ratings': self._calculate_user_avg_ratings(feedback_records)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _auto_categorize_feedback(self, feedback: UserFeedback):
        """
        Auto-categorize feedback based on content and set priority
        """
        title_lower = feedback.title.lower()
        desc_lower = feedback.description.lower()
        content = f"{title_lower} {desc_lower}"
        
        # Auto-categorize based on keywords
        if any(word in content for word in ['bug', 'error', 'broken', 'not working']):
            feedback.feedback_type = FeedbackType.BUG_REPORT.value
            feedback.priority = FeedbackPriority.HIGH.value
        elif any(word in content for word in ['feature', 'add', 'improvement', 'enhancement']):
            feedback.feedback_type = FeedbackType.FEATURE_REQUEST.value
            feedback.priority = FeedbackPriority.MEDIUM.value
        elif any(word in content for word in ['slow', 'fast', 'performance', 'speed']):
            feedback.feedback_type = FeedbackType.PERFORMANCE.value
            feedback.priority = FeedbackPriority.MEDIUM.value
        elif any(word in content for word in ['quality', 'accurate', 'wrong', 'incorrect']):
            feedback.feedback_type = FeedbackType.DEFENSE_QUALITY.value
            feedback.priority = FeedbackPriority.HIGH.value
        else:
            feedback.feedback_type = FeedbackType.GENERAL.value
            feedback.priority = FeedbackPriority.MEDIUM.value
    
    def _trigger_immediate_analysis(self, feedback: UserFeedback):
        """
        Trigger immediate analysis for high-priority feedback
        """
        # In a real implementation, this might trigger alerts or notifications
        print(f"High-priority feedback received: {feedback.title}")
    
    def _get_response_time(self, priority: str) -> str:
        """
        Get expected response time based on priority
        """
        response_times = {
            'critical': '2 hours',
            'high': '24 hours',
            'medium': '3 days',
            'low': '1 week'
        }
        return response_times.get(priority, '3 days')
    
    def _calculate_feedback_trends(self, feedback_records: List[UserFeedback], days: int) -> Dict[str, Any]:
        """
        Calculate feedback trends over time
        """
        # Simple trend analysis - group by day
        daily_counts = {}
        daily_ratings = {}
        
        for feedback in feedback_records:
            day = feedback.created_at.date().isoformat()
            
            # Count feedback per day
            daily_counts[day] = daily_counts.get(day, 0) + 1
            
            # Average ratings per day
            if feedback.overall_rating:
                if day not in daily_ratings:
                    daily_ratings[day] = []
                daily_ratings[day].append(feedback.overall_rating)
        
        # Calculate averages
        avg_daily_ratings = {}
        for day, ratings in daily_ratings.items():
            avg_daily_ratings[day] = sum(ratings) / len(ratings)
        
        return {
            'daily_feedback_counts': daily_counts,
            'daily_avg_ratings': avg_daily_ratings
        }
    
    def _extract_keywords(self, texts: List[str]) -> List[str]:
        """
        Extract common keywords from feedback text (simplified implementation)
        """
        # Simple keyword extraction - in production, use NLP libraries
        all_words = []
        for text in texts:
            words = text.lower().split()
            # Filter out common words and short words
            filtered_words = [w for w in words if len(w) > 3 and w not in ['this', 'that', 'with', 'have', 'will', 'been', 'from', 'they', 'know', 'want', 'been', 'good', 'much', 'some', 'time']]
            all_words.extend(filtered_words)
        
        # Count word frequency
        word_counts = {}
        for word in all_words:
            word_counts[word] = word_counts.get(word, 0) + 1
        
        # Return top 10 most common words
        return sorted(word_counts.items(), key=lambda x: x[1], reverse=True)[:10]
    
    def _identify_recurring_issues(self, feedback_records: List[UserFeedback]) -> List[str]:
        """
        Identify recurring issues from feedback
        """
        # Group similar feedback by title similarity
        issues = {}
        for feedback in feedback_records:
            if feedback.feedback_type == FeedbackType.BUG_REPORT.value:
                # Simple similarity check - in production, use better similarity algorithms
                title_words = set(feedback.title.lower().split())
                
                found_similar = False
                for existing_issue in issues:
                    existing_words = set(existing_issue.lower().split())
                    similarity = len(title_words.intersection(existing_words)) / len(title_words.union(existing_words))
                    
                    if similarity > 0.5:  # 50% similarity threshold
                        issues[existing_issue] += 1
                        found_similar = True
                        break
                
                if not found_similar:
                    issues[feedback.title] = 1
        
        # Return issues that appear multiple times
        return [issue for issue, count in issues.items() if count > 1]
    
    def _generate_action_items(self, feedback_records: List[UserFeedback]) -> List[str]:
        """
        Generate action items based on feedback analysis
        """
        action_items = []
        
        # High-priority feedback
        high_priority_count = len([f for f in feedback_records if f.priority in ['high', 'critical']])
        if high_priority_count > 5:
            action_items.append(f"Address {high_priority_count} high-priority feedback items")
        
        # Low ratings
        low_ratings_count = len([f for f in feedback_records if f.overall_rating and f.overall_rating <= 2])
        if low_ratings_count > 3:
            action_items.append(f"Improve user experience - {low_ratings_count} users gave low ratings")
        
        # Performance issues
        performance_issues = len([f for f in feedback_records if 'performance' in f.feedback_type or 'slow' in f.description.lower()])
        if performance_issues > 2:
            action_items.append(f"Optimize system performance - {performance_issues} performance-related feedback")
        
        return action_items
    
    def _calculate_user_avg_ratings(self, feedback_records: List[UserFeedback]) -> Dict[str, float]:
        """
        Calculate average ratings for a user
        """
        ratings = {
            'overall': [],
            'defense_quality': [],
            'user_experience': [],
            'performance': []
        }
        
        for feedback in feedback_records:
            if feedback.overall_rating:
                ratings['overall'].append(feedback.overall_rating)
            if feedback.defense_quality_rating:
                ratings['defense_quality'].append(feedback.defense_quality_rating)
            if feedback.user_experience_rating:
                ratings['user_experience'].append(feedback.user_experience_rating)
            if feedback.performance_rating:
                ratings['performance'].append(feedback.performance_rating)
        
        return {
            rating_type: sum(rating_list) / len(rating_list) if rating_list else 0
            for rating_type, rating_list in ratings.items()
        }
"""
Analytics service tests.

This module tests the comprehensive analytics tracking system including:
- Event tracking and data storage
- KPI calculation and aggregation
- User dashboard data generation
- System overview metrics
- Performance monitoring
"""

import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta, date
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from ..conftest import mock_analytics_service
from services.analytics_service import (
    AnalyticsService, EventData, AnalyticsEvent, UserKPI, SystemKPI
)


@pytest.mark.analytics
@pytest.mark.services
class TestAnalyticsEvent:
    """Test suite for AnalyticsEvent model."""
    
    def test_analytics_event_creation(self):
        """Test creating an analytics event."""
        event = AnalyticsEvent(
            event_type="pdf_upload",
            user_id="user123",
            session_id="session456",
            event_data={"file_size": 1024},
            timestamp=datetime.utcnow(),
            ip_address="192.168.1.1",
            user_agent="Mozilla/5.0",
            referrer="https://example.com",
            response_time=1.5,
            success=True
        )
        
        assert event.event_type == "pdf_upload"
        assert event.user_id == "user123"
        assert event.session_id == "session456"
        assert event.event_data == {"file_size": 1024}
        assert event.response_time == 1.5
        assert event.success is True
    
    def test_analytics_event_to_dict(self):
        """Test converting analytics event to dictionary."""
        timestamp = datetime.utcnow()
        event = AnalyticsEvent(
            event_type="defense_generated",
            user_id="user123",
            session_id="session456",
            event_data={"fine_amount": 150.0},
            timestamp=timestamp,
            ip_address="192.168.1.1",
            response_time=2.0,
            success=True
        )
        
        event_dict = event.to_dict()
        
        assert event_dict["event_type"] == "defense_generated"
        assert event_dict["user_id"] == "user123"
        assert event_dict["session_id"] == "session456"
        assert event_dict["event_data"] == {"fine_amount": 150.0}
        assert event_dict["response_time"] == 2.0
        assert event_dict["success"] is True
        assert event_dict["timestamp"] == timestamp.isoformat()


@pytest.mark.analytics
@pytest.mark.services
class TestUserKPI:
    """Test suite for UserKPI model."""
    
    def test_user_kpi_creation(self):
        """Test creating a user KPI record."""
        kpi = UserKPI(
            user_id="user123",
            date=date.today(),
            pdfs_uploaded=5,
            defenses_generated=3,
            successful_defenses=2,
            avg_processing_time=1.5,
            total_fine_amount=450.0,
            total_potential_savings=300.0,
            subscription_tier="premium",
            session_count=10,
            avg_session_duration=25.5,
            feature_usage={"pdf_upload": 5, "defense_gen": 3}
        )
        
        assert kpi.user_id == "user123"
        assert kpi.pdfs_uploaded == 5
        assert kpi.defenses_generated == 3
        assert kpi.successful_defenses == 2
        assert kpi.total_fine_amount == 450.0
        assert kpi.subscription_tier == "premium"
    
    def test_user_kpi_to_dict(self):
        """Test converting user KPI to dictionary."""
        test_date = date(2025, 11, 11)
        kpi = UserKPI(
            user_id="user123",
            date=test_date,
            pdfs_uploaded=2,
            defenses_generated=1,
            subscription_tier="free"
        )
        
        kpi_dict = kpi.to_dict()
        
        assert kpi_dict["user_id"] == "user123"
        assert kpi_dict["date"] == "2025-11-11"
        assert kpi_dict["pdfs_uploaded"] == 2
        assert kpi_dict["defenses_generated"] == 1
        assert kpi_dict["subscription_tier"] == "free"


@pytest.mark.analytics
@pytest.mark.services
class TestSystemKPI:
    """Test suite for SystemKPI model."""
    
    def test_system_kpi_creation(self):
        """Test creating a system KPI record."""
        kpi = SystemKPI(
            timestamp=datetime.utcnow(),
            avg_response_time=0.8,
            request_count=1000,
            error_rate=2.5,
            success_rate=97.5,
            cpu_usage=45.2,
            memory_usage=1024.5,
            disk_usage=60.0,
            total_pdfs_processed=50,
            total_defenses_generated=30,
            active_users_24h=25,
            active_users_7d=150,
            active_users_30d=500
        )
        
        assert kpi.avg_response_time == 0.8
        assert kpi.request_count == 1000
        assert kpi.error_rate == 2.5
        assert kpi.success_rate == 97.5
        assert kpi.total_pdfs_processed == 50
        assert kpi.active_users_24h == 25
    
    def test_system_kpi_to_dict(self):
        """Test converting system KPI to dictionary."""
        timestamp = datetime.utcnow()
        kpi = SystemKPI(
            timestamp=timestamp,
            avg_response_time=1.0,
            request_count=500,
            error_rate=1.0
        )
        
        kpi_dict = kpi.to_dict()
        
        assert kpi_dict["avg_response_time"] == 1.0
        assert kpi_dict["request_count"] == 500
        assert kpi_dict["error_rate"] == 1.0
        assert kpi_dict["timestamp"] == timestamp.isoformat()


@pytest.mark.analytics
@pytest.mark.services
class TestEventData:
    """Test suite for EventData dataclass."""
    
    def test_event_data_creation(self):
        """Test creating EventData objects."""
        event = EventData(
            event_type="pdf_upload",
            user_id="user123",
            session_id="session456",
            data={"file_size": 1024},
            response_time=1.5,
            success=True,
            error_message=None
        )
        
        assert event.event_type == "pdf_upload"
        assert event.user_id == "user123"
        assert event.session_id == "session456"
        assert event.data == {"file_size": 1024}
        assert event.response_time == 1.5
        assert event.success is True
        assert event.error_message is None
    
    def test_event_data_minimal(self):
        """Test creating EventData with minimal required fields."""
        event = EventData(
            event_type="page_view"
        )
        
        assert event.event_type == "page_view"
        assert event.user_id is None
        assert event.session_id is None
        assert event.data is None
        assert event.response_time is None
        assert event.success is True  # Default value
        assert event.error_message is None


@pytest.mark.analytics
@pytest.mark.services
class TestAnalyticsService:
    """Test suite for AnalyticsService class."""
    
    @pytest.fixture
    def test_db_session(self):
        """Create a test database session."""
        engine = create_engine("sqlite:///:memory:")
        from services.analytics_service import Base
        Base.metadata.create_all(bind=engine)
        SessionLocal = sessionmaker(bind=engine)
        session = SessionLocal()
        yield session
        session.close()
    
    def test_init_analytics_service(self, test_db_session):
        """Test initializing analytics service."""
        service = AnalyticsService(test_db_session)
        
        assert service.db == test_db_session
        assert service.session_id is not None
        assert isinstance(service.session_id, str)
        assert len(service.session_id) > 0
    
    def test_track_event_success(self, test_db_session):
        """Test successful event tracking."""
        service = AnalyticsService(test_db_session)
        
        event_data = EventData(
            event_type="pdf_upload",
            user_id="user123",
            session_id="session456",
            data={"file_size": 1024},
            response_time=1.5,
            success=True
        )
        
        result = service.track_event(event_data)
        
        assert result["success"] is True
        assert "event_id" in result
        assert "timestamp" in result
        assert isinstance(result["event_id"], int)
        
        # Verify event was stored in database
        stored_event = test_db_session.query(AnalyticsEvent).first()
        assert stored_event is not None
        assert stored_event.event_type == "pdf_upload"
        assert stored_event.user_id == "user123"
        assert stored_event.session_id == "session456"
    
    def test_track_event_failure(self, test_db_session):
        """Test event tracking with database failure."""
        service = AnalyticsService(test_db_session)
        
        # Mock database rollback
        test_db_session.rollback = MagicMock()
        test_db_session.add = MagicMock(side_effect=Exception("DB Error"))
        
        event_data = EventData(event_type="test_event")
        result = service.track_event(event_data)
        
        assert result["success"] is False
        assert "error" in result
        assert "DB Error" in result["error"]
    
    def test_track_pdf_upload(self, test_db_session):
        """Test PDF upload tracking."""
        service = AnalyticsService(test_db_session)
        
        result = service.track_pdf_upload(
            user_id="user123",
            file_size=2048,
            processing_time=2.0,
            success=True
        )
        
        assert result["success"] is True
        assert "event_id" in result
        
        # Verify event details
        stored_event = test_db_session.query(AnalyticsEvent).first()
        assert stored_event.event_type == "pdf_upload"
        assert stored_event.user_id == "user123"
        assert stored_event.event_data["file_size"] == 2048
        assert stored_event.response_time == 2.0
        assert stored_event.success is True
    
    def test_track_defense_generation(self, test_db_session):
        """Test defense generation tracking."""
        service = AnalyticsService(test_db_session)
        
        fine_data = {
            "fine_amount": 150.0,
            "infraction_code": "ART135-1-A"
        }
        
        result = service.track_defense_generation(
            user_id="user123",
            fine_data=fine_data,
            processing_time=3.0,
            success=True
        )
        
        assert result["success"] is True
        
        # Verify event details
        stored_event = test_db_session.query(AnalyticsEvent).first()
        assert stored_event.event_type == "defense_generated"
        assert stored_event.user_id == "user123"
        assert stored_event.event_data["fine_amount"] == 150.0
        assert stored_event.event_data["infraction_code"] == "ART135-1-A"
    
    def test_track_user_engagement(self, test_db_session):
        """Test user engagement tracking."""
        service = AnalyticsService(test_db_session)
        
        additional_data = {
            "page": "/dashboard",
            "duration": 120
        }
        
        result = service.track_user_engagement(
            user_id="user123",
            action="page_view",
            additional_data=additional_data
        )
        
        assert result["success"] is True
        
        # Verify event details
        stored_event = test_db_session.query(AnalyticsEvent).first()
        assert stored_event.event_type == "user_engagement"
        assert stored_event.user_id == "user123"
        assert stored_event.event_data["action"] == "page_view"
        assert stored_event.event_data["page"] == "/dashboard"
        assert stored_event.event_data["duration"] == 120
    
    def test_update_user_kpis_new_record(self, test_db_session):
        """Test creating new user KPI record."""
        service = AnalyticsService(test_db_session)
        
        metrics = {
            "pdfs_uploaded": 3,
            "defenses_generated": 2,
            "total_fine_amount": 300.0,
            "subscription_tier": "premium"
        }
        
        result = service.update_user_kpis(
            user_id="user123",
            date=datetime.utcnow(),
            metrics=metrics
        )
        
        assert result["success"] is True
        assert "kpi_id" in result
        
        # Verify KPI was created
        kpi = test_db_session.query(UserKPI).first()
        assert kpi is not None
        assert kpi.user_id == "user123"
        assert kpi.pdfs_uploaded == 3
        assert kpi.defenses_generated == 2
        assert kpi.total_fine_amount == 300.0
    
    def test_update_user_kpis_existing_record(self, test_db_session):
        """Test updating existing user KPI record."""
        service = AnalyticsService(test_db_session)
        
        # Create initial KPI
        initial_metrics = {
            "pdfs_uploaded": 1,
            "defenses_generated": 1
        }
        service.update_user_kpis("user123", datetime.utcnow(), initial_metrics)
        
        # Update with additional metrics
        update_metrics = {
            "pdfs_uploaded": 2,
            "defenses_generated": 2,
            "total_fine_amount": 200.0
        }
        result = service.update_user_kpis("user123", datetime.utcnow(), update_metrics)
        
        assert result["success"] is True
        
        # Verify KPI was updated (not duplicated)
        kpis = test_db_session.query(UserKPI).filter(UserKPI.user_id == "user123").all()
        assert len(kpis) == 1
        assert kpis[0].pdfs_uploaded == 2
        assert kpis[0].defenses_generated == 2
        assert kpis[0].total_fine_amount == 200.0
    
    def test_get_user_dashboard_data(self, test_db_session):
        """Test generating user dashboard data."""
        service = AnalyticsService(test_db_session)
        
        # Add sample events
        base_time = datetime.utcnow() - timedelta(days=5)
        for i in range(5):
            event = AnalyticsEvent(
                event_type="pdf_upload",
                user_id="user123",
                session_id=f"session{i}",
                event_data={"file_size": 1024 * (i + 1)},
                timestamp=base_time + timedelta(days=i),
                response_time=1.0 + i * 0.1,
                success=True
            )
            test_db_session.add(event)
        
        test_db_session.commit()
        
        dashboard_data = service.get_user_dashboard_data("user123", days=7)
        
        assert dashboard_data["user_id"] == "user123"
        assert dashboard_data["period_days"] == 7
        assert "summary" in dashboard_data
        assert "daily_activity" in dashboard_data
        assert "feature_usage" in dashboard_data
        assert "recent_events" in dashboard_data
        
        summary = dashboard_data["summary"]
        assert summary["total_pdfs_uploaded"] == 1024 * 15  # Sum of all file sizes
        assert summary["total_defenses_generated"] == 0  # No defense events
        assert summary["success_rate"] == 100.0  # All events successful
    
    def test_get_system_overview(self, test_db_session):
        """Test generating system overview."""
        service = AnalyticsService(test_db_session)
        
        # Add sample system events
        base_time = datetime.utcnow() - timedelta(hours=2)
        for i in range(10):
            event = AnalyticsEvent(
                event_type="pdf_upload",
                user_id=f"user{i}",
                session_id=f"session{i}",
                timestamp=base_time + timedelta(minutes=i * 10),
                response_time=1.0 + i * 0.1,
                success=True if i < 9 else False  # One failure
            )
            test_db_session.add(event)
        
        test_db_session.commit()
        
        overview = service.get_system_overview(hours=3)
        
        assert overview["period_hours"] == 3
        assert "summary" in overview
        assert "hourly_breakdown" in overview
        assert "top_events" in overview
        assert "system_health" in overview
        
        summary = overview["summary"]
        assert summary["total_events"] == 10
        assert summary["unique_users"] == 10
        assert summary["pdfs_processed"] == 10
        assert summary["error_rate"] == 10.0  # 1 failure out of 10 events
        assert summary["success_rate"] == 90.0
    
    def test_generate_session_id(self, test_db_session):
        """Test session ID generation."""
        service = AnalyticsService(test_db_session)
        
        session_id = service._generate_session_id()
        
        assert isinstance(session_id, str)
        assert len(session_id) > 0
        assert len(session_id.split('-')) >= 4  # UUID format
    
    def test_aggregate_daily_activity(self, test_db_session):
        """Test daily activity aggregation."""
        service = AnalyticsService(test_db_session)
        
        # Create sample events for multiple days
        events = []
        for day in range(3):
            date_obj = datetime.utcnow() - timedelta(days=day)
            
            # Create different types of events
            for event_type in ["pdf_upload", "defense_generated"]:
                event = AnalyticsEvent(
                    event_type=event_type,
                    user_id="user123",
                    session_id=f"session_{day}_{event_type}",
                    timestamp=date_obj,
                    success=True
                )
                events.append(event)
        
        daily_activity = service._aggregate_daily_activity(events)
        
        assert len(daily_activity) >= 1
        for day_data in daily_activity:
            assert "date" in day_data
            assert "pdfs_uploaded" in day_data
            assert "defenses_generated" in day_data
            assert "total_events" in day_data
            assert day_data["pdfs_uploaded"] >= 0
            assert day_data["defenses_generated"] >= 0
    
    def test_get_feature_usage(self, test_db_session):
        """Test feature usage statistics."""
        service = AnalyticsService(test_db_session)
        
        # Create user engagement events
        engagement_events = [
            AnalyticsEvent(
                event_type="user_engagement",
                event_data={"action": "page_view"},
                user_id="user1",
                timestamp=datetime.utcnow()
            ),
            AnalyticsEvent(
                event_type="user_engagement",
                event_data={"action": "pdf_upload"},
                user_id="user1",
                timestamp=datetime.utcnow()
            ),
            AnalyticsEvent(
                event_type="user_engagement",
                event_data={"action": "page_view"},
                user_id="user2",
                timestamp=datetime.utcnow()
            )
        ]
        
        feature_usage = service._get_feature_usage(engagement_events)
        
        assert feature_usage["page_view"] == 2
        assert feature_usage["pdf_upload"] == 1
        assert "defense_gen" not in feature_usage  # Not present in test data


@pytest.mark.analytics
@pytest.mark.integration
class TestAnalyticsIntegration:
    """Integration tests for analytics service."""
    
    def test_full_analytics_workflow(self, test_db_session):
        """Test complete analytics workflow."""
        service = AnalyticsService(test_db_session)
        
        # 1. Track multiple events
        service.track_pdf_upload("user123", 1024, 1.5, True)
        service.track_defense_generation("user123", {"fine_amount": 150.0}, 2.0, True)
        service.track_user_engagement("user123", "page_view", {"page": "/dashboard"})
        
        # 2. Update user KPIs
        service.update_user_kpis("user123", datetime.utcnow(), {
            "pdfs_uploaded": 1,
            "defenses_generated": 1,
            "total_fine_amount": 150.0
        })
        
        # 3. Generate dashboard data
        dashboard = service.get_user_dashboard_data("user123", days=1)
        
        assert dashboard["summary"]["total_pdfs_uploaded"] == 1024
        assert dashboard["summary"]["total_defenses_generated"] == 1
        assert dashboard["summary"]["success_rate"] == 100.0
        
        # 4. Generate system overview
        overview = service.get_system_overview(hours=1)
        
        assert overview["summary"]["total_events"] == 3
        assert overview["summary"]["unique_users"] == 1
        assert overview["summary"]["pdfs_processed"] == 1
        assert overview["summary"]["defenses_generated"] == 1
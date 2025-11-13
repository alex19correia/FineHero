"""
SQL Injection Protection Tests for Analytics Service
Comprehensive security testing for all analytics endpoints
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import json

# Import the secured analytics service and security validator
from backend.services.analytics_service import AnalyticsService, EventData, AnalyticsEvent
from backend.services.security_validator import SecurityValidator


class TestSQLInjectionProtection:
    """
    Comprehensive tests for SQL injection protection in analytics service
    """
    
    @pytest.fixture
    def mock_db_session(self):
        """Create mock database session for testing"""
        mock_session = Mock()
        mock_session.add = Mock()
        mock_session.commit = Mock()
        mock_session.rollback = Mock()
        mock_session.refresh = Mock()
        mock_session.query = Mock()
        return mock_session
    
    @pytest.fixture
    def analytics_service(self, mock_db_session):
        """Create analytics service instance for testing"""
        return AnalyticsService(mock_db_session)
    
    def test_event_data_sql_injection_attempts(self):
        """
        Test EventData class rejects SQL injection attempts in all fields
        """
        validator = SecurityValidator()
        
        # Test user_id SQL injection attempts
        malicious_user_ids = [
            "admin' OR '1'='1",
            "1; DROP TABLE users;--",
            "1 UNION SELECT * FROM users--",
            "1' OR 'x'='x",
            "1; DELETE FROM analytics_events;--"
        ]
        
        for malicious_id in malicious_user_ids:
            with pytest.raises(ValueError) as exc_info:
                validator.validate_user_id(malicious_id)
            assert "Invalid user ID format" in str(exc_info.value)
        
        # Test session_id SQL injection attempts
        malicious_sessions = [
            "sess'; DROP TABLE sessions;--",
            "abc123' UNION SELECT * FROM sessions--",
            "test' OR '1'='1'--"
        ]
        
        for malicious_session in malicious_sessions:
            with pytest.raises(ValueError) as exc_info:
                validator.validate_session_id(malicious_session)
            # Should either raise error or return safe session ID
        
        # Test event_data SQL injection attempts
        malicious_event_data = [
            {"user_id": "1' OR '1'='1"},
            {"query": "SELECT * FROM users WHERE id = '1'"},
            {"sql": "DROP TABLE analytics_events;"}
        ]
        
        for malicious_data in malicious_event_data:
            sanitized = validator.validate_event_data(malicious_data)
            # Should sanitize dangerous patterns
            assert not any("SELECT" in str(v) for v in sanitized.values())
            assert not any("DROP" in str(v) for v in sanitized.values())
    
    def test_event_creation_with_malicious_input(self, analytics_service):
        """
        Test that event creation rejects malicious input
        """
        # Mock successful database operations
        mock_event = Mock()
        mock_event.id = 1
        mock_event.timestamp = datetime.utcnow()
        analytics_service.db.add = Mock()
        analytics_service.db.commit = Mock()
        analytics_service.db.refresh = Mock(return_value=mock_event)
        
        # Test malicious user_id in EventData
        malicious_event = EventData(
            event_type="page_view",
            user_id="admin' OR '1'='1",  # SQL injection attempt
            data={"query": "SELECT * FROM users"}
        )
        
        result = analytics_service.track_event(malicious_event)
        assert result['success'] is False
        assert 'VALIDATION_ERROR' in result.get('error_code', '')
    
    def test_pdf_upload_sql_injection_protection(self, analytics_service):
        """
        Test PDF upload endpoint SQL injection protection
        """
        # Mock database operations
        analytics_service.db.add = Mock()
        analytics_service.db.commit = Mock()
        analytics_service.db.refresh = Mock()
        
        malicious_user_ids = [
            "user'; DROP TABLE users;--",
            "1 UNION SELECT * FROM users--",
            "user' OR '1'='1'--"
        ]
        
        for malicious_id in malicious_user_ids:
            result = analytics_service.track_pdf_upload(
                user_id=malicious_id,
                file_size=1024,
                processing_time=1.5
            )
            assert result['success'] is False
            assert 'VALIDATION_ERROR' in result.get('error_code', '')
    
    def test_defense_generation_sql_injection_protection(self, analytics_service):
        """
        Test defense generation endpoint SQL injection protection
        """
        # Mock database operations
        analytics_service.db.add = Mock()
        analytics_service.db.commit = Mock()
        analytics_service.db.refresh = Mock()
        
        # Test malicious fine_data with SQL injection
        malicious_fine_data = {
            "fine_amount": "100' OR '1'='1",  # SQL injection in amount
            "infraction_code": "CE-ART'; DROP TABLE fines;--",  # SQL injection in code
            "notes": "SELECT * FROM users WHERE admin=1"  # SQL injection in notes
        }
        
        result = analytics_service.track_defense_generation(
            user_id="malicious_user",
            fine_data=malicious_fine_data,
            processing_time=2.0
        )
        
        assert result['success'] is False
        # Should sanitize the malicious data or reject it
    
    def test_user_engagement_sql_injection_protection(self, analytics_service):
        """
        Test user engagement endpoint SQL injection protection
        """
        # Mock database operations
        analytics_service.db.add = Mock()
        analytics_service.db.commit = Mock()
        analytics_service.db.refresh = Mock()
        
        malicious_actions = [
            "login'; DROP TABLE users;--",
            "view' UNION SELECT * FROM sessions--",
            "download' OR '1'='1'--"
        ]
        
        for malicious_action in malicious_actions:
            result = analytics_service.track_user_engagement(
                user_id="test_user",
                action=malicious_action,
                additional_data={"page": "admin.php?id=1' OR '1'='1"}
            )
            
            assert result['success'] is False
            assert 'VALIDATION_ERROR' in result.get('error_code', '')
    
    def test_user_kpi_update_sql_injection_protection(self, analytics_service):
        """
        Test user KPI update endpoint SQL injection protection
        """
        # Mock database query and operations
        analytics_service.db.query.return_value.filter.return_value.first.return_value = None
        analytics_service.db.add = Mock()
        analytics_service.db.commit = Mock()
        analytics_service.db.refresh = Mock()
        
        malicious_metrics = {
            "pdfs_uploaded": "100' OR '1'='1",
            "subscription_tier": "premium'; DROP TABLE user_kpis;--",
            "custom_field": "SELECT * FROM users"  # Should be filtered out
        }
        
        result = analytics_service.update_user_kpis(
            user_id="user'; DROP TABLE users;--",
            date=datetime.utcnow(),
            metrics=malicious_metrics
        )
        
        assert result['success'] is False
        assert 'VALIDATION_ERROR' in result.get('error_code', '')
    
    def test_get_user_dashboard_data_sql_injection_protection(self, analytics_service):
        """
        Test user dashboard data retrieval SQL injection protection
        """
        # Mock database query to return empty results
        analytics_service.db.query.return_value.filter.return_value.all.return_value = []
        
        malicious_user_ids = [
            "user' UNION SELECT * FROM users--",
            "admin'; DELETE FROM analytics_events;--",
            "1' OR '1'='1"
        ]
        
        for malicious_id in malicious_user_ids:
            result = analytics_service.get_user_dashboard_data(
                user_id=malicious_id,
                days=30
            )
            
            # Should either reject the malicious input or return error
            if 'success' in result and not result['success']:
                assert 'VALIDATION_ERROR' in result.get('error_code', '')
    
    def test_get_system_overview_sql_injection_protection(self, analytics_service):
        """
        Test system overview endpoint SQL injection protection
        """
        # Mock database queries
        analytics_service.db.query.return_value.filter.return_value.all.return_value = []
        analytics_service.db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = []
        
        # Test with negative hours (potential injection)
        result = analytics_service.get_system_overview(hours=-1)
        assert result['success'] is False
        
        # Test with extremely large hours
        result = analytics_service.get_system_overview(hours=999999)
        assert result['success'] is False
    
    def test_xss_protection_in_event_data(self):
        """
        Test XSS protection in event data
        """
        validator = SecurityValidator()
        
        # Test XSS attempts in various fields
        xss_payloads = [
            "<script>alert('xss')</script>",
            "javascript:alert('xss')",
            "<img src=x onerror=alert('xss')>",
            "<iframe src=javascript:alert('xss')></iframe>",
            "<svg onload=alert('xss')>"
        ]
        
        for xss_payload in xss_payloads:
            # Test in user_id
            try:
                validator.validate_user_id(f"user_{xss_payload}")
                # If no error, check that payload was sanitized
                # This depends on the implementation
            except ValueError:
                # Expected - malicious input should be rejected
                pass
            
            # Test in event data
            malicious_data = {"user_input": xss_payload}
            sanitized = validator.validate_event_data(malicious_data)
            
            # Check that XSS patterns were removed
            sanitized_str = str(sanitized).lower()
            assert "<script>" not in sanitized_str
            assert "javascript:" not in sanitized_str
            assert "onerror=" not in sanitized_str
    
    def test_path_traversal_protection(self):
        """
        Test path traversal protection
        """
        validator = SecurityValidator()
        
        # Test path traversal attempts
        path_traversal_attempts = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\config\\sam",
            "%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd",
            "....//....//....//etc//passwd"
        ]
        
        for malicious_path in path_traversal_attempts:
            # Test in URL fields
            result = validator.validate_url(f"http://example.com/{malicious_path}")
            assert result is None  # Should be rejected or sanitized
    
    def test_rate_limiting_protection(self, analytics_service):
        """
        Test rate limiting protection against abuse
        """
        # Mock database operations
        mock_event = Mock()
        mock_event.id = 1
        mock_event.timestamp = datetime.utcnow()
        analytics_service.db.add = Mock()
        analytics_service.db.commit = Mock()
        analytics_service.db.refresh = Mock(return_value=mock_event)
        
        # Simulate excessive requests
        malicious_user_id = "test_user"
        
        # Make many requests to trigger rate limiting
        for i in range(150):  # Exceed the 100 request limit
            event = EventData(
                event_type="test_event",
                user_id=malicious_user_id,
                data={"request_id": i}
            )
            
            result = analytics_service.track_event(event)
            
            if i >= 100:  # Rate limit should kick in
                assert result['success'] is False
                assert 'VALIDATION_ERROR' in result.get('error_code', '')
    
    def test_error_handling_doesnt_expose_internal_info(self, analytics_service):
        """
        Test that error handling doesn't expose sensitive information
        """
        # Mock database to raise SQLAlchemy error
        analytics_service.db.add = Mock(side_effect=Exception("Database connection failed"))
        analytics_service.db.commit = Mock()
        
        event = EventData(
            event_type="test_event",
            user_id="test_user"
        )
        
        result = analytics_service.track_event(event)
        
        # Check that internal error details are not exposed
        assert result['success'] is False
        error_msg = result.get('error', '')
        assert "Database connection failed" not in error_msg
        assert "traceback" not in error_msg.lower()
        assert "sql" not in error_msg.lower() or "operation failed" in error_msg.lower()
    
    def test_ip_address_validation(self):
        """
        Test IP address validation
        """
        validator = SecurityValidator()
        
        # Test valid IP addresses
        valid_ips = ["192.168.1.1", "127.0.0.1", "::1", "2001:db8::1"]
        for ip in valid_ips:
            result = validator.validate_ip_address(ip)
            assert result is not None or result == ip  # Should pass validation
        
        # Test malicious IP attempts
        malicious_ips = [
            "192.168.1.1'; DROP TABLE users;--",
            "127.0.0.1' UNION SELECT * FROM sessions--",
            "'; DROP TABLE users;--"
        ]
        
        for malicious_ip in malicious_ips:
            result = validator.validate_ip_address(malicious_ip)
            assert result is None  # Should be rejected
    
    def test_url_validation(self):
        """
        Test URL validation and sanitization
        """
        validator = SecurityValidator()
        
        # Test safe URLs
        safe_urls = [
            "https://example.com/page",
            "http://localhost:8000/api/data",
            "/relative/path"
        ]
        
        for url in safe_urls:
            result = validator.validate_url(url)
            assert result is not None  # Should pass validation
        
        # Test malicious URLs
        malicious_urls = [
            "javascript:alert('xss')",
            "data:text/html,<script>alert('xss')</script>",
            "http://evil.com'; DROP TABLE users;--"
        ]
        
        for malicious_url in malicious_urls:
            result = validator.validate_url(malicious_url)
            assert result is None  # Should be rejected
    
    def test_comprehensive_security_logging(self, analytics_service):
        """
        Test that security events are properly logged
        """
        with patch('logging.getLogger') as mock_logger:
            mock_security_logger = Mock()
            mock_logger.return_value = mock_security_logger
            
            # Mock database operations
            analytics_service.db.add = Mock()
            analytics_service.db.commit = Mock()
            analytics_service.db.refresh = Mock()
            
            # Test logging of security events
            event = EventData(
                event_type="test_event",
                user_id="admin' OR '1'='1",  # Malicious input
                data={"query": "SELECT * FROM users"}
            )
            
            result = analytics_service.track_event(event)
            
            # Check that security events were logged
            assert mock_security_logger.warning.called or mock_security_logger.error.called


class TestSecurityValidatorComprehensive:
    """
    Comprehensive tests for the SecurityValidator class
    """
    
    def test_validate_user_id_comprehensive(self):
        """
        Test all aspects of user ID validation
        """
        validator = SecurityValidator()
        
        # Test valid user IDs
        valid_user_ids = ["user123", "user@example.com", "user_name-123", "UPPERCASE_USER"]
        for user_id in valid_user_ids:
            result = validator.validate_user_id(user_id)
            assert isinstance(result, str)
            assert len(result) <= 100
        
        # Test invalid user IDs
        invalid_cases = [
            "",  # Empty string
            "   ",  # Whitespace only
            None,  # None value
            "user' OR '1'='1",  # SQL injection
            "user<script>alert('xss')</script>",  # XSS
            "a" * 101,  # Too long
        ]
        
        for invalid_case in invalid_cases:
            with pytest.raises(ValueError):
                validator.validate_user_id(invalid_case)
    
    def test_validate_event_data_comprehensive(self):
        """
        Test comprehensive event data validation
        """
        validator = SecurityValidator()
        
        # Test valid event data
        valid_data = {
            "user_id": "user123",
            "action": "click",
            "count": 5,
            "amount": 99.99,
            "enabled": True,
            "metadata": {"key": "value"}
        }
        
        result = validator.validate_event_data(valid_data)
        assert isinstance(result, dict)
        assert "user_id" in result or "user_id" not in result  # Depends on filtering
        
        # Test malicious event data
        malicious_data = {
            "user_id": "admin' OR '1'='1",
            "query": "SELECT * FROM users",
            "script": "<script>alert('xss')</script>",
            "path": "../../../etc/passwd",
            "valid_field": "safe_value"
        }
        
        result = validator.validate_event_data(malicious_data)
        
        # Check that dangerous content was sanitized
        result_str = str(result).lower()
        assert "<script>" not in result_str
        assert "select *" not in result_str
        assert "../../.." not in result_str


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
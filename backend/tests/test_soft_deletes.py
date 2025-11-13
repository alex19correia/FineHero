"""
Comprehensive testing suite for soft delete and audit trail functionality.

This test suite covers:
- Soft delete and restore operations
- Audit trail logging and retrieval
- GDPR compliance functionality
- Data retention policies
- API endpoint testing
- Edge cases and error handling
- Performance and integration testing

Run with: pytest backend/tests/test_soft_deletes.py -v
"""
import pytest
import json
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

# Import application modules
from backend.app.models import *
from backend.app.schemas import *
from backend.app.crud_soft_delete import fine_crud, defense_crud, user_crud, audit_trail_crud
from backend.services.gdpr_compliance_service import (
    GDPRComplianceService, create_gdpr_service,
    DataRetentionService, DataExportService, DataAnonymizationService
)
from backend.app.main import app

# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_soft_deletes.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Test fixtures
@pytest.fixture(scope="session")
def db():
    """Create test database and tables."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def db_session():
    """Create a test database session."""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.rollback()
        db.close()

@pytest.fixture
def test_client():
    """Create a test client for API testing."""
    return TestClient(app)

@pytest.fixture
def sample_user_data():
    """Sample user data for testing."""
    return {
        "email": "testuser@example.com",
        "username": "testuser",
        "hashed_password": "hashed_password_123",
        "full_name": "Test User"
    }

@pytest.fixture
def sample_fine_data():
    """Sample fine data for testing."""
    return {
        "date": "2024-01-15",
        "location": "Lisbon, Portugal",
        "infractor": "John Doe",
        "fine_amount": 100.0,
        "infraction_code": "ART-048"
    }

@pytest.fixture
def sample_defense_data():
    """Sample defense data for testing."""
    return {
        "content": "This is a test defense for the traffic fine."
    }


class TestSoftDeleteMixin:
    """Test soft delete functionality."""
    
    def test_soft_delete_operations(self, db_session):
        """Test basic soft delete and restore operations."""
        # Create a user
        user = User(
            email="test@example.com",
            username="testuser",
            hashed_password="hashed_password"
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        
        # Test soft delete
        assert user.is_deleted == False
        assert user.deleted_at is None
        
        user.soft_delete()
        db_session.commit()
        db_session.refresh(user)
        
        assert user.is_deleted == True
        assert user.deleted_at is not None
        
        # Test restore
        user.restore()
        db_session.commit()
        db_session.refresh(user)
        
        assert user.is_deleted == False
        assert user.deleted_at is None
    
    def test_soft_delete_with_specific_timestamp(self, db_session):
        """Test soft delete with specific timestamp."""
        user = User(
            email="test@example.com",
            username="testuser",
            hashed_password="hashed_password"
        )
        db_session.add(user)
        db_session.commit()
        
        custom_timestamp = datetime.utcnow() - timedelta(days=1)
        user.soft_delete(custom_timestamp)
        db_session.commit()
        
        assert user.is_deleted == True
        assert user.deleted_at == custom_timestamp
    
    def test_soft_delete_queries(self, db_session):
        """Test soft delete filtering in queries."""
        # Create multiple users
        users = []
        for i in range(5):
            user = User(
                email=f"user{i}@example.com",
                username=f"user{i}",
                hashed_password="hashed_password"
            )
            users.append(user)
            db_session.add(user)
        db_session.commit()
        
        # Soft delete some users
        users[0].soft_delete()
        users[2].soft_delete()
        db_session.commit()
        
        # Test active records query
        active_users = User.get_active_records_query(db_session).all()
        assert len(active_users) == 3
        
        # Test deleted records query
        deleted_users = User.get_deleted_records_query(db_session).all()
        assert len(deleted_users) == 2


class TestAuditMixin:
    """Test audit trail functionality."""
    
    def test_audit_trail_creation(self, db_session):
        """Test audit trail creation and logging."""
        # Create a user with audit info
        user = User(
            email="test@example.com",
            username="testuser",
            hashed_password="hashed_password"
        )
        user.create_with_audit(user_id=1, metadata={"test": "creation"})
        
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        
        # Check audit metadata
        assert user.created_at is not None
        assert user.updated_at is not None
        assert user.created_by == 1
        assert user.updated_by == 1
        
        # Verify audit metadata contains creation info
        audit_metadata = json.loads(user.audit_metadata)
        assert "created_by_user" in audit_metadata
        assert audit_metadata["created_by_user"] == 1
    
    def test_audit_update(self, db_session):
        """Test audit trail updates."""
        user = User(
            email="test@example.com",
            username="testuser",
            hashed_password="hashed_password"
        )
        db_session.add(user)
        db_session.commit()
        
        # Update user with audit info
        user.update_audit_info(user_id=2, metadata={"test": "update"})
        db_session.commit()
        
        assert user.updated_by == 2
        assert user.updated_at >= user.created_at
        
        # Verify audit metadata contains update info
        audit_metadata = json.loads(user.audit_metadata)
        assert "updated_fields" in audit_metadata


class TestFineCRUD:
    """Test Fine CRUD operations with soft delete and audit."""
    
    def test_create_fine_with_audit(self, db_session, sample_fine_data):
        """Test creating a fine with audit trail."""
        user = User(
            email="user@example.com",
            username="testuser",
            hashed_password="hashed_password"
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        
        # Create fine with audit
        fine = fine_crud.create_with_audit(
            db=db_session,
            fine=FineCreate(**sample_fine_data),
            user_id=user.id
        )
        
        assert fine.id is not None
        assert fine.created_by == user.id
        assert fine.updated_by == user.id
    
    def test_soft_delete_fine(self, db_session, sample_fine_data):
        """Test soft deleting a fine."""
        # Create and save fine
        fine = Fine(**sample_fine_data)
        db_session.add(fine)
        db_session.commit()
        db_session.refresh(fine)
        
        # Soft delete
        deleted_fine = fine_crud.soft_delete(
            db=db_session,
            id=fine.id,
            user_id=1,
            reason="Test deletion"
        )
        
        assert deleted_fine.is_deleted == True
        assert deleted_fine.deleted_at is not None
    
    def test_restore_fine(self, db_session, sample_fine_data):
        """Test restoring a soft-deleted fine."""
        # Create and soft delete fine
        fine = Fine(**sample_fine_data)
        fine.soft_delete()
        db_session.add(fine)
        db_session.commit()
        db_session.refresh(fine)
        
        # Restore
        restored_fine = fine_crud.restore(
            db=db_session,
            id=fine.id,
            user_id=1
        )
        
        assert restored_fine.is_deleted == False
        assert restored_fine.deleted_at is None
    
    def test_get_with_relationships(self, db_session, sample_fine_data):
        """Test getting fine with relationships."""
        # Create user and fine
        user = User(
            email="user@example.com",
            username="testuser",
            hashed_password="hashed_password"
        )
        db_session.add(user)
        db_session.commit()
        
        fine_data = sample_fine_data.copy()
        fine_data["user_id"] = user.id
        
        fine = Fine(**fine_data)
        db_session.add(fine)
        db_session.commit()
        db_session.refresh(fine)
        
        # Test eager loading
        loaded_fine = fine_crud.get_with_relationships(db=db_session, id=fine.id)
        assert loaded_fine is not None
        assert loaded_fine.user is not None


class TestDefenseCRUD:
    """Test Defense CRUD operations."""
    
    def test_create_defense_with_audit(self, db_session, sample_fine_data, sample_defense_data):
        """Test creating a defense with audit trail."""
        # Create user and fine
        user = User(
            email="user@example.com",
            username="testuser",
            hashed_password="hashed_password"
        )
        db_session.add(user)
        db_session.commit()
        
        fine_data = sample_fine_data.copy()
        fine_data["user_id"] = user.id
        
        fine = Fine(**fine_data)
        db_session.add(fine)
        db_session.commit()
        db_session.refresh(fine)
        
        # Create defense
        defense = defense_crud.create_with_audit(
            db=db_session,
            defense=DefenseCreate(**sample_defense_data),
            fine_id=fine.id,
            user_id=user.id
        )
        
        assert defense.id is not None
        assert defense.fine_id == fine.id
        assert defense.created_by == user.id


class TestAuditTrailCRUD:
    """Test audit trail CRUD operations."""
    
    def test_get_audit_by_table_and_record(self, db_session):
        """Test getting audit trail for a specific table record."""
        # Create user
        user = User(
            email="test@example.com",
            username="testuser",
            hashed_password="hashed_password"
        )
        db_session.add(user)
        db_session.commit()
        
        # Create audit entry
        audit_entry = AuditTrail.create_audit_entry(
            table_name="users",
            record_id=user.id,
            action="CREATE",
            user_id=1
        )
        db_session.add(audit_entry)
        db_session.commit()
        
        # Retrieve audit trail
        audit_trail = audit_trail_crud.get_by_table_and_record(
            db=db_session,
            table_name="users",
            record_id=user.id,
            limit=10
        )
        
        assert len(audit_trail) == 1
        assert audit_trail[0].table_name == "users"
        assert audit_trail[0].record_id == user.id
        assert audit_trail[0].action == "CREATE"
    
    def test_cleanup_old_audit_data(self, db_session):
        """Test cleaning up old audit data."""
        # Create old audit entries
        cutoff_date = datetime.utcnow() - timedelta(days=100)
        
        old_audit = AuditTrail(
            table_name="test_table",
            record_id=1,
            action="CREATE",
            timestamp=cutoff_date - timedelta(days=1)
        )
        
        recent_audit = AuditTrail(
            table_name="test_table",
            record_id=2,
            action="CREATE",
            timestamp=datetime.utcnow()
        )
        
        db_session.add_all([old_audit, recent_audit])
        db_session.commit()
        
        # Clean up old data
        deleted_count = audit_trail_crud.cleanup_old_audit_data(
            db=db_session,
            retention_days=90
        )
        
        assert deleted_count == 1
        
        # Verify only recent entry remains
        remaining_audits = db_session.query(AuditTrail).all()
        assert len(remaining_audits) == 1


class TestGDPRComplianceService:
    """Test GDPR compliance functionality."""
    
    def test_data_export(self, db_session, sample_user_data):
        """Test user data export for GDPR compliance."""
        # Create user
        user = user_crud.create_with_audit(db=db_session, user=UserCreate(**sample_user_data))
        
        # Create some related data
        fine_data = {
            "date": "2024-01-15",
            "location": "Lisbon",
            "infractor": "Test User",
            "fine_amount": 100.0,
            "infraction_code": "ART-048"
        }
        fine = fine_crud.create_with_audit(db=db_session, fine=FineCreate(**fine_data), user_id=user.id)
        
        # Test data export
        gdpr_service = create_gdpr_service(db_session)
        result = gdpr_service.handle_data_subject_request(
            user_id=user.id,
            request_type="export"
        )
        
        assert result["status"] == "completed"
        assert "user_profile" in result["data"]["data"]
        assert "fines" in result["data"]["data"]
    
    def test_user_deletion_request(self, db_session, sample_user_data):
        """Test user deletion request for GDPR compliance."""
        # Create user
        user = user_crud.create_with_audit(db=db_session, user=UserCreate(**sample_user_data))
        
        # Test deletion request
        gdpr_service = create_gdpr_service(db_session)
        result = gdpr_service.handle_data_subject_request(
            user_id=user.id,
            request_type="delete",
            reason="User requested deletion",
            confirm_deletion=True
        )
        
        assert result["status"] == "completed"
        assert "retention_days" in result
        
        # Verify user is soft deleted
        db_session.refresh(user)
        assert user.is_deleted == True
    
    def test_data_anonymization(self, db_session, sample_user_data):
        """Test data anonymization for GDPR compliance."""
        # Create user
        user = user_crud.create_with_audit(db=db_session, user=UserCreate(**sample_user_data))
        
        # Create related data
        fine_data = {
            "date": "2024-01-15",
            "location": "Lisbon",
            "infractor": "Test User",
            "fine_amount": 100.0,
            "infraction_code": "ART-048"
        }
        fine = fine_crud.create_with_audit(db=db_session, fine=FineCreate(**fine_data), user_id=user.id)
        
        # Test anonymization
        anonymization_service = DataAnonymizationService(db_session)
        success = anonymization_service.anonymize_user_data(
            user_id=user.id,
            reason="User requested anonymization"
        )
        
        assert success == True
        
        # Verify user data is anonymized
        db_session.refresh(user)
        assert user.email.startswith("anonymized_user_")
        assert user.username.startswith("anonymized_user_")
        assert user.full_name == "Anonymized User"
        
        # Verify fine data is anonymized
        db_session.refresh(fine)
        assert fine.infractor == "ANONYMIZED"
    
    def test_data_retention_cleanup(self, db_session):
        """Test automated data retention cleanup."""
        # Create user with old deletion date
        old_deletion_date = datetime.utcnow() - timedelta(days=800)  # > 2 years
        user = User(
            email="olduser@example.com",
            username="olduser",
            hashed_password="hashed_password"
        )
        user.soft_delete(old_deletion_date)
        db_session.add(user)
        db_session.commit()
        
        # Test retention cleanup (dry run)
        retention_service = DataRetentionService(db_session)
        results = retention_service.run_retention_cleanup(dry_run=True)
        
        assert "users_to_cleanup" in results
        assert results["users_to_cleanup"] == 1
        
        # Test actual cleanup
        results = retention_service.run_retention_cleanup(dry_run=False)
        assert "users_deleted" in results
        assert results["users_deleted"] == 1


class TestDataRetentionService:
    """Test data retention service."""
    
    def test_retention_policies(self):
        """Test data retention policy configuration."""
        from backend.services.gdpr_compliance_service import RetentionPolicy
        
        # Test different retention periods
        financial_retention = RetentionPolicy.get_retention_days("payments", "financial")
        user_retention = RetentionPolicy.get_retention_days("users", "user_data")
        audit_retention = RetentionPolicy.get_retention_days("audit_trails", "audit_data")
        
        # Verify retention periods
        assert financial_retention == 2555  # 7 years
        assert user_retention == 730       # 2 years
        assert audit_retention == 2555     # 7 years
    
    def test_bulk_operations(self, db_session):
        """Test bulk soft delete operations."""
        # Create multiple users
        users = []
        for i in range(5):
            user = User(
                email=f"user{i}@example.com",
                username=f"user{i}",
                hashed_password="hashed_password"
            )
            users.append(user)
            db_session.add(user)
        db_session.commit()
        
        # Bulk soft delete
        user_ids = [user.id for user in users[:3]]
        deleted_count = user_crud.bulk_soft_delete(
            db=db_session,
            ids=user_ids,
            user_id=1,
            reason="Bulk deletion test"
        )
        
        assert deleted_count == 3
        
        # Verify users are deleted
        for user_id in user_ids:
            user = db_session.query(User).filter(User.id == user_id).first()
            assert user.is_deleted == True


class TestAPIEndpoints:
    """Test API endpoints with soft delete functionality."""
    
    def test_create_fine_endpoint(self, test_client, sample_fine_data):
        """Test creating a fine via API."""
        response = test_client.post("/api/v1/fines/", json=sample_fine_data)
        
        assert response.status_code == 200
        fine_data = response.json()
        assert fine_data["date"] == sample_fine_data["date"]
        assert fine_data["location"] == sample_fine_data["location"]
    
    def test_soft_delete_fine_endpoint(self, test_client):
        """Test soft deleting a fine via API."""
        # First create a fine
        fine_data = {
            "date": "2024-01-15",
            "location": "Lisbon",
            "infractor": "Test User",
            "fine_amount": 100.0,
            "infraction_code": "ART-048"
        }
        
        create_response = test_client.post("/api/v1/fines/", json=fine_data)
        assert create_response.status_code == 200
        fine_id = create_response.json()["id"]
        
        # Soft delete the fine
        delete_response = test_client.delete(f"/api/v1/fines/{fine_id}")
        assert delete_response.status_code == 200
        assert "soft deleted successfully" in delete_response.json()["message"]
    
    def test_get_fine_with_deleted_param(self, test_client):
        """Test getting fine with include_deleted parameter."""
        # Create and delete a fine
        fine_data = {
            "date": "2024-01-15",
            "location": "Lisbon",
            "infractor": "Test User",
            "fine_amount": 100.0,
            "infraction_code": "ART-048"
        }
        
        create_response = test_client.post("/api/v1/fines/", json=fine_data)
        fine_id = create_response.json()["id"]
        
        # Delete the fine
        test_client.delete(f"/api/v1/fines/{fine_id}")
        
        # Try to get active fine (should not return)
        active_response = test_client.get(f"/api/v1/fines/{fine_id}")
        assert active_response.status_code == 404
        
        # Get fine with deleted included
        include_deleted_response = test_client.get(f"/api/v1/fines/{fine_id}?include_deleted=true")
        assert include_deleted_response.status_code == 200
        assert include_deleted_response.json()["is_deleted"] == True
    
    def test_gdpr_export_endpoint(self, test_client):
        """Test GDPR data export endpoint."""
        # Create user and data via API
        user_data = {
            "email": "exporttest@example.com",
            "username": "exportuser",
            "hashed_password": "hashed_password",
            "full_name": "Export Test User"
        }
        
        user_response = test_client.post("/api/v1/users/", json=user_data)
        assert user_response.status_code == 200
        user_id = user_response.json()["id"]
        
        # Request data export
        export_response = test_client.post(f"/api/v1/fines/gdpr/export/{user_id}")
        assert export_response.status_code == 200
        assert export_response.json()["status"] == "success"


class TestEdgeCases:
    """Test edge cases and error handling."""
    
    def test_restore_nonexistent_fine(self, db_session):
        """Test restoring a fine that doesn't exist."""
        result = fine_crud.restore(db=db_session, id=999, user_id=1)
        assert result is None
    
    def test_permanent_delete_without_confirmation(self, db_session, sample_fine_data):
        """Test permanent delete without confirmation."""
        fine = Fine(**sample_fine_data)
        db_session.add(fine)
        db_session.commit()
        
        # Should not delete without confirmation
        success = fine_crud.permanent_delete(
            db=db_session,
            id=fine.id,
            user_id=1,
            reason="Test"
        )
        
        # Should still exist since no actual implementation for confirmation
        remaining_fine = db_session.query(Fine).filter(Fine.id == fine.id).first()
        assert remaining_fine is not None
    
    def test_audit_trail_with_invalid_json(self, db_session):
        """Test audit trail with invalid JSON metadata."""
        user = User(
            email="test@example.com",
            username="testuser",
            hashed_password="hashed_password",
            audit_metadata="invalid json"
        )
        db_session.add(user)
        db_session.commit()
        
        # Should handle invalid JSON gracefully
        user.update_audit_info(user_id=1, metadata={"test": "update"})
        db_session.commit()
        
        assert user.updated_by == 1
    
    def test_bulk_operations_with_empty_list(self, db_session):
        """Test bulk operations with empty lists."""
        # Should handle empty lists gracefully
        deleted_count = user_crud.bulk_soft_delete(
            db=db_session,
            ids=[],
            user_id=1,
            reason="Empty list test"
        )
        
        assert deleted_count == 0


class TestPerformance:
    """Test performance aspects of soft delete and audit functionality."""
    
    def test_bulk_operations_performance(self, db_session):
        """Test performance of bulk operations."""
        import time
        
        # Create many users
        start_time = time.time()
        users = []
        for i in range(100):
            user = User(
                email=f"bulk_user{i}@example.com",
                username=f"bulk_user{i}",
                hashed_password="hashed_password"
            )
            users.append(user)
            db_session.add(user)
        db_session.commit()
        
        creation_time = time.time() - start_time
        
        # Bulk delete
        start_time = time.time()
        user_ids = [user.id for user in users]
        deleted_count = user_crud.bulk_soft_delete(
            db=db_session,
            ids=user_ids,
            user_id=1,
            reason="Performance test bulk delete"
        )
        
        deletion_time = time.time() - start_time
        
        assert deleted_count == 100
        assert deletion_time < 5.0  # Should complete within 5 seconds
    
    def test_audit_trail_performance(self, db_session):
        """Test audit trail performance with many operations."""
        import time
        
        user = User(
            email="perf_test@example.com",
            username="perfuser",
            hashed_password="hashed_password"
        )
        db_session.add(user)
        db_session.commit()
        
        # Create many audit entries
        start_time = time.time()
        for i in range(50):
            audit_entry = AuditTrail.create_audit_entry(
                table_name="users",
                record_id=user.id,
                action="UPDATE",
                user_id=1,
                additional_info=f"Audit entry {i}"
            )
            db_session.add(audit_entry)
        db_session.commit()
        
        creation_time = time.time() - start_time
        
        # Query audit trail
        start_time = time.time()
        audit_trail = audit_trail_crud.get_by_table_and_record(
            db=db_session,
            table_name="users",
            record_id=user.id,
            limit=100
        )
        
        query_time = time.time() - start_time
        
        assert len(audit_trail) == 50
        assert creation_time < 5.0  # Should create 50 entries within 5 seconds
        assert query_time < 1.0    # Should query within 1 second


# Integration tests
class TestIntegration:
    """Integration tests for complete workflows."""
    
    def test_complete_user_lifecycle(self, db_session):
        """Test complete user lifecycle with soft deletes and audit."""
        # Create user
        user_data = {
            "email": "lifecycle@example.com",
            "username": "lifecycleuser",
            "hashed_password": "hashed_password",
            "full_name": "Lifecycle Test User"
        }
        
        user = user_crud.create_with_audit(db=db_session, user=UserCreate(**user_data))
        user_id = user.id
        
        # Create fines
        for i in range(3):
            fine_data = {
                "date": f"2024-01-{15+i}",
                "location": f"Location {i}",
                "infractor": "Lifecycle User",
                "fine_amount": 100.0 + i * 50,
                "infraction_code": f"ART-{048+i}"
            }
            fine_crud.create_with_audit(db=db_session, fine=FineCreate(**fine_data), user_id=user_id)
        
        # Create defenses
        for i in range(2):
            defense_data = {
                "content": f"Defense content for fine {i}"
            }
            defense_crud.create_with_audit(
                db=db_session,
                defense=DefenseCreate(**defense_data),
                fine_id=user.fines[i].id,
                user_id=user_id
            )
        
        # Soft delete user
        user = user_crud.soft_delete(db=db_session, id=user_id, user_id=1, reason="Test lifecycle")
        assert user.is_deleted == True
        
        # Verify related data is also accessible
        fines = fine_crud.get_user_fines(db=db_session, user_id=user_id)
        assert len(fines) == 3
        
        # Restore user
        user = user_crud.restore(db=db_session, id=user_id, user_id=1)
        assert user.is_deleted == False
        
        # Create audit trail for lifecycle
        lifecycle_audit = audit_trail_crud.get_by_user(db=db_session, user_id=user_id, limit=100)
        assert len(lifecycle_audit) >= 4  # Create user + 3 fines + 2 defenses updates
        
        # Test GDPR export
        gdpr_service = create_gdpr_service(db_session)
        export_result = gdpr_service.handle_data_subject_request(
            user_id=user_id,
            request_type="export"
        )
        
        assert export_result["status"] == "completed"
        assert "user_profile" in export_result["data"]["data"]
        assert "fines" in export_result["data"]["data"]
        assert "defenses" in export_result["data"]["data"]


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
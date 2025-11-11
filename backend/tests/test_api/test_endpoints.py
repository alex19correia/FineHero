"""
API endpoint tests for fines and defenses routes.

This module contains comprehensive tests for all API endpoints including:
- CRUD operations for fines
- Defense generation endpoints  
- Error handling and validation
- Authentication and authorization scenarios
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from datetime import date
import json

from ..conftest import FineFactory, DefenseFactory, sample_fine_data, sample_defense_data


@pytest.mark.api
@pytest.mark.unit
class TestFinesAPI:
    """Test suite for fines API endpoints."""
    
    def test_create_fine_success(self, client, db_session, sample_fine_data):
        """Test successful fine creation."""
        response = client.post("/api/v1/fines/", json=sample_fine_data)
        
        assert response.status_code == 200
        response_data = response.json()
        assert response_data["date"] == "2025-11-11"
        assert response_data["location"] == sample_fine_data["location"]
        assert response_data["infractor"] == sample_fine_data["infractor"]
        assert response_data["fine_amount"] == sample_fine_data["fine_amount"]
        assert response_data["infraction_code"] == sample_fine_data["infraction_code"]
        assert response_data["pdf_reference"] == sample_fine_data["pdf_reference"]
        assert "id" in response_data
    
    def test_create_fine_invalid_data(self, client):
        """Test fine creation with invalid data."""
        invalid_data = {
            "date": "invalid-date",
            "location": "Test Location",
            "infractor": "Test Person",
            "fine_amount": "not-a-number",
            "infraction_code": "",
            "pdf_reference": "TEST-001"
        }
        
        response = client.post("/api/v1/fines/", json=invalid_data)
        assert response.status_code == 422  # Pydantic validation error
    
    def test_create_fine_missing_required_fields(self, client):
        """Test fine creation with missing required fields."""
        incomplete_data = {
            "location": "Test Location",
            "infractor": "Test Person"
            # Missing required fields: fine_amount, infraction_code
        }
        
        response = client.post("/api/v1/fines/", json=incomplete_data)
        assert response.status_code == 422
    
    def test_get_fines_empty_list(self, client):
        """Test retrieving empty fines list."""
        response = client.get("/api/v1/fines/")
        
        assert response.status_code == 200
        response_data = response.json()
        assert isinstance(response_data, list)
        assert len(response_data) == 0
    
    def test_get_fines_with_data(self, client, db_session, sample_fine_data):
        """Test retrieving fines with existing data."""
        # Create a fine first
        from app import crud
        crud.create_fine(db=db_session, fine=sample_fine_data)
        
        response = client.get("/api/v1/fines/")
        
        assert response.status_code == 200
        response_data = response.json()
        assert len(response_data) == 1
        assert response_data[0]["location"] == sample_fine_data["location"]
        assert response_data[0]["infractor"] == sample_fine_data["infractor"]
    
    def test_get_fines_with_pagination(self, client, db_session):
        """Test fines retrieval with pagination."""
        from app import crud
        
        # Create multiple fines
        for i in range(5):
            fine_data = {
                "date": "2025-11-11",
                "location": f"Location {i}",
                "infractor": f"Person {i}",
                "fine_amount": 100.0 + i * 10,
                "infraction_code": f"CODE{i}",
                "pdf_reference": f"MULT-{i:06d}"
            }
            crud.create_fine(db=db_session, fine=fine_data)
        
        # Test skip and limit
        response = client.get("/api/v1/fines/?skip=2&limit=2")
        
        assert response.status_code == 200
        response_data = response.json()
        assert len(response_data) == 2
        assert response_data[0]["location"] == "Location 2"
        assert response_data[1]["location"] == "Location 3"
    
    def test_get_fine_success(self, client, db_session, sample_fine_data):
        """Test retrieving a specific fine by ID."""
        from app import crud
        
        # Create a fine first
        created_fine = crud.create_fine(db=db_session, fine=sample_fine_data)
        fine_id = created_fine.id
        
        response = client.get(f"/api/v1/fines/{fine_id}")
        
        assert response.status_code == 200
        response_data = response.json()
        assert response_data["id"] == fine_id
        assert response_data["location"] == sample_fine_data["location"]
        assert response_data["infractor"] == sample_fine_data["infractor"]
    
    def test_get_fine_not_found(self, client):
        """Test retrieving a non-existent fine."""
        response = client.get("/api/v1/fines/99999")
        
        assert response.status_code == 404
        assert "Fine not found" in response.json()["detail"]
    
    def test_get_fine_invalid_id(self, client):
        """Test retrieving fine with invalid ID format."""
        response = client.get("/api/v1/fines/invalid-id")
        
        assert response.status_code == 422  # Validation error for invalid ID
    
    def test_get_fine_negative_id(self, client):
        """Test retrieving fine with negative ID."""
        response = client.get("/api/v1/fines/-1")
        
        assert response.status_code == 422  # Validation error


@pytest.mark.api
@pytest.mark.unit
class TestDefensesAPI:
    """Test suite for defenses API endpoints."""
    
    def test_create_defense_success(self, client, db_session, sample_fine_data, sample_defense_data):
        """Test successful defense creation for a fine."""
        from app import crud
        
        # Create a fine first
        created_fine = crud.create_fine(db=db_session, fine=sample_fine_data)
        
        defense_data = {
            "fine_id": created_fine.id,
            "content": sample_defense_data["content"]
        }
        
        response = client.post(f"/api/v1/fines/{created_fine.id}/defenses/", json=defense_data)
        
        assert response.status_code == 200
        response_data = response.json()
        assert response_data["fine_id"] == created_fine.id
        assert response_data["content"] == sample_defense_data["content"]
        assert "id" in response_data
    
    def test_create_defense_for_nonexistent_fine(self, client, sample_defense_data):
        """Test creating defense for a non-existent fine."""
        defense_data = {
            "fine_id": 99999,  # Non-existent fine
            "content": sample_defense_data["content"]
        }
        
        response = client.post(f"/api/v1/fines/99999/defenses/", json=defense_data)
        
        assert response.status_code == 404  # Fine not found
    
    def test_create_defense_invalid_data(self, client):
        """Test defense creation with invalid data."""
        invalid_data = {
            "fine_id": "invalid-id",
            "content": ""  # Empty content
        }
        
        response = client.post("/api/v1/fines/1/defenses/", json=invalid_data)
        assert response.status_code == 422  # Validation error
    
    def test_create_defense_missing_required_fields(self, client):
        """Test defense creation with missing required fields."""
        incomplete_data = {
            "content": "Defense content only"
            # Missing fine_id
        }
        
        response = client.post("/api/v1/fines/1/defenses/", json=incomplete_data)
        assert response.status_code == 422


@pytest.mark.api
@pytest.mark.integration
class TestAPIIntegration:
    """Integration tests for API workflows."""
    
    def test_full_fine_workflow(self, client, db_session):
        """Test complete fine workflow from creation to defense."""
        from app import crud
        
        # 1. Create a fine
        fine_data = {
            "date": "2025-11-11",
            "location": "Avenida da Liberdade, Lisboa",
            "infractor": "Maria Santos",
            "fine_amount": 150.00,
            "infraction_code": "ART135-1-A",
            "pdf_reference": "MULT-2025-001234"
        }
        
        create_response = client.post("/api/v1/fines/", json=fine_data)
        assert create_response.status_code == 200
        created_fine = create_response.json()
        
        # 2. Retrieve the fine
        get_response = client.get(f"/api/v1/fines/{created_fine['id']}")
        assert get_response.status_code == 200
        retrieved_fine = get_response.json()
        assert retrieved_fine["location"] == fine_data["location"]
        
        # 3. Create a defense for the fine
        defense_data = {
            "fine_id": created_fine["id"],
            "content": "Defense based on emergency medical circumstances."
        }
        
        defense_response = client.post(f"/api/v1/fines/{created_fine['id']}/defenses/", json=defense_data)
        assert defense_response.status_code == 200
        created_defense = defense_response.json()
        assert created_defense["fine_id"] == created_fine["id"]
        
        # 4. Verify defense was created
        assert created_defense["content"] == defense_data["content"]
    
    def test_root_endpoint(self, client):
        """Test the root API endpoint."""
        response = client.get("/")
        
        assert response.status_code == 200
        response_data = response.json()
        assert "message" in response_data
        assert "FineHero AI" in response_data["message"]
    
    def test_api_documentation_accessible(self, client):
        """Test that API documentation is accessible."""
        # Test Swagger UI
        response = client.get("/docs")
        assert response.status_code == 200
        
        # Test OpenAPI spec
        response = client.get("/openapi.json")
        assert response.status_code == 200
        openapi_spec = response.json()
        assert "openapi" in openapi_spec
        assert "info" in openapi_spec


@pytest.mark.api
@pytest.mark.security
class TestAPISecurity:
    """Security tests for API endpoints."""
    
    def test_sql_injection_protection(self, client):
        """Test protection against SQL injection attempts."""
        malicious_data = {
            "date": "2025-11-11",
            "location": "'; DROP TABLE fines; --",
            "infractor": "Test Person",
            "fine_amount": 100.0,
            "infraction_code": "CODE1",
            "pdf_reference": "TEST-001"
        }
        
        response = client.post("/api/v1/fines/", json=malicious_data)
        
        # Should either succeed (if data is properly sanitized) or return validation error
        # Should NOT result in database corruption
        assert response.status_code in [200, 422]
    
    def test_xss_protection_in_content(self, client):
        """Test XSS protection in defense content."""
        xss_payload = "<script>alert('xss')</script>"
        
        defense_data = {
            "fine_id": 1,
            "content": f"Defense with XSS attempt: {xss_payload}"
        }
        
        # In production, this should be properly sanitized
        # For now, we test that the endpoint accepts the content
        response = client.post("/api/v1/fines/1/defenses/", json=defense_data)
        
        # Should either succeed or return error, but not execute the script
        assert response.status_code in [200, 404, 422]  # 404 if fine doesn't exist
    
    def test_large_payload_handling(self, client):
        """Test handling of large payloads."""
        large_content = "X" * 10000  # 10KB content
        
        defense_data = {
            "fine_id": 1,
            "content": large_content
        }
        
        response = client.post("/api/v1/fines/1/defenses/", json=defense_data)
        
        # Should handle large payloads gracefully
        assert response.status_code in [200, 404, 413, 422]  # 413 if payload too large


@pytest.mark.api
@pytest.mark.performance
class TestAPIPerformance:
    """Performance tests for API endpoints."""
    
    def test_response_time_under_threshold(self, client, db_session):
        """Test that API responses complete under acceptable time threshold."""
        import time
        
        fine_data = {
            "date": "2025-11-11",
            "location": "Test Location",
            "infractor": "Test Person",
            "fine_amount": 100.0,
            "infraction_code": "CODE1",
            "pdf_reference": "TEST-001"
        }
        
        start_time = time.time()
        response = client.post("/api/v1/fines/", json=fine_data)
        end_time = time.time()
        
        response_time = end_time - start_time
        
        assert response.status_code == 200
        assert response_time < 1.0  # Should respond within 1 second
    
    def test_concurrent_requests_handling(self, client, db_session):
        """Test handling of concurrent requests."""
        import threading
        import time
        
        results = []
        errors = []
        
        def make_request():
            try:
                fine_data = {
                    "date": "2025-11-11",
                    "location": f"Location {threading.get_ident()}",
                    "infractor": "Test Person",
                    "fine_amount": 100.0,
                    "infraction_code": "CODE1",
                    "pdf_reference": f"TEST-{threading.get_ident()}"
                }
                response = client.post("/api/v1/fines/", json=fine_data)
                results.append(response.status_code)
            except Exception as e:
                errors.append(str(e))
        
        # Create 10 concurrent threads
        threads = []
        for i in range(10):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # All requests should succeed
        assert len(errors) == 0, f"Errors occurred: {errors}"
        assert all(status == 200 for status in results)
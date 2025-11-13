"""
Test suite for the centralized error handling middleware
"""

import json
import pytest
from datetime import datetime, timezone
from fastapi import FastAPI, Depends, HTTPException
from fastapi.testclient import TestClient
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from unittest.mock import Mock, patch

from backend.app.middleware.error_handler import (
    setup_error_handlers,
    add_error_middleware,
    FineHeroException,
    AuthenticationError,
    AuthorizationError,
    ResourceNotFoundError,
    ValidationError,
    PaymentError,
    ServiceUnavailableError,
    ConflictError,
    ErrorResponse
)
from backend.app.schemas.error import (
    ErrorResponse,
    ValidationErrorResponse,
    NotFoundErrorResponse,
    AuthErrorResponse,
    PermissionErrorResponse,
    ServerErrorResponse,
    PaymentErrorResponse
)


@pytest.fixture
def app_with_error_handling():
    """Create a FastAPI app with error handling."""
    app = FastAPI(title="Test API")
    
    # Add error handlers
    add_error_middleware(app)
    
    # Add a simple test endpoint
    @app.get("/test")
    def test_endpoint():
        return {"message": "Success"}
    
    # Add endpoint that raises custom exceptions
    @app.get("/test/auth-error")
    def test_auth_error():
        raise AuthenticationError()
    
    @app.get("/test/permission-error")
    def test_permission_error():
        raise AuthorizationError()
    
    @app.get("/test/not-found-error")
    def test_not_found_error():
        raise ResourceNotFoundError("test_resource", "123")
    
    @app.get("/test/validation-error")
    def test_validation_error():
        raise ValidationError("Validation failed", {"field1": "Invalid format", "field2": "Missing value"})
    
    @app.get("/test/payment-error")
    def test_payment_error():
        raise PaymentError("Payment declined", "FINEHERO_402_001")
    
    @app.get("/test/service-error")
    def test_service_error():
        raise ServiceUnavailableError("Document service is down")
    
    @app.get("/test/conflict-error")
    def test_conflict_error():
        raise ConflictError("User with this email already exists")
    
    # Endpoint with normal exception
    @app.get("/test/unexpected-error")
    def test_unexpected_error():
        raise ValueError("This is a test error")
    
    return app


@pytest.fixture
def client_with_error_handling(app_with_error_handling):
    """Create a test client for the app with error handling."""
    return TestClient(app_with_error_handling)


class TestErrorHandlerMiddleware:
    """Test class for error handler middleware."""
    
    def test_error_response_structure(self):
        """Test the structure of error responses."""
        error = ErrorResponse(
            error_type="validation_error",
            error_code="FINEHERO_422",
            detail="Request validation failed",
            status_code=422,
            path="/api/test",
            extra_data={"field_errors": {"name": "Required"}}
        )
        
        error_dict = error.to_dict()
        
        # Check structure
        assert "error" in error_dict
        assert "type" in error_dict["error"]
        assert "code" in error_dict["error"]
        assert "detail" in error_dict["error"]
        assert "timestamp" in error_dict["error"]
        assert error_dict["error"]["type"] == "validation_error"
        assert error_dict["error"]["code"] == "FINEHERO_422"
        assert error_dict["error"]["detail"] == "Request validation failed"
        assert error_dict["error"]["path"] == "/api/test"
        assert "data" in error_dict["error"]
        assert "field_errors" in error_dict["error"]["data"]
    
    def test_auth_error(self, client_with_error_handling):
        """Test authentication error handling."""
        response = client_with_error_handling.get("/test/auth-error")
        
        # Check status code
        assert response.status_code == 401
        
        # Check response structure
        json_response = response.json()
        assert "error" in json_response
        assert "type" in json_response["error"]
        assert "code" in json_response["error"]
        assert "detail" in json_response["error"]
        assert "timestamp" in json_response["error"]
        
        # Check error type
        assert json_response["error"]["type"] == "auth_error"
        assert json_response["error"]["code"] == "FINEHERO_401"
        assert "Authentication" in json_response["error"]["detail"]
    
    def test_permission_error(self, client_with_error_handling):
        """Test authorization error handling."""
        response = client_with_error_handling.get("/test/permission-error")
        
        # Check status code
        assert response.status_code == 403
        
        # Check error type
        json_response = response.json()
        assert json_response["error"]["type"] == "permission_error"
        assert json_response["error"]["code"] == "FINEHERO_403"
        assert "permission" in json_response["error"]["detail"].lower()
    
    def test_not_found_error(self, client_with_error_handling):
        """Test resource not found error handling."""
        response = client_with_error_handling.get("/test/not-found-error")
        
        # Check status code
        assert response.status_code == 404
        
        # Check error type
        json_response = response.json()
        assert json_response["error"]["type"] == "not_found_error"
        assert json_response["error"]["code"] == "FINEHERO_404"
        assert "not found" in json_response["error"]["detail"].lower()
        
        # Check resource data
        assert "data" in json_response["error"]
        assert json_response["error"]["data"]["resource_type"] == "test_resource"
        assert json_response["error"]["data"]["resource_id"] == "123"
    
    def test_validation_error(self, client_with_error_handling):
        """Test validation error handling."""
        response = client_with_error_handling.get("/test/validation-error")
        
        # Check status code
        assert response.status_code == 422
        
        # Check error type
        json_response = response.json()
        assert json_response["error"]["type"] == "validation_error"
        assert json_response["error"]["code"] == "FINEHERO_422"
        assert "Validation" in json_response["error"]["detail"]
        
        # Check field errors
        assert "data" in json_response["error"]
        assert "field_errors" in json_response["error"]["data"]
        assert "field1" in json_response["error"]["data"]["field_errors"]
        assert "field2" in json_response["error"]["data"]["field_errors"]
    
    def test_payment_error(self, client_with_error_handling):
        """Test payment error handling."""
        response = client_with_error_handling.get("/test/payment-error")
        
        # Check status code
        assert response.status_code == 402
        
        # Check error type
        json_response = response.json()
        assert json_response["error"]["type"] == "payment_error"
        assert json_response["error"]["code"] == "FINEHERO_402_001"  # Custom code
        
    def test_service_error(self, client_with_error_handling):
        """Test service unavailable error handling."""
        response = client_with_error_handling.get("/test/service-error")
        
        # Check status code
        assert response.status_code == 503
        
        # Check error type
        json_response = response.json()
        assert json_response["error"]["type"] == "service_error"
        assert json_response["error"]["code"] == "FINEHERO_503"
        assert "unavailable" in json_response["error"]["detail"].lower()
    
    def test_conflict_error(self, client_with_error_handling):
        """Test resource conflict error handling."""
        response = client_with_error_handling.get("/test/conflict-error")
        
        # Check status code
        assert response.status_code == 409
        
        # Check error type
        json_response = response.json()
        assert json_response["error"]["type"] == "conflict_error"
        assert json_response["error"]["code"] == "FINEHERO_409"
        assert "conflict" in json_response["error"]["detail"].lower()
    
    def test_unexpected_error(self, client_with_error_handling):
        """Test handling of unexpected errors."""
        response = client_with_error_handling.get("/test/unexpected-error")
        
        # Check status code
        assert response.status_code == 500
        
        # Check error type
        json_response = response.json()
        assert json_response["error"]["type"] == "server_error"
        assert json_response["error"]["code"] == "FINEHERO_500"
        assert "unexpected" in json_response["error"]["detail"].lower()
    
    def test_successful_request(self, client_with_error_handling):
        """Test that successful requests still work correctly."""
        response = client_with_error_handling.get("/test")
        
        # Check status code
        assert response.status_code == 200
        
        # Check response format
        json_response = response.json()
        assert "message" in json_response
        assert json_response["message"] == "Success"
    
    def test_timestamp_format(self, client_with_error_handling):
        """Test that timestamps are in ISO format."""
        response = client_with_error_handling.get("/test/auth-error")
        
        # Check that timestamp is a valid ISO format
        json_response = response.json()
        timestamp_str = json_response["error"]["timestamp"]
        
        # Parse timestamp to ensure it's valid
        timestamp = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
        assert isinstance(timestamp, datetime)
        assert timestamp.tzinfo == timezone.utc


@pytest.mark.asyncio
async def test_error_handler_with_custom_logger():
    """Test error handlers with a custom logger."""
    app = FastAPI(title="Test API with Custom Logger")
    
    # Create a mock logger
    mock_logger = Mock()
    
    # Add error handlers with custom logger
    add_error_middleware(app, mock_logger)
    
    # Add a test endpoint that raises an exception
    @app.get("/test-error")
    def test_error():
        raise FineHeroException(
            status_code=400,
            detail="Test error",
            error_type="test_error",
            error_code="TEST_001"
        )
    
    # Create test client
    client = TestClient(app)
    
    # Make request
    response = client.get("/test-error")
    
    # Check that error was logged
    mock_logger.warning.assert_called()
    
    # Check response structure
    assert response.status_code == 400
    json_response = response.json()
    assert "error" in json_response
    assert json_response["error"]["detail"] == "Test error"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
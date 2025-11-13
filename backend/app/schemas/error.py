"""
Error schemas for consistent error responses
"""

from datetime import datetime
from typing import Dict, Any, Optional, Union
from pydantic import BaseModel, Field


class ErrorDetail(BaseModel):
    """Schema for error details."""
    type: str = Field(..., description="Error type/category")
    code: str = Field(..., description="Error code")
    detail: str = Field(..., description="Error message")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Timestamp of error")
    path: Optional[str] = Field(None, description="Request path where error occurred")
    data: Optional[Dict[str, Any]] = Field(None, description="Additional error data")


class ErrorResponse(BaseModel):
    """Schema for error response."""
    error: ErrorDetail
    
    class Config:
        schema_extra = {
            "example": {
                "error": {
                    "type": "validation_error",
                    "code": "FINEHERO_422",
                    "detail": "Request validation failed",
                    "timestamp": "2025-11-12T21:17:00.000Z",
                    "path": "/api/v1/fines/123/defenses",
                    "data": {
                        "field_errors": {
                            "date": "Invalid date format",
                            "fine_amount": "Must be a positive number"
                        }
                    }
                }
            }
        }


class ValidationErrorDetail(BaseModel):
    """Schema for field validation errors."""
    field: str = Field(..., description="Field name")
    message: str = Field(..., description="Validation error message")


class ValidationErrorResponse(BaseModel):
    """Schema for validation error response."""
    error: Dict[str, Any]
    field_errors: list[ValidationErrorDetail] = Field(..., description="List of field validation errors")
    
    class Config:
        schema_extra = {
            "example": {
                "error": {
                    "type": "validation_error",
                    "code": "FINEHERO_422",
                    "detail": "Request validation failed",
                    "timestamp": "2025-11-12T21:17:00.000Z",
                    "path": "/api/v1/fines/123/defenses"
                },
                "field_errors": [
                    {
                        "field": "date",
                        "message": "Invalid date format"
                    },
                    {
                        "field": "fine_amount",
                        "message": "Must be a positive number"
                    }
                ]
            }
        }


class NotFoundErrorResponse(BaseModel):
    """Schema for not found error response."""
    error: Dict[str, Any]
    
    class Config:
        schema_extra = {
            "example": {
                "error": {
                    "type": "not_found_error",
                    "code": "FINEHERO_404",
                    "detail": "Fine with ID 123 not found",
                    "timestamp": "2025-11-12T21:17:00.000Z",
                    "path": "/api/v1/fines/123",
                    "data": {
                        "resource_type": "fine",
                        "resource_id": "123"
                    }
                }
            }
        }


class AuthErrorResponse(BaseModel):
    """Schema for authentication error response."""
    error: Dict[str, Any]
    
    class Config:
        schema_extra = {
            "example": {
                "error": {
                    "type": "auth_error",
                    "code": "FINEHERO_401",
                    "detail": "Authentication credentials are invalid or missing",
                    "timestamp": "2025-11-12T21:17:00.000Z",
                    "path": "/api/v1/auth/me"
                }
            }
        }


class PermissionErrorResponse(BaseModel):
    """Schema for permission error response."""
    error: Dict[str, Any]
    
    class Config:
        schema_extra = {
            "example": {
                "error": {
                    "type": "permission_error",
                    "code": "FINEHERO_403",
                    "detail": "You do not have permission to perform this action",
                    "timestamp": "2025-11-12T21:17:00.000Z",
                    "path": "/api/v1/admin/users"
                }
            }
        }


class ServerErrorResponse(BaseModel):
    """Schema for server error response."""
    error: Dict[str, Any]
    
    class Config:
        schema_extra = {
            "example": {
                "error": {
                    "type": "server_error",
                    "code": "FINEHERO_500",
                    "detail": "An unexpected error occurred",
                    "timestamp": "2025-11-12T21:17:00.000Z",
                    "path": "/api/v1/payments/process"
                }
            }
        }


class PaymentErrorResponse(BaseModel):
    """Schema for payment error response."""
    error: Dict[str, Any]
    
    class Config:
        schema_extra = {
            "example": {
                "error": {
                    "type": "payment_error",
                    "code": "FINEHERO_402",
                    "detail": "Payment processing error",
                    "timestamp": "2025-11-12T21:17:00.000Z",
                    "path": "/api/v1/payments/intents",
                    "data": {
                        "stripe_error_code": "card_declined",
                        "payment_intent_id": "pi_1234567890"
                    }
                }
            }
        }
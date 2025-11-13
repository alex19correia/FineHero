"""
Centralized Error Handler for FastAPI Applications
Provides consistent error handling across the API
"""

import json
import traceback
from typing import Dict, Any, Optional, Union, Type
from datetime import datetime, timezone
from fastapi import FastAPI, Request, Response, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from pydantic import ValidationError
from pydantic.error_wrappers import ErrorWrapper

# Custom exception types
class FineHeroException(Exception):
    """Base exception for FineHero application."""
    def __init__(
        self, 
        status_code: int = 500, 
        detail: str = "Internal server error",
        error_type: str = "server_error",
        error_code: str = "FINEHERO_500",
        extra_data: Optional[Dict[str, Any]] = None
    ):
        self.status_code = status_code
        self.detail = detail
        self.error_type = error_type
        self.error_code = error_code
        self.extra_data = extra_data or {}
        super().__init__(self.detail)

class AuthenticationError(FineHeroException):
    """Authentication error for when credentials are invalid or missing."""
    def __init__(self, detail: str = "Authentication credentials are invalid or missing", extra_data: Optional[Dict[str, Any]] = None):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            error_type="auth_error",
            error_code="FINEHERO_401",
            extra_data=extra_data
        )

class AuthorizationError(FineHeroException):
    """Authorization error for when user is not permitted to perform an action."""
    def __init__(self, detail: str = "You do not have permission to perform this action", extra_data: Optional[Dict[str, Any]] = None):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
            error_type="permission_error",
            error_code="FINEHERO_403",
            extra_data=extra_data
        )

class ResourceNotFoundError(FineHeroException):
    """Resource not found error."""
    def __init__(self, resource_type: str = "resource", resource_id: Optional[Union[str, int]] = None, extra_data: Optional[Dict[str, Any]] = None):
        resource = f"{resource_type}"
        if resource_id is not None:
            resource += f" with ID {resource_id}"
            
        detail = f"{resource} not found"
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail,
            error_type="not_found_error",
            error_code="FINEHERO_404",
            extra_data=extra_data or {"resource_type": resource_type, "resource_id": resource_id}
        )

class ValidationError(FineHeroException):
    """Validation error for when request parameters are invalid."""
    def __init__(self, detail: str = "Validation failed", field_errors: Optional[Dict[str, Any]] = None, extra_data: Optional[Dict[str, Any]] = None):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=detail,
            error_type="validation_error",
            error_code="FINEHERO_422",
            extra_data=extra_data or {"field_errors": field_errors}
        )

class PaymentError(FineHeroException):
    """Payment-related error."""
    def __init__(self, detail: str = "Payment processing error", error_code_override: Optional[str] = None, extra_data: Optional[Dict[str, Any]] = None):
        super().__init__(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=detail,
            error_type="payment_error",
            error_code=error_code_override or "FINEHERO_402",
            extra_data=extra_data
        )

class ServiceUnavailableError(FineHeroException):
    """Service unavailable error."""
    def __init__(self, detail: str = "Service is temporarily unavailable", extra_data: Optional[Dict[str, Any]] = None):
        super().__init__(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=detail,
            error_type="service_error",
            error_code="FINEHERO_503",
            extra_data=extra_data
        )

class ConflictError(FineHeroException):
    """Resource conflict error."""
    def __init__(self, detail: str = "Resource already exists or conflicts with existing data", extra_data: Optional[Dict[str, Any]] = None):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=detail,
            error_type="conflict_error",
            error_code="FINEHERO_409",
            extra_data=extra_data
        )

# Error response schema
class ErrorResponse:
    """Schema for error responses."""
    def __init__(
        self, 
        error_type: str, 
        error_code: str, 
        detail: str, 
        status_code: int = 500,
        timestamp: Optional[datetime] = None,
        path: Optional[str] = None,
        extra_data: Optional[Dict[str, Any]] = None
    ):
        self.error_type = error_type
        self.error_code = error_code
        self.detail = detail
        self.status_code = status_code
        self.timestamp = timestamp or datetime.now(timezone.utc)
        self.path = path
        self.extra_data = extra_data or {}
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON response."""
        response = {
            "error": {
                "type": self.error_type,
                "code": self.error_code,
                "detail": self.detail,
                "timestamp": self.timestamp.isoformat(),
            }
        }
        
        if self.path:
            response["error"]["path"] = self.path
            
        if self.extra_data:
            response["error"]["data"] = self.extra_data
            
        return response

def setup_error_handlers(app: FastAPI, logger=None) -> None:
    """
    Configure error handlers for the FastAPI application.
    
    Args:
        app: FastAPI application instance
        logger: Logger instance for error logging
    """
    if logger is None:
        import logging
        logger = logging.getLogger("finehero.error_handler")
    
    @app.exception_handler(FineHeroException)
    async def finehero_exception_handler(request: Request, exc: FineHeroException):
        """Handle custom FineHero exceptions."""
        logger.warning(
            f"FineHero exception occurred: {exc.error_code} - {exc.detail}",
            extra={
                "path": str(request.url.path),
                "method": request.method,
                "status_code": exc.status_code,
                "error_type": exc.error_type,
                "error_code": exc.error_code,
                "extra_data": exc.extra_data
            }
        )
        
        error_response = ErrorResponse(
            error_type=exc.error_type,
            error_code=exc.error_code,
            detail=exc.detail,
            status_code=exc.status_code,
            path=str(request.url.path),
            extra_data=exc.extra_data
        )
        
        return JSONResponse(
            status_code=exc.status_code,
            content=error_response.to_dict()
        )
    
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        """Convert FastAPI HTTPException to standard error format."""
        logger.warning(
            f"HTTP exception occurred: {exc.status_code} - {exc.detail}",
            extra={
                "path": str(request.url.path),
                "method": request.method,
                "status_code": exc.status_code
            }
        )
        
        error_response = ErrorResponse(
            error_type="http_error",
            error_code=f"FINEHERO_{exc.status_code}",
            detail=exc.detail,
            status_code=exc.status_code,
            path=str(request.url.path)
        )
        
        return JSONResponse(
            status_code=exc.status_code,
            content=error_response.to_dict()
        )
    
    @app.exception_handler(ValidationError)
    async def validation_exception_handler(request: Request, exc: ValidationError):
        """Handle Pydantic validation errors."""
        field_errors = {}
        for error in exc.errors():
            field = ".".join(str(x) for x in error["loc"]) if "loc" in error else "unknown"
            field_errors[field] = error.get("msg", "Validation error")
        
        logger.warning(
            f"Validation error occurred",
            extra={
                "path": str(request.url.path),
                "method": request.method,
                "field_errors": field_errors
            }
        )
        
        error_response = ErrorResponse(
            error_type="validation_error",
            error_code="FINEHERO_422",
            detail="Request validation failed",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            path=str(request.url.path),
            extra_data={"field_errors": field_errors}
        )
        
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=error_response.to_dict()
        )
    
    @app.exception_handler(RequestValidationError)
    async def request_validation_exception_handler(request: Request, exc: RequestValidationError):
        """Handle FastAPI request validation errors."""
        field_errors = {}
        for error in exc.errors():
            field = ".".join(str(x) for x in error.get("loc", []))
            field_errors[field] = error.get("msg", "Validation error")
        
        logger.warning(
            f"Request validation error occurred",
            extra={
                "path": str(request.url.path),
                "method": request.method,
                "field_errors": field_errors
            }
        )
        
        error_response = ErrorResponse(
            error_type="validation_error",
            error_code="FINEHERO_422",
            detail="Request validation failed",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            path=str(request.url.path),
            extra_data={"field_errors": field_errors}
        )
        
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=error_response.to_dict()
        )
    
    @app.exception_handler(StarletteHTTPException)
    async def starlette_http_exception_handler(request: Request, exc: StarletteHTTPException):
        """Handle Starlette HTTP exceptions."""
        logger.warning(
            f"HTTP exception occurred: {exc.status_code} - {exc.detail}",
            extra={
                "path": str(request.url.path),
                "method": request.method,
                "status_code": exc.status_code
            }
        )
        
        error_response = ErrorResponse(
            error_type="http_error",
            error_code=f"FINEHERO_{exc.status_code}",
            detail=exc.detail,
            status_code=exc.status_code,
            path=str(request.url.path)
        )
        
        return JSONResponse(
            status_code=exc.status_code,
            content=error_response.to_dict()
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        """Handle all other exceptions as server errors."""
        logger.error(
            f"Unexpected error occurred: {str(exc)}",
            extra={
                "path": str(request.url.path),
                "method": request.method,
                "traceback": traceback.format_exc()
            }
        )
        
        error_response = ErrorResponse(
            error_type="server_error",
            error_code="FINEHERO_500",
            detail="An unexpected error occurred",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            path=str(request.url.path)
        )
        
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error_response.to_dict()
        )

def add_error_middleware(app: FastAPI, logger=None):
    """
    Add error handling middleware to a FastAPI application.
    
    Args:
        app: FastAPI application instance
        logger: Logger instance for error logging
    """
    # Set up exception handlers
    setup_error_handlers(app, logger)
    
    # Add middleware for request/response logging
    if logger is None:
        import logging
        logger = logging.getLogger("finehero.middleware")
    
    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        """Middleware to log requests and responses."""
        start_time = datetime.now(timezone.utc)
        
        # Get client IP
        client_ip = request.client.host if request.client else "unknown"
        
        logger.info(
            f"Request started: {request.method} {request.url.path} from {client_ip}",
            extra={
                "path": str(request.url.path),
                "method": request.method,
                "client_ip": client_ip,
                "query_params": str(request.query_params),
            }
        )
        
        # Process the request
        response = await call_next(request)
        
        # Calculate processing time
        process_time = (datetime.now(timezone.utc) - start_time).total_seconds()
        
        # Log the response
        logger.info(
            f"Request completed: {request.method} {request.url.path} - {response.status_code} ({process_time:.3f}s)",
            extra={
                "path": str(request.url.path),
                "method": request.method,
                "status_code": response.status_code,
                "process_time": process_time,
            }
        )
        
        # Add processing time to response headers
        response.headers["X-Process-Time"] = str(process_time)
        
        return response
    
    return app
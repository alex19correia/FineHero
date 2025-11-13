"""
Security Middleware for Analytics Endpoints
Comprehensive security protection with rate limiting, headers, and monitoring
"""

import time
import json
import logging
from typing import Dict, Any, Optional, Callable
from fastapi import Request, Response, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from collections import defaultdict, deque
from datetime import datetime, timedelta
import re
import html
from .security_validator import SecurityValidator


class AnalyticsSecurityMiddleware(BaseHTTPMiddleware):
    """
    Comprehensive security middleware for analytics endpoints
    """
    
    def __init__(self, app: ASGIApp, rate_limit_per_minute: int = 100):
        super().__init__(app)
        self.rate_limit = rate_limit_per_minute
        self.rate_limit_window = 60  # seconds
        self.request_counts = defaultdict(deque)
        self.blocked_ips = defaultdict(float)
        self.security_validator = SecurityValidator()
        self.security_logger = logging.getLogger('analytics_security_middleware')
        
        # Suspicious patterns to monitor
        self.suspicious_patterns = [
            r'union\s+select',
            r'drop\s+table',
            r'insert\s+into',
            r'update\s+\w+\s+set',
            r'delete\s+from',
            r'<script',
            r'javascript:',
            r'onerror=',
            r'\.\./',
            r'%2e%2e%2f',
            r'eval\s*\(',
            r'exec\s*\(',
        ]
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        client_ip = self._get_client_ip(request)
        request_path = request.url.path
        request_method = request.method
        
        # Skip security checks for health checks and static files
        if self._should_skip_security_check(request_path):
            return await call_next(request)
        
        # Check if IP is temporarily blocked
        if self._is_ip_blocked(client_ip):
            self.security_logger.warning(f"Blocked request from banned IP: {client_ip}")
            return JSONResponse(
                status_code=429,
                content={
                    "error": "Too Many Requests",
                    "message": "Your IP has been temporarily blocked due to suspicious activity",
                    "retry_after": int(self._get_block_remaining_time(client_ip))
                }
            )
        
        # Rate limiting
        if not self._check_rate_limit(client_ip):
            self._block_ip(client_ip, duration=300)  # 5 minutes
            self.security_logger.warning(f"Rate limit exceeded for IP: {client_ip}")
            return JSONResponse(
                status_code=429,
                content={
                    "error": "Too Many Requests",
                    "message": "Rate limit exceeded. Please try again later.",
                    "retry_after": 60
                }
            )
        
        # Log request for monitoring
        self._log_request(client_ip, request_method, request_path, request.headers)
        
        # Process the request
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        
        # Add security headers
        response = self._add_security_headers(response)
        
        # Monitor for suspicious patterns in request
        if self._contains_suspicious_patterns(request_path):
            self._log_suspicious_activity(client_ip, request_method, request_path)
            
            # For critical endpoints, return sanitized response
            if self._is_critical_endpoint(request_path):
                return JSONResponse(
                    status_code=400,
                    content={
                        "error": "Bad Request",
                        "message": "Request contains invalid characters"
                    }
                )
        
        # Add performance header
        response.headers["X-Process-Time"] = str(process_time)
        
        return response
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP address from request"""
        # Check for forwarded headers first (for load balancers/proxies)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        # Fallback to direct connection
        return request.client.host if request.client else "unknown"
    
    def _should_skip_security_check(self, path: str) -> bool:
        """Check if security checks should be skipped for this path"""
        skip_patterns = [
            "/health",
            "/metrics",
            "/favicon.ico",
            "/static/",
            "/docs",
            "/redoc",
            "/openapi.json"
        ]
        
        return any(path.startswith(pattern) for pattern in skip_patterns)
    
    def _check_rate_limit(self, client_ip: str) -> bool:
        """Check if client is within rate limits"""
        now = time.time()
        window_start = now - self.rate_limit_window
        
        # Clean old entries
        while self.request_counts[client_ip] and self.request_counts[client_ip][0] < window_start:
            self.request_counts[client_ip].popleft()
        
        # Check current count
        if len(self.request_counts[client_ip]) >= self.rate_limit:
            return False
        
        # Add current request
        self.request_counts[client_ip].append(now)
        return True
    
    def _is_ip_blocked(self, client_ip: str) -> bool:
        """Check if IP is currently blocked"""
        if client_ip in self.blocked_ips:
            block_time = self.blocked_ips[client_ip]
            if time.time() < block_time:
                return True
            else:
                # Unblock expired IP
                del self.blocked_ips[client_ip]
        return False
    
    def _block_ip(self, client_ip: str, duration: int = 300):
        """Temporarily block an IP address"""
        self.blocked_ips[client_ip] = time.time() + duration
        self.security_logger.warning(f"Blocked IP {client_ip} for {duration} seconds")
    
    def _get_block_remaining_time(self, client_ip: str) -> int:
        """Get remaining block time for an IP"""
        if client_ip in self.blocked_ips:
            remaining = self.blocked_ips[client_ip] - time.time()
            return max(0, int(remaining))
        return 0
    
    def _log_request(self, client_ip: str, method: str, path: str, headers: Dict[str, str]):
        """Log request for security monitoring"""
        self.security_logger.info(f"Request: {method} {path}", extra={
            "client_ip": client_ip,
            "method": method,
            "path": path,
            "user_agent": headers.get("user-agent", ""),
            "timestamp": datetime.utcnow().isoformat()
        })
    
    def _contains_suspicious_patterns(self, text: str) -> bool:
        """Check if text contains suspicious patterns"""
        text_lower = text.lower()
        return any(re.search(pattern, text_lower) for pattern in self.suspicious_patterns)
    
    def _is_critical_endpoint(self, path: str) -> bool:
        """Check if endpoint is critical and requires strict security"""
        critical_patterns = [
            "/analytics/track",
            "/analytics/user/",
            "/analytics/system/",
            "/api/v1/analytics/",
        ]
        
        return any(path.startswith(pattern) for pattern in critical_patterns)
    
    def _log_suspicious_activity(self, client_ip: str, method: str, path: str):
        """Log suspicious activity"""
        self.security_logger.warning(f"Suspicious activity detected", extra={
            "client_ip": client_ip,
            "method": method,
            "path": path,
            "activity_type": "suspicious_pattern",
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Automatically block IP for critical endpoints
        if self._is_critical_endpoint(path):
            self._block_ip(client_ip, duration=600)  # 10 minutes
    
    def _add_security_headers(self, response: Response) -> Response:
        """Add comprehensive security headers to response"""
        # Content Security Policy
        csp = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self'; "
            "connect-src 'self'; "
            "frame-ancestors 'none';"
        )
        
        # Add headers
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        response.headers['Content-Security-Policy'] = csp
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response.headers['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'
        
        return response


class InputValidationMiddleware(BaseHTTPMiddleware):
    """
    Middleware for comprehensive input validation and sanitization
    """
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.security_validator = SecurityValidator()
        self.security_logger = logging.getLogger('input_validation_middleware')
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip validation for certain endpoints
        if self._should_skip_validation(request.url.path):
            return await call_next(request)
        
        try:
            # Validate request data
            validation_error = await self._validate_request(request)
            if validation_error:
                self.security_logger.warning(f"Request validation failed", extra={
                    "path": request.url.path,
                    "client_ip": self._get_client_ip(request),
                    "validation_error": validation_error
                })
                return JSONResponse(
                    status_code=400,
                    content={
                        "error": "Validation Error",
                        "message": validation_error
                    }
                )
            
            # Process request
            response = await call_next(request)
            
            # Validate response data for critical endpoints
            if self._requires_response_validation(request.url.path):
                response = await self._validate_response(response, request)
            
            return response
            
        except Exception as e:
            self.security_logger.error(f"Request processing error: {str(e)}", extra={
                "path": request.url.path,
                "client_ip": self._get_client_ip(request),
                "error_type": type(e).__name__
            })
            
            return JSONResponse(
                status_code=500,
                content={
                    "error": "Internal Server Error",
                    "message": "An error occurred processing your request"
                }
            )
    
    def _should_skip_validation(self, path: str) -> bool:
        """Check if validation should be skipped"""
        skip_patterns = [
            "/health",
            "/metrics",
            "/docs",
            "/openapi.json"
        ]
        return any(path.startswith(pattern) for pattern in skip_patterns)
    
    def _requires_response_validation(self, path: str) -> bool:
        """Check if response validation is required"""
        critical_patterns = [
            "/analytics/user/",
            "/analytics/system/",
            "/api/v1/analytics/"
        ]
        return any(path.startswith(pattern) for pattern in critical_patterns)
    
    async def _validate_request(self, request: Request) -> Optional[str]:
        """Validate request data"""
        # Validate URL parameters
        for param_name, param_value in request.path_params.items():
            if isinstance(param_value, str):
                # Check for SQL injection patterns
                if self.security_validator._contains_sql_injection_patterns(param_value):
                    return f"Invalid characters in parameter: {param_name}"
                
                # Check for XSS patterns
                if self.security_validator._contains_xss_patterns(param_value):
                    return f"Potentially dangerous content in parameter: {param_name}"
        
        # Validate query parameters
        for param_name, param_value in request.query_params.multi_items():
            if isinstance(param_value, str):
                # Validate user_id specifically
                if param_name == 'user_id':
                    try:
                        self.security_validator.validate_user_id(param_value)
                    except ValueError as e:
                        return f"Invalid user_id: {str(e)}"
        
        # Validate request body for POST/PUT requests
        if request.method in ['POST', 'PUT', 'PATCH']:
            try:
                body = await request.body()
                if body:
                    content_type = request.headers.get('content-type', '')
                    if 'application/json' in content_type:
                        data = json.loads(body)
                        if isinstance(data, dict):
                            # Validate and sanitize event data
                            if 'user_id' in data:
                                self.security_validator.validate_user_id(data['user_id'])
                            
                            if 'data' in data:
                                self.security_validator.validate_event_data(data['data'])
            except json.JSONDecodeError:
                return "Invalid JSON in request body"
            except Exception as e:
                return f"Request validation error: {str(e)}"
        
        return None
    
    async def _validate_response(self, response: Response, request: Request) -> Response:
        """Validate response data"""
        # For critical endpoints, ensure response doesn't contain sensitive data
        if hasattr(response, 'body'):
            try:
                response_text = response.body.decode('utf-8')
                # Check for potential data leakage
                sensitive_patterns = [
                    r'"password":\s*"[^"]*"',
                    r'"secret":\s*"[^"]*"',
                    r'"token":\s*"[^"]*"',
                    r'"key":\s*"[^"]*"',
                    r'SQL\s+syntax',
                    r'database',
                    r'table\s+\w+'
                ]
                
                for pattern in sensitive_patterns:
                    if re.search(pattern, response_text, re.IGNORECASE):
                        self.security_logger.warning(f"Potential data leakage detected", extra={
                            "path": request.url.path,
                            "pattern": pattern
                        })
                        # Return sanitized error response
                        return JSONResponse(
                            status_code=500,
                            content={
                                "error": "Internal Server Error",
                                "message": "An error occurred processing your request"
                            }
                        )
            except Exception:
                pass  # Ignore encoding errors
        
        return response
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP address"""
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        return request.client.host if request.client else "unknown"
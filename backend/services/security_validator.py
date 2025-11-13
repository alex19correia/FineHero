"""
Security Validation and Input Sanitization Module
Comprehensive protection against SQL injection, XSS, and other injection attacks
"""

import re
import html
import json
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urlparse
import logging
from sqlalchemy.exc import SQLAlchemyError


class SecurityValidator:
    """
    Comprehensive input validation and sanitization service
    """
    
    # SQL injection patterns to detect and block
    SQL_INJECTION_PATTERNS = [
        r"(?i)(\bunion\b.*\bselect\b|\bor\b.*\b1\b=\b1\b|'.*'.*'.*'|\";.*\")",
        r"(?i)(exec|execute|script|scripting|javascript:|vbscript:)",
        r"(?i)(\bor\b\s*\d+\s*=\s*\d+|and\s*\d+\s*=\s*\d+)",
        r"(?i)(\bdrop\b\s+\btable\b|\bdelete\b\s+from\s+\b|\binsert\b\s+into\s+\b)",
        r"(?i)(\bupdate\b\s+\b.*\bset\b|\balter\b\s+\btable\b|\bcreate\b\s+\btable\b)"
    ]
    
    # XSS patterns to detect and sanitize
    XSS_PATTERNS = [
        r"<script[^>]*>.*?</script>",
        r"javascript:",
        r"on\w+\s*=",
        r"<iframe[^>]*>.*?</iframe>",
        r"<object[^>]*>.*?</object>",
        r"<embed[^>]*>.*?</embed>",
        r"vbscript:",
        r"data:text/html"
    ]
    
    # Path traversal patterns
    PATH_TRAVERSAL_PATTERNS = [
        r"\.\./",
        r"\.\.\\",
        r"%2e%2e%2f",
        r"%2e%2e%5c",
        r"\.\.%2f",
        r"\.\.%5c"
    ]
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.security_events_logger = logging.getLogger('security_events')
    
    def validate_user_id(self, user_id: Any) -> str:
        """
        Validate and sanitize user_id parameter
        """
        if not user_id:
            raise ValueError("User ID is required")
        
        # Convert to string and validate format
        user_id_str = str(user_id).strip()
        
        # Check for empty strings
        if not user_id_str:
            raise ValueError("User ID cannot be empty")
        
        # Check length limits
        if len(user_id_str) > 100:
            raise ValueError("User ID too long")
        
        # Check for SQL injection patterns
        if self._contains_sql_injection_patterns(user_id_str):
            self._log_security_event("sql_injection_attempt", {
                "user_id": user_id_str,
                "pattern_detected": self._detect_patterns(user_id_str, self.SQL_INJECTION_PATTERNS)
            })
            raise ValueError("Invalid user ID format")
        
        # Remove any potentially dangerous characters
        safe_user_id = re.sub(r'[^\w\-_.@]', '', user_id_str)
        
        if safe_user_id != user_id_str:
            self._log_security_event("user_id_sanitization", {
                "original": user_id_str,
                "sanitized": safe_user_id
            })
        
        return safe_user_id
    
    def validate_date_range(self, start_date: Any, end_date: Any) -> tuple:
        """
        Validate and sanitize date range parameters
        """
        # Validate start_date
        if start_date:
            try:
                if isinstance(start_date, str):
                    start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                else:
                    start_dt = start_date
                
                # Check for reasonable date range (not more than 1 year ago)
                min_date = datetime.now() - timedelta(days=365)
                if start_dt < min_date:
                    raise ValueError("Start date too far in the past")
                
                # Check for future dates (allow some buffer)
                max_date = datetime.now() + timedelta(days=1)
                if start_dt > max_date:
                    raise ValueError("Start date cannot be in the future")
                    
            except (ValueError, TypeError) as e:
                raise ValueError(f"Invalid start date format: {e}")
        
        # Validate end_date
        if end_date:
            try:
                if isinstance(end_date, str):
                    end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                else:
                    end_dt = end_date
                
                # Check for reasonable date range
                min_date = datetime.now() - timedelta(days=365)
                if end_dt < min_date:
                    raise ValueError("End date too far in the past")
                    
                max_date = datetime.now() + timedelta(days=1)
                if end_dt > max_date:
                    raise ValueError("End date cannot be in the future")
                    
            except (ValueError, TypeError) as e:
                raise ValueError(f"Invalid end date format: {e}")
        
        # Ensure start_date <= end_date if both provided
        if start_date and end_date:
            start_dt = start_date if not isinstance(start_date, str) else datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            end_dt = end_date if not isinstance(end_date, str) else datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            
            if start_dt > end_dt:
                raise ValueError("Start date cannot be after end date")
        
        return start_date, end_date
    
    def validate_event_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate and sanitize event data dictionary
        """
        if not isinstance(data, dict):
            raise ValueError("Event data must be a dictionary")
        
        sanitized_data = {}
        
        for key, value in data.items():
            # Validate key
            if not isinstance(key, str) or not key.strip():
                continue
            
            # Sanitize key (alphanumeric and underscore only)
            safe_key = re.sub(r'[^a-zA-Z0-9_]', '', key.strip())
            
            # Validate and sanitize value
            if isinstance(value, str):
                # Check for XSS and SQL injection in string values
                sanitized_value = self._sanitize_string(value)
                
                # Validate length
                if len(sanitized_value) > 1000:
                    sanitized_value = sanitized_value[:1000]
                    self._log_security_event("data_truncated", {
                        "key": safe_key,
                        "original_length": len(value),
                        "truncated_length": 1000
                    })
                
                sanitized_data[safe_key] = sanitized_value
                
            elif isinstance(value, (int, float)):
                # Validate numeric ranges
                if isinstance(value, int):
                    if value < -1000000 or value > 1000000:
                        self._log_security_event("value_out_of_range", {
                            "key": safe_key,
                            "value": value,
                            "range": (-1000000, 1000000)
                        })
                        continue
                else:  # float
                    if value < -1000000.0 or value > 1000000.0:
                        self._log_security_event("value_out_of_range", {
                            "key": safe_key,
                            "value": value,
                            "range": (-1000000.0, 1000000.0)
                        })
                        continue
                
                sanitized_data[safe_key] = value
                
            elif isinstance(value, bool):
                sanitized_data[safe_key] = value
                
            elif value is None:
                sanitized_data[safe_key] = None
                
            else:
                # Skip unsupported types but log
                self._log_security_event("unsupported_value_type", {
                    "key": safe_key,
                    "type": type(value).__name__,
                    "value": str(value)
                })
        
        return sanitized_data
    
    def validate_session_id(self, session_id: Any) -> str:
        """
        Validate and sanitize session ID
        """
        if not session_id:
            return self._generate_safe_session_id()
        
        session_id_str = str(session_id).strip()
        
        # Check for injection patterns
        if self._contains_sql_injection_patterns(session_id_str):
            self._log_security_event("session_id_injection_attempt", {
                "session_id": session_id_str,
                "pattern_detected": self._detect_patterns(session_id_str, self.SQL_INJECTION_PATTERNS)
            })
            return self._generate_safe_session_id()
        
        # Check length
        if len(session_id_str) > 100:
            raise ValueError("Session ID too long")
        
        # Use only safe characters
        safe_session_id = re.sub(r'[^\w\-]', '', session_id_str)
        
        if not safe_session_id:
            return self._generate_safe_session_id()
        
        return safe_session_id
    
    def validate_ip_address(self, ip_address: Any) -> Optional[str]:
        """
        Validate and sanitize IP address
        """
        if not ip_address:
            return None
        
        ip_str = str(ip_address).strip()
        
        # Basic IP validation
        ip_pattern = r'^(\d{1,3}\.){3}\d{1,3}$|^[a-fA-F0-9:]+$'
        if not re.match(ip_pattern, ip_str):
            self._log_security_event("invalid_ip_format", {
                "ip_address": ip_str
            })
            return None
        
        # Check for suspicious patterns
        if self._contains_sql_injection_patterns(ip_str):
            self._log_security_event("ip_injection_attempt", {
                "ip_address": ip_str
            })
            return None
        
        return ip_str
    
    def validate_url(self, url: Any) -> Optional[str]:
        """
        Validate and sanitize URL
        """
        if not url:
            return None
        
        url_str = str(url).strip()
        
        if len(url_str) > 500:
            self._log_security_event("url_too_long", {
                "url_length": len(url_str)
            })
            return None
        
        try:
            parsed = urlparse(url_str)
            
            # Only allow safe protocols
            if parsed.scheme not in ['http', 'https', '']:
                self._log_security_event("unsafe_url_protocol", {
                    "scheme": parsed.scheme,
                    "url": url_str
                })
                return None
            
            # Check for injection patterns
            if self._contains_sql_injection_patterns(url_str) or self._contains_xss_patterns(url_str):
                self._log_security_event("url_injection_attempt", {
                    "url": url_str
                })
                return None
            
            return url_str
            
        except Exception as e:
            self._log_security_event("url_parsing_error", {
                "url": url_str,
                "error": str(e)
            })
            return None
    
    def _sanitize_string(self, value: str) -> str:
        """
        Sanitize string to remove XSS and injection patterns
        """
        # Remove null bytes
        value = value.replace('\x00', '')
        
        # HTML escape to prevent XSS
        sanitized = html.escape(value)
        
        # Remove potentially dangerous patterns
        for pattern in self.XSS_PATTERNS:
            sanitized = re.sub(pattern, '', sanitized, flags=re.IGNORECASE | re.DOTALL)
        
        # Remove SQL injection patterns
        for pattern in self.SQL_INJECTION_PATTERNS:
            if re.search(pattern, sanitized, re.IGNORECASE):
                self._log_security_event("sanitization_removal", {
                    "original": value,
                    "pattern": pattern,
                    "sanitized": sanitized
                })
                sanitized = re.sub(pattern, '[REMOVED]', sanitized, flags=re.IGNORECASE)
        
        return sanitized.strip()
    
    def _contains_sql_injection_patterns(self, value: str) -> bool:
        """
        Check if value contains SQL injection patterns
        """
        for pattern in self.SQL_INJECTION_PATTERNS:
            if re.search(pattern, value, re.IGNORECASE):
                return True
        return False
    
    def _contains_xss_patterns(self, value: str) -> bool:
        """
        Check if value contains XSS patterns
        """
        for pattern in self.XSS_PATTERNS:
            if re.search(pattern, value, re.IGNORECASE | re.DOTALL):
                return True
        return False
    
    def _detect_patterns(self, value: str, patterns: List[str]) -> List[str]:
        """
        Detect which patterns are present in the value
        """
        detected = []
        for pattern in patterns:
            if re.search(pattern, value, re.IGNORECASE):
                detected.append(pattern)
        return detected
    
    def _generate_safe_session_id(self) -> str:
        """
        Generate a safe session ID
        """
        import uuid
        return f"safe_{uuid.uuid4().hex[:16]}"
    
    def _log_security_event(self, event_type: str, details: Dict[str, Any]):
        """
        Log security events for monitoring and alerting
        """
        self.security_events_logger.warning(f"Security event: {event_type}", extra={
            "security_event": True,
            "event_type": event_type,
            "details": details,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    def handle_secure_error(self, error: Exception) -> Dict[str, Any]:
        """
        Handle errors securely without exposing sensitive information
        """
        # Log the actual error for debugging (with context)
        self.logger.error(f"Analytics service error: {type(error).__name__}", extra={
            "error_type": type(error).__name__,
            "error_message": str(error),
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Return safe error response
        if isinstance(error, SQLAlchemyError):
            return {
                'success': False,
                'error': 'Database operation failed. Please try again.',
                'error_code': 'DB_ERROR'
            }
        elif isinstance(error, ValueError):
            return {
                'success': False,
                'error': 'Invalid input parameters.',
                'error_code': 'VALIDATION_ERROR'
            }
        else:
            return {
                'success': False,
                'error': 'An unexpected error occurred. Please try again.',
                'error_code': 'INTERNAL_ERROR'
            }